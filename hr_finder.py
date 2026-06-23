"""
HR Finder — finds REAL recruiter emails for job outreach.

Strategy chain:
  1. JD email (extracted from job description text)
  2. Apollo contact cache (verified personal emails from Apollo.io)
  3. Apify poster enrichment (real LinkedIn poster → email pattern)
  4. DuckDuckGo/Bing recruiter search (FREE)
  5. Company website scrape (FREE)
  6. Hunter.io domain search (if key available)
  7. Generic recruitment@ alias (last resort)
"""

import os
import re
import json
import time
import socket
import urllib.parse
import requests
from config import HUNTER_API_KEY, APIFY_TOKEN, APIFY_BASE_URL, APOLLO_API_KEY


# ── Apollo REST API — verified recruiter emails ───────────────────────────
_APOLLO_CACHE = os.path.join(os.path.dirname(__file__), "output", "apollo_contacts.json")
_APOLLO_API = "https://api.apollo.io/api/v1"


def _load_apollo_cache():
    try:
        with open(_APOLLO_CACHE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_apollo_cache(cache):
    os.makedirs(os.path.dirname(_APOLLO_CACHE), exist_ok=True)
    with open(_APOLLO_CACHE, "w") as f:
        json.dump(cache, f, indent=2)


def apollo_find_recruiter(company_name):
    """
    Find a recruiter/TA person at a company via Apollo REST API.
    Uses cache to avoid repeat API calls. Returns dict or None.
    """
    cache = _load_apollo_cache()
    key = company_name.lower().strip()

    # Check cache first (exact + partial match)
    if key in cache:
        return cache[key]
    for cached_key, contact in cache.items():
        if key in cached_key or cached_key in key:
            return contact

    # No cache hit — call Apollo API
    if not APOLLO_API_KEY:
        return None

    try:
        result = _apollo_search_people(company_name)
        if result:
            cache[key] = result
            _save_apollo_cache(cache)
            return result
    except Exception as e:
        print(f"   [Apollo] API error: {e}")

    # Cache the miss too (avoid re-querying)
    cache[key] = None
    _save_apollo_cache(cache)
    return None


def _apollo_search_people(company_name):
    """Search Apollo for TA/HR people at a company. Returns best match or None."""
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    # Search for recruiters/TA at the company
    payload = {
        "api_key": APOLLO_API_KEY,
        "q_organization_name": company_name,
        "person_titles": [
            "Talent Acquisition",
            "Recruiter",
            "HR Manager",
            "People Partner",
            "Head of Talent",
            "Hiring Manager",
        ],
        "per_page": 5,
        "person_seniorities": ["manager", "senior", "director"],
    }

    resp = requests.post(
        f"{_APOLLO_API}/mixed_people/search",
        json=payload,
        headers=headers,
        timeout=15,
    )

    if resp.status_code == 422:
        print(f"   [Apollo] Rate limited or invalid request")
        return None
    if resp.status_code != 200:
        print(f"   [Apollo] API {resp.status_code}")
        return None

    data = resp.json()
    people = data.get("people", [])

    if not people:
        return None

    # Pick best match — prefer someone with an email
    for person in people:
        email = person.get("email")
        first = person.get("first_name", "")
        last = person.get("last_name", "")
        title = person.get("title", "")
        linkedin = person.get("linkedin_url", "")

        if email and first and last:
            print(f"   [Apollo] Found: {first} {last} ({title}) — {email}")
            return {
                "full_name": f"{first} {last}",
                "first_name": first,
                "last_name": last,
                "title": title,
                "email": email,
                "linkedin_url": linkedin,
                "source": "apollo_verified",
            }

    # No email but have a name — return for pattern building
    p = people[0]
    first = p.get("first_name", "")
    last = p.get("last_name", "")
    if first and last:
        print(f"   [Apollo] Found name (no email): {first} {last} ({p.get('title','')})")
        return {
            "full_name": f"{first} {last}",
            "first_name": first,
            "last_name": last,
            "title": p.get("title", ""),
            "email": None,
            "linkedin_url": p.get("linkedin_url", ""),
            "source": "apollo_name_only",
        }

    return None

# Common suffixes to strip when guessing a domain from a company name
_STRIP = [
    r'\s+(plc|ltd|limited|llc|inc|corp|corporation|group|holdings|solutions|technologies|technology|tech|services|consulting|consultancy|ireland|uk|india|global|international)\b',
]

# HR/recruitment-related title keywords for Hunter.io result filtering
_HR_KEYWORDS = [
    "recruit", "talent", "hr ", "human resource", "people",
    "hiring", "acquisition", "staffing", "head of people",
]

# Generic outreach aliases tried in order
_GENERIC_ALIASES = ["careers", "recruitment", "talent", "hr", "jobs", "hello"]


def _clean_name_part(s):
    """Lowercase, keep only letters."""
    return re.sub(r"[^a-z]", "", s.lower()) if s else ""


def extract_hr_info(job):
    """
    Pull poster info already embedded in the LinkedIn/Apify job record.
    Returns dict: first_name, last_name, full_name, title, linkedin_url
    """
    full_name   = (job.get("jobPosterName")       or "").strip()
    title       = (job.get("jobPosterTitle")      or "").strip()
    profile_url = (job.get("jobPosterProfileUrl") or "").strip()

    parts = full_name.split(maxsplit=1)
    first = parts[0] if parts else ""
    last  = parts[1] if len(parts) > 1 else ""

    return {
        "full_name":    full_name,
        "first_name":   first,
        "last_name":    last,
        "title":        title,
        "linkedin_url": profile_url,
    }


def find_agency_contact(company_name, domain):
    """
    Fallback HR finder for postings without a named poster (agencies etc.).

    Strategy:
      1. Hunter.io domain search → prefer emails with recruiter/HR titles
      2. If no Hunter.io key, return a generic alias email

    Returns dict same shape as extract_hr_info, with an extra 'email' key
    containing the best found address (or None).
    """
    if domain and HUNTER_API_KEY:
        try:
            resp = requests.get(
                "https://api.hunter.io/v2/domain-search",
                params={
                    "domain":  domain,
                    "api_key": HUNTER_API_KEY,
                    "limit":   10,
                    "type":    "personal",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                emails = resp.json().get("data", {}).get("emails", [])

                # Prefer emails with HR/recruiter titles
                for e in emails:
                    pos = (e.get("position") or "").lower()
                    if any(kw in pos for kw in _HR_KEYWORDS):
                        fn = e.get("first_name") or ""
                        ln = e.get("last_name")  or ""
                        return {
                            "full_name":    f"{fn} {ln}".strip() or company_name,
                            "first_name":   fn,
                            "last_name":    ln,
                            "title":        e.get("position") or "Recruiter",
                            "linkedin_url": "",
                            "email":        e.get("value"),
                            "source":       "hunter_domain",
                        }

                # No HR title match — use first available email
                if emails:
                    e = emails[0]
                    fn = e.get("first_name") or ""
                    ln = e.get("last_name")  or ""
                    return {
                        "full_name":    f"{fn} {ln}".strip() or company_name,
                        "first_name":   fn,
                        "last_name":    ln,
                        "title":        e.get("position") or "Contact",
                        "linkedin_url": "",
                        "email":        e.get("value"),
                        "source":       "hunter_domain",
                    }
        except Exception as e:
            print(f"[HR] Hunter.io domain search error: {e}")

    # Generic fallback — use careers@ / recruitment@ alias
    if domain:
        generic_email = f"{_GENERIC_ALIASES[0]}@{domain}"
        return {
            "full_name":    "Hiring Team",
            "first_name":   "Hiring",
            "last_name":    "Team",
            "title":        "Recruitment",
            "linkedin_url": "",
            "email":        generic_email,
            "source":       "generic_alias",
        }

    return None


def guess_company_domain(company_name, company_linkedin_url=""):
    """
    Resolve a valid email domain for the company.
    1. Extract slug from LinkedIn company URL
    2. Try slug + common TLDs
    3. Fall back to cleaned company name + TLDs
    Returns first domain that resolves, or best guess.
    """
    candidates = []

    if company_linkedin_url:
        m = re.search(r"/company/([^/?#]+)", company_linkedin_url)
        if m:
            slug = m.group(1).lower().replace("-", "")
            candidates.append(slug)

    name = str(company_name or "").lower()
    for pattern in _STRIP:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    name_slug = re.sub(r"[^a-z0-9]", "", name)
    if name_slug and name_slug not in candidates:
        candidates.append(name_slug)

    tlds = [".com", ".ie", ".co.uk", ".co.in", ".io", ".net"]
    for slug in candidates:
        for tld in tlds:
            domain = slug + tld
            try:
                socket.getaddrinfo(domain, None)
                return domain
            except socket.gaierror:
                continue

    return (candidates[0] + ".com") if candidates else ""


def build_email_patterns(first_name, last_name, domain):
    """Return ordered list of (email, label) pairs."""
    f = _clean_name_part(first_name)
    l = _clean_name_part(last_name)
    if not f or not l or not domain:
        return []

    return [
        (f"{f}.{l}@{domain}",   "firstname.lastname"),
        (f"{f}{l}@{domain}",    "firstnamelastname"),
        (f"{f[0]}.{l}@{domain}", "f.lastname"),
        (f"{f}@{domain}",       "firstname"),
        (f"{f[0]}{l}@{domain}", "flastname"),
    ]


def build_generic_patterns(domain):
    """Return generic alias patterns for companies with no poster name."""
    if not domain:
        return []
    return [(f"{alias}@{domain}", alias) for alias in _GENERIC_ALIASES]


def verify_email_smtp(email):
    """
    Quick SMTP RCPT TO check — verifies if an email address exists.
    Returns True if the server accepts, False if rejected, None if inconclusive.
    """
    domain = email.split("@")[1]
    try:
        mx_host = domain
        socket.getaddrinfo(mx_host, 25)
    except Exception:
        return None

    try:
        import smtplib
        smtp = smtplib.SMTP(timeout=10)
        smtp.connect(mx_host, 25)
        smtp.helo("verify.local")
        smtp.mail("verify@verify.local")
        code, _ = smtp.rcpt(email)
        smtp.quit()
        return code == 250
    except Exception:
        return None


# ── Google/DuckDuckGo recruiter search (FREE) ───────────────────────────────

_NAME_FROM_TITLE_RE = re.compile(
    r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-–—|·]",
)
_LINKEDIN_PROFILE_RE = re.compile(
    r"linkedin\.com/in/([a-z0-9-]+)",
)


def _parse_recruiter_from_snippets(html):
    """Extract recruiter name from DuckDuckGo search result HTML.

    Handles multiple DDG HTML formats — class names change periodically.
    """
    # Try multiple selectors — DDG changes their CSS classes
    titles = re.findall(r"<a[^>]*class=\"result__a\"[^>]*>([^<]+)</a>", html)
    if not titles:
        titles = re.findall(r'<a[^>]*class="[^"]*result[^"]*"[^>]*>([^<]+)</a>', html)
    if not titles:
        titles = re.findall(r'<a[^>]*href="[^"]*linkedin\.com/in/[^"]*"[^>]*>([^<]+)</a>', html)
    if not titles:
        titles = re.findall(r"<h[23][^>]*>.*?<a[^>]*>([^<]+)</a>", html)

    # Also extract from snippet text that contains "Name - Title" patterns
    snippets = re.findall(r'<a[^>]*>([^<]{10,80})</a>', html)
    titles = titles + snippets

    for title in titles[:20]:
        title = re.sub(r"&[a-z]+;", " ", title).strip()
        title = re.sub(r"<[^>]+>", "", title)
        title = re.sub(r"\s+", " ", title).strip()

        # Pattern: "Firstname Lastname - Title at Company" or "Firstname Lastname | Title"
        m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*[-–—|·]", title)
        if not m:
            # Also try: "Firstname Lastname, Title"
            m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*,\s*", title)
        if m:
            name = m.group(1).strip()
            words = name.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words):
                linkedin_slug = ""
                # Search nearby HTML for the linkedin slug
                idx = html.find(title)
                if idx >= 0:
                    chunk = html[max(0, idx-200):idx+500]
                else:
                    chunk = html
                lm = _LINKEDIN_PROFILE_RE.search(chunk)
                if lm:
                    linkedin_slug = lm.group(1)
                return {
                    "full_name": name,
                    "first_name": words[0],
                    "last_name": words[-1],
                    "linkedin_slug": linkedin_slug,
                }
    return None


def google_find_recruiter(company_name, domain=""):
    """
    FREE recruiter finder via DuckDuckGo + Bing.
    Searches for Talent Acquisition / Recruiter / HR people at the company.
    Returns dict with name info, or None.
    """
    clean_company = re.sub(r"\s*\(.*?\)", "", company_name).strip()
    clean_company = re.sub(r"\s+(Inc|Ltd|LLC|Corp|Pvt|Limited|Technologies|Solutions)\.?$", "",
                           clean_company, flags=re.IGNORECASE).strip()

    search_terms = [
        f'"Talent Acquisition" "{clean_company}"',
        f'"Recruiter" "{clean_company}"',
        f'"HR Manager" "{clean_company}"',
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    search_engines = [
        ("DDG",  lambda q: f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"),
        ("Bing", lambda q: f"https://www.bing.com/search?q={urllib.parse.quote(q)}"),
    ]

    for term in search_terms:
        query = f"site:linkedin.com/in {term}"
        for engine_name, url_fn in search_engines:
            try:
                resp = requests.get(url_fn(query), headers=headers, timeout=10)
                if resp.status_code == 200 and len(resp.text) > 5000:
                    result = _parse_recruiter_from_snippets(resp.text)
                    if result:
                        print(f"   [HR-Search] Found: {result['full_name']} ({engine_name})")
                        return {
                            "full_name":    result["full_name"],
                            "first_name":   result["first_name"],
                            "last_name":    result["last_name"],
                            "title":        "Talent Acquisition",
                            "linkedin_url": f"https://linkedin.com/in/{result['linkedin_slug']}" if result.get("linkedin_slug") else "",
                            "source":       "google_search",
                        }
            except Exception as e:
                print(f"   [HR-Search] {engine_name} error: {e}")
        time.sleep(1)

    return None


# ── Free website email scraper (no API key needed) ──────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_SKIP_EMAILS = {"example.com", "email.com", "domain.com", "company.com", "yourcompany.com"}
_CAREER_PATHS = ["/careers", "/jobs", "/contact", "/about", "/about-us", "/contact-us"]


def scrape_company_emails(domain):
    """
    Scrape company website for real contact emails. FREE, no API key.
    Checks homepage + careers/contact pages for email addresses.
    Returns list of (email, source_page) tuples, HR-related first.
    """
    if not domain:
        return []

    found = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    base = f"https://{domain}"
    pages = [""] + _CAREER_PATHS

    for path in pages:
        url = base + path
        try:
            resp = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
            if resp.status_code != 200:
                continue
            text = resp.text
            emails = _EMAIL_RE.findall(text)
            for em in emails:
                em = em.lower().strip()
                em_domain = em.split("@")[1]
                if em_domain in _SKIP_EMAILS:
                    continue
                if em.endswith((".png", ".jpg", ".svg", ".gif", ".css", ".js")):
                    continue
                found.append((em, path or "/"))
        except Exception:
            continue

    # Deduplicate, prioritize HR-related emails
    seen = set()
    hr_emails = []
    other_emails = []
    for em, src in found:
        if em in seen:
            continue
        seen.add(em)
        local = em.split("@")[0]
        if any(kw in local for kw in ["recruit", "talent", "hr", "hiring", "career", "jobs", "people"]):
            hr_emails.append((em, src))
        elif not local.startswith(("noreply", "no-reply", "info@", "support", "admin", "webmaster", "privacy")):
            other_emails.append((em, src))

    return hr_emails + other_emails


def find_website_hr_contact(domain, company_name=""):
    """
    Free HR email finder — scrapes company website.
    Returns dict with email + name info, or None.
    """
    emails = scrape_company_emails(domain)
    if not emails:
        return None

    email, source = emails[0]
    local = email.split("@")[0]

    # Try to extract name from email pattern (firstname.lastname@)
    parts = local.replace("_", ".").replace("-", ".").split(".")
    if len(parts) >= 2 and all(p.isalpha() for p in parts[:2]):
        first = parts[0].capitalize()
        last = parts[1].capitalize()
        full_name = f"{first} {last}"
    else:
        first, last = "", ""
        full_name = company_name or "Hiring Team"

    return {
        "full_name":    full_name,
        "first_name":   first,
        "last_name":    last,
        "title":        "Contact" if first else "Recruitment",
        "linkedin_url": "",
        "email":        email,
        "source":       "website_scrape",
    }


# ── Apify poster enrichment ($0.001/job) ────────────────────────────────────

DETAIL_ACTOR = "ayk_6789~linkedin-job-details-scraper"
_POSTER_FIELDS = [
    "posterName", "posterFullName", "jobPosterName", "postedBy",
    "poster_name", "recruiter_name", "recruiterName",
]
_POSTER_TITLE_FIELDS = [
    "posterTitle", "posterHeadline", "jobPosterTitle",
    "poster_title", "recruiterTitle", "recruiter_title",
]
_POSTER_URL_FIELDS = [
    "posterProfileUrl", "posterUrl", "posterLinkedinUrl",
    "jobPosterProfileUrl", "poster_url", "recruiterUrl",
]


def _find_field(data, candidates):
    for key in candidates:
        val = data.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def enrich_with_poster_data(jobs):
    """
    For LinkedIn best-fit jobs, call Apify detail scraper to get poster info.
    Mutates jobs in-place. Only processes jobs without existing poster data.
    Cost: ~$0.001 per job.
    """
    if not APIFY_TOKEN:
        print("[HR] No APIFY_TOKEN — skipping poster enrichment")
        return

    linkedin_jobs = [
        j for j in jobs
        if j.get("source") == "linkedin"
        and not j.get("jobPosterName")
        and j.get("url")
    ]
    if not linkedin_jobs:
        print("[HR] No LinkedIn jobs need poster enrichment")
        return

    urls = [{"url": j["url"]} for j in linkedin_jobs]
    print(f"[HR] Enriching {len(urls)} LinkedIn jobs with poster data via Apify (~${len(urls)*0.001:.3f})...")

    try:
        run_url = f"{APIFY_BASE_URL}/acts/{DETAIL_ACTOR}/runs"
        resp = requests.post(
            run_url,
            json={"startUrls": urls},
            params={"token": APIFY_TOKEN},
            timeout=30,
        )
        if resp.status_code == 403:
            print("[HR] Apify 403 — token may be expired, skipping enrichment")
            return
        resp.raise_for_status()
        run_data = resp.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")

        if not run_id:
            print("[HR] Failed to start detail scraper")
            return

        status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
        status = "UNKNOWN"
        for _ in range(12):
            time.sleep(10)
            try:
                st = requests.get(status_url, params={"token": APIFY_TOKEN}, timeout=15)
                status = st.json().get("data", {}).get("status", "")
            except Exception:
                continue
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break

        if status != "SUCCEEDED":
            print(f"[HR] Detail scraper ended: {status} (continuing without poster data)")
            return

        items_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
        items = requests.get(items_url, params={"token": APIFY_TOKEN}, timeout=30).json()

        # Build URL → poster data lookup
        enriched = 0
        for item in items:
            item_url = item.get("url", "") or item.get("jobUrl", "") or item.get("link", "")
            poster_name = _find_field(item, _POSTER_FIELDS)
            poster_title = _find_field(item, _POSTER_TITLE_FIELDS)
            poster_url = _find_field(item, _POSTER_URL_FIELDS)

            if not poster_name:
                continue

            # Match back to our job by URL
            for job in linkedin_jobs:
                job_url_id = job["url"].split("?")[0].rstrip("/").split("/")[-1]
                item_url_id = item_url.split("?")[0].rstrip("/").split("/")[-1] if item_url else ""
                job_id_field = str(item.get("jobId", "") or item.get("id", ""))

                if (item_url_id and item_url_id == job_url_id) or (job_id_field and job_id_field in job["url"]):
                    job["jobPosterName"] = poster_name
                    job["jobPosterTitle"] = poster_title
                    job["jobPosterProfileUrl"] = poster_url
                    enriched += 1
                    break

        print(f"[HR] Enriched {enriched}/{len(linkedin_jobs)} jobs with poster data")

    except Exception as e:
        print(f"[HR] Poster enrichment error: {e}")
