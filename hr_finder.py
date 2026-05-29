"""
HR Finder — extracts poster name/title from job data and resolves
the company's email domain.

For agency postings (no LinkedIn poster), falls back to:
  1. Hunter.io domain search — finds real emails + names at company domain
  2. Generic recruiter aliases: careers@, recruitment@, talent@, hr@
"""

import re
import socket
import requests
from config import HUNTER_API_KEY

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

    name = company_name.lower()
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
