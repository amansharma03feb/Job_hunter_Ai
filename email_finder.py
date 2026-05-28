"""
Email Finder — validates email patterns using:
  1. Hunter.io API (if key provided — 25 free/month)
  2. MX record check via dnspython (always free)
  3. Falls back to "best guess" first pattern if nothing conclusive
"""

import requests
from config import HUNTER_API_KEY


def _check_mx(domain):
    """Return True if domain has MX records (free DNS check)."""
    try:
        import dns.resolver
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        return False


def _hunter_verify(email):
    """
    Use Hunter.io email verifier (25 free/month).
    Returns 'valid' | 'invalid' | 'unknown' | None (if no key).
    """
    if not HUNTER_API_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-verifier",
            params={"email": email, "api_key": HUNTER_API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("result", "unknown")
    except Exception:
        pass
    return None


def _hunter_find(first_name, last_name, domain):
    """
    Use Hunter.io email finder (25 free/month).
    Returns email string or None.
    """
    if not HUNTER_API_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": HUNTER_API_KEY,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return data.get("email") or None
    except Exception:
        pass
    return None


def find_best_email(first_name, last_name, domain, patterns):
    """
    Try to find/validate the best email for this person.

    Returns:
        (email, confidence)  confidence: 'verified' | 'likely' | 'guess' | None
    """
    if not domain or not patterns:
        return None, None

    # 1 — Hunter.io direct find (most reliable if key present)
    hunter_email = _hunter_find(first_name, last_name, domain)
    if hunter_email:
        return hunter_email, "verified"

    # 2 — MX sanity check: is the domain even receiving email?
    if not _check_mx(domain):
        # Domain has no MX — try .com fallback if domain isn't .com already
        if not domain.endswith(".com"):
            alt = domain.split(".")[0] + ".com"
            if _check_mx(alt):
                domain = alt
                patterns = [(e.replace(patterns[0][0].split("@")[1], alt), l)
                            for e, l in patterns]
            else:
                return patterns[0][0], "guess"

    # 3 — Hunter.io verify each pattern (stops on first valid)
    for email, label in patterns:
        result = _hunter_verify(email)
        if result == "valid":
            return email, "verified"
        if result == "unknown":
            # Still usable — mark as likely
            return email, "likely"

    # 4 — No API key, domain has MX → return most common pattern as likely
    return patterns[0][0], "likely"
