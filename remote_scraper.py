"""
Remote Jobs Scraper — uses RemoteOK.com's free public API (no auth needed).
Fetches globally-remote roles matching target tags posted in last 7 days.
"""

import time
import requests
from datetime import datetime, timezone, timedelta

REMOTEOK_API = "https://remoteok.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (Job Hunter Bot — personal use)"}

# Tag combinations to query on RemoteOK
REMOTE_TAG_QUERIES = [
    "business+analyst",
    "product+manager",
    "product+owner",
    "data+analyst",
    "technical+analyst",
]

MAX_AGE_DAYS = 7   # only keep jobs posted in last 7 days


def _fetch_by_tag(tags):
    """Fetch jobs from RemoteOK for a tag string (e.g. 'business+analyst')."""
    try:
        resp = requests.get(
            f"{REMOTEOK_API}?tags={tags}",
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        # First element is always a legal notice dict — skip it
        return [j for j in data if isinstance(j, dict) and j.get("id")]
    except Exception as e:
        print(f"[Remote] Error fetching tag '{tags}': {e}")
        return []


def _is_recent(job):
    """Return True if job was posted within MAX_AGE_DAYS."""
    date_str = job.get("date") or job.get("epoch")
    if not date_str:
        return True   # assume recent if no date
    try:
        if isinstance(date_str, (int, float)):
            posted = datetime.fromtimestamp(date_str, tz=timezone.utc)
        else:
            posted = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (datetime.now(tz=timezone.utc) - posted).days <= MAX_AGE_DAYS
    except Exception:
        return True


def _normalize(item):
    """Map RemoteOK fields to unified job schema."""
    tags = item.get("tags", [])
    tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
    desc = item.get("description") or f"Remote role: {item.get('position','')} at {item.get('company','')}. Tags: {tag_str}"

    salary = ""
    if item.get("salary_min") and item.get("salary_max"):
        salary = f"${item['salary_min']:,}–${item['salary_max']:,}/yr"

    return {
        "job_id":              f"remote_{item.get('id', hash(item.get('url','')))}",
        "title":               item.get("position") or item.get("title", ""),
        "company":             item.get("company", ""),
        "location":            "Remote (Global)",
        "url":                 item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id','')}",
        "description":         desc,
        "salary":              salary,
        "easy_apply":          False,
        "companyLinkedinUrl":  "",
        "jobPosterName":       "",
        "jobPosterTitle":      "",
        "jobPosterProfileUrl": "",
        "source":              "remoteok",
    }


def scrape_remote_jobs():
    """Fetch remote jobs from RemoteOK for all target tag queries."""
    all_jobs = {}
    for tags in REMOTE_TAG_QUERIES:
        print(f"[Remote] Fetching tag: {tags}...")
        items = _fetch_by_tag(tags)
        recent = [j for j in items if _is_recent(j)]
        for item in recent:
            job = _normalize(item)
            if job["job_id"] not in all_jobs and job["title"]:
                all_jobs[job["job_id"]] = job
        time.sleep(1)

    print(f"[Remote] Total: {len(all_jobs)} unique remote jobs (last {MAX_AGE_DAYS} days)")
    return list(all_jobs.values())
