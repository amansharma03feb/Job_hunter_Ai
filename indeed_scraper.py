"""
Indeed Job Scraper — uses Apify actor valig/indeed-jobs-scraper
Searches Ireland, UK, and India for target roles posted in last 24h.
"""

import time
import requests
from config import APIFY_TOKEN, APIFY_BASE_URL

ACTOR_ID   = "valig~indeed-jobs-scraper"
MAX_JOBS   = 50   # per query

INDEED_QUERIES = [
    # Ireland
    {"title": "Senior Business Analyst",       "location": "Ireland",        "country": "ie"},
    {"title": "Technical Product Owner",        "location": "Dublin",         "country": "ie"},
    {"title": "Data Product Owner",             "location": "Ireland",        "country": "ie"},
    {"title": "Technical Business Analyst",     "location": "Ireland",        "country": "ie"},
    # UK
    {"title": "Senior Business Analyst",        "location": "London",         "country": "uk"},
    {"title": "Technical Product Owner",        "location": "United Kingdom", "country": "uk"},
    {"title": "Data Platform Business Analyst", "location": "United Kingdom", "country": "uk"},
    # India
    {"title": "Senior Business Analyst",        "location": "Bangalore",      "country": "in"},
    {"title": "Technical Product Owner",        "location": "India",          "country": "in"},
    {"title": "Senior Business Analyst MDM",    "location": "India",          "country": "in"},
    {"title": "Business Analyst healthcare",    "location": "Pune",           "country": "in"},
    {"title": "Data Product Owner",             "location": "India",          "country": "in"},
]


def _run_actor(query):
    """Run one Indeed query, return raw results list."""
    if not APIFY_TOKEN:
        return []
    try:
        # Start actor
        start = requests.post(
            f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs",
            params={"token": APIFY_TOKEN},
            json={
                "country":    query["country"],
                "title":      query["title"],
                "location":   query["location"],
                "limit":      MAX_JOBS,
                "datePosted": "1",   # last 24h
            },
            timeout=30,
        )
        start.raise_for_status()
        run_id = start.json()["data"]["id"]

        # Poll until finished
        for _ in range(60):
            time.sleep(5)
            status = requests.get(
                f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                params={"token": APIFY_TOKEN},
                timeout=15,
            ).json()["data"]["status"]
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break

        if status != "SUCCEEDED":
            return []

        # Fetch results
        dataset_id = requests.get(
            f"{APIFY_BASE_URL}/actor-runs/{run_id}",
            params={"token": APIFY_TOKEN},
            timeout=15,
        ).json()["data"]["defaultDatasetId"]

        items = requests.get(
            f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
            params={"token": APIFY_TOKEN, "limit": MAX_JOBS, "clean": "true"},
            timeout=30,
        ).json()
        return items if isinstance(items, list) else []

    except Exception as e:
        print(f"[Indeed] Query error ({query['title']} / {query['location']}): {e}")
        return []


def _normalize(item, query):
    """Map Indeed result fields to unified job schema."""
    job_id = f"indeed_{item.get('id') or item.get('jobKey') or hash(item.get('url',''))}"
    return {
        "job_id":             job_id,
        "title":              item.get("title") or item.get("jobTitle", ""),
        "company":            item.get("company") or item.get("companyName", ""),
        "location":           item.get("location") or item.get("jobLocation", ""),
        "url":                item.get("url") or item.get("jobUrl", ""),
        "description":        item.get("description") or item.get("jobDescription", ""),
        "salary":             item.get("salary") or item.get("salaryRange", ""),
        "easy_apply":         False,
        "companyLinkedinUrl": "",
        "jobPosterName":      "",
        "jobPosterTitle":     "",
        "jobPosterProfileUrl": "",
        "source":             "indeed",
        "_country":           query["country"],
    }


def scrape_indeed_jobs():
    """Run all Indeed queries, return deduplicated list of jobs."""
    if not APIFY_TOKEN:
        print("[Indeed] APIFY_TOKEN not set — skipping")
        return []

    all_jobs = {}
    for q in INDEED_QUERIES:
        print(f"[Indeed] {q['title']} / {q['location']} ({q['country'].upper()})...")
        raw = _run_actor(q)
        for item in raw:
            job = _normalize(item, q)
            if job["job_id"] not in all_jobs and job["url"]:
                all_jobs[job["job_id"]] = job
        time.sleep(2)

    print(f"[Indeed] Total: {len(all_jobs)} unique jobs")
    return list(all_jobs.values())
