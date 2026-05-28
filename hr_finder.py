"""
HR Finder — extracts poster name/title from Apify job data
and resolves the company's email domain.
"""

import re
import socket
import requests

# Common suffixes to strip when guessing a domain from a company name
_STRIP = [
    r'\s+(plc|ltd|limited|llc|inc|corp|corporation|group|holdings|solutions|technologies|technology|tech|services|consulting|consultancy|ireland|uk|india|global|international)\b',
]

def _clean_name_part(s):
    """Lowercase, keep only letters, return empty string if blank."""
    return re.sub(r"[^a-z]", "", s.lower()) if s else ""


def extract_hr_info(job):
    """
    Pull poster info already embedded in the Apify job record.
    Returns a dict with keys: first_name, last_name, full_name, title, linkedin_url
    """
    full_name  = (job.get("jobPosterName")  or "").strip()
    title      = (job.get("jobPosterTitle") or "").strip()
    profile_url = (job.get("jobPosterProfileUrl") or "").strip()

    parts = full_name.split(maxsplit=1)
    first = parts[0] if parts else ""
    last  = parts[1] if len(parts) > 1 else ""

    return {
        "full_name":   full_name,
        "first_name":  first,
        "last_name":   last,
        "title":       title,
        "linkedin_url": profile_url,
    }


def guess_company_domain(company_name, company_linkedin_url=""):
    """
    Try to resolve a valid email domain for the company.
    Strategy:
      1. Extract slug from LinkedIn company URL
      2. Try slug + common TLDs
      3. Fall back to stripped/cleaned company name + TLDs
    Returns the first domain that resolves (has an A or MX record), or best guess.
    """
    candidates = []

    # From LinkedIn URL: https://ie.linkedin.com/company/accenture  → accenture
    if company_linkedin_url:
        m = re.search(r"/company/([^/?#]+)", company_linkedin_url)
        if m:
            slug = m.group(1).lower().replace("-", "")
            candidates.append(slug)

    # From company name: clean up common suffixes and spaces
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
                return domain          # first one that resolves
            except socket.gaierror:
                continue

    # Return best guess even if unresolved
    return (candidates[0] + ".com") if candidates else ""


def build_email_patterns(first_name, last_name, domain):
    """
    Return ordered list of (email, pattern_label) pairs.
    Most likely pattern first.
    """
    f = _clean_name_part(first_name)
    l = _clean_name_part(last_name)
    if not f or not l or not domain:
        return []

    return [
        (f"{f}.{l}@{domain}",  "firstname.lastname"),
        (f"{f}{l}@{domain}",   "firstnamelastname"),
        (f"{f[0]}.{l}@{domain}", "f.lastname"),
        (f"{f}@{domain}",      "firstname"),
        (f"{f[0]}{l}@{domain}", "flastname"),
    ]
