"""
Naukri.com Job Scraper — uses Apify actor muhammetakkurtt/naukri-job-scraper
Searches India for target roles posted in last 24h.
"""

import time
import requests
from config import APIFY_TOKEN, APIFY_BASE_URL

ACTOR_ID = "muhammetakkurtt~naukri-job-scraper"
MAX_JOBS = 50

NAUKRI_QUERIES = [
    {"keyword": "Senior Business Analyst healthcare",  "freshness": "1"},
    {"keyword": "Technical Product Owner data",        "freshness": "1"},
    {"keyword": "Data Product Owner MDM",              "freshness": "1"},
    {"keyword": "Technical Business Analyst AWS",      "freshness": "1"},
    {"keyword": "Senior Business Analyst Snowflake",   "freshness": "1"},
    {"keyword": "Business Analyst Kafka Airflow",      "freshness": "1"},
    {"keyword": "Senior Business Analyst AI LLM",      "freshness": "1"},
    {"keyword": "Business Analyst healthcare data",    "freshness": "1"},
]


def _run_actor(query):
    """Run one Naukri query via Apify."""
    if not APIFY_TOKEN:
        return []
    try:
        start = requests.post(
            f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs",
            params={"token": APIFY_TOKEN},
            json={
                "keyword":  query["keyword"],
                "maxJobs":  MAX_JOBS,
                "freshness": query.get("freshness", "1"),
                "sortBy":   "date",
                "fetchDetails": True,
            },
            timeout=30,
        )
        start.raise_for_status()
        run_id = start.json()["data"]["id"]

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
        print(f"[Naukri] Query error ({query['keyword']}): {e}")
        return []


def _normalize(item):
    """Map Naukri result fields to unified job schema."""
    job_id = f"naukri_{item.get('jobId') or item.get('id') or hash(item.get('jobUrl',''))}"
    desc = item.get("jobDescription") or item.get("description") or ""
    if not desc:
        # Build description from available fields
        skills = ", ".join(item.get("skills", []) if isinstance(item.get("skills"), list) else [])
        desc = f"{item.get('jobTitle','')} at {item.get('companyName','')}. Skills: {skills}"

    salary = ""
    if item.get("salaryMin") and item.get("salaryMax"):
        salary = f"₹{item['salaryMin']}-{item['salaryMax']} LPA"
    elif item.get("salary"):
        salary = str(item["salary"])

    return {
        "job_id":              job_id,
        "title":               item.get("jobTitle") or item.get("title", ""),
        "company":             item.get("companyName") or item.get("company", ""),
        "location":            item.get("location") or item.get("jobLocation", "India"),
        "url":                 item.get("jobUrl") or item.get("url", ""),
        "description":         desc,
        "salary":              salary,
        "easy_apply":          False,
        "companyLinkedinUrl":  "",
        "jobPosterName":       "",
        "jobPosterTitle":      "",
        "jobPosterProfileUrl": "",
        "source":              "naukri",
    }


def scrape_naukri_jobs():
    """Run all Naukri queries, return deduplicated list."""
    if not APIFY_TOKEN:
        print("[Naukri] APIFY_TOKEN not set — skipping")
        return []

    all_jobs = {}
    for q in NAUKRI_QUERIES:
        print(f"[Naukri] {q['keyword']}...")
        raw = _run_actor(q)
        for item in raw:
            job = _normalize(item)
            if job["job_id"] not in all_jobs and job["url"]:
                all_jobs[job["job_id"]] = job
        time.sleep(2)

    print(f"[Naukri] Total: {len(all_jobs)} unique jobs")
    return list(all_jobs.values())
