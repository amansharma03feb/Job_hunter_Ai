"""LinkedIn job scraper using Apify curious_coder/linkedin-jobs-scraper."""

import time
import urllib.parse
import requests
from config import APIFY_TOKEN, APIFY_BASE_URL, SEARCH_QUERIES

ACTOR_ID = "curious_coder~linkedin-jobs-scraper"
JOBS_PER_BATCH = 50       # jobs per actor run (split into two regional batches)
POLL_INTERVAL  = 10       # seconds between status checks
MAX_POLLS      = 36       # 6 minutes max


def _build_search_url(title, location):
    """Build a public LinkedIn jobs search URL (no login required)."""
    params = urllib.parse.urlencode({
        "keywords": title,
        "location": location,
        "f_TPR": "r86400",     # posted in last 24 hours
        "position": 1,
        "pageNum": 0,
    })
    return f"https://www.linkedin.com/jobs/search/?{params}"


def _run_actor(search_urls, count=JOBS_PER_BATCH):
    """Call Apify actor with a batch of LinkedIn search URLs."""
    if not APIFY_TOKEN:
        print("[Scraper] APIFY_TOKEN not set — skipping scrape.")
        return []

    run_url = f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs"
    payload = {
        "urls": search_urls,
        "count": count,
        "scrapeCompany": False,
    }

    try:
        resp = requests.post(run_url, json=payload,
                             params={"token": APIFY_TOKEN}, timeout=30)
        resp.raise_for_status()
        run_data = resp.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")

        if not run_id:
            print("[Scraper] Failed to start actor run.")
            return []

        # Poll until finished
        status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
        status = None
        for _ in range(MAX_POLLS):
            time.sleep(POLL_INTERVAL)
            st = requests.get(status_url,
                              params={"token": APIFY_TOKEN}, timeout=15)
            status = st.json().get("data", {}).get("status", "")
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break

        if status != "SUCCEEDED":
            print(f"[Scraper] Actor ended with status: {status}")
            return []

        items_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
        items_resp = requests.get(items_url,
                                  params={"token": APIFY_TOKEN}, timeout=30)
        items_resp.raise_for_status()
        return items_resp.json()

    except Exception as e:
        print(f"[Scraper] Actor error: {e}")
        return []


def _normalize_job(item):
    """Map curious_coder actor output to our standard job schema."""
    salary_info = item.get("salaryInfo", {})
    salary_parts = salary_info.get("compensationBreakdown", []) if isinstance(salary_info, dict) else []
    salary_str = ""
    if salary_parts:
        b = salary_parts[0]
        currency = b.get("currencyCode", "")
        low  = b.get("minSalary", "")
        high = b.get("maxSalary", "")
        if low and high:
            salary_str = f"{currency} {low}–{high} / yr"
        elif low:
            salary_str = f"{currency} {low}+ / yr"

    benefits = item.get("benefits", [])
    easy_apply = any("easy apply" in b.lower() for b in benefits)

    return {
        "job_id":          str(item.get("id", "")),
        "title":           item.get("title", ""),
        "company":         item.get("companyName", "Unknown"),
        "location":        item.get("location", ""),
        "url":             item.get("link", ""),
        "apply_url":       item.get("applyUrl", item.get("link", "")),
        "description":     item.get("descriptionText", ""),
        "salary":          salary_str or item.get("salary", ""),
        "seniority":       item.get("seniorityLevel", ""),
        "employment_type": item.get("employmentType", ""),
        "easy_apply":      easy_apply,
        "posted_at":       item.get("postedAt", ""),
        "source":          "LinkedIn",
    }


def scrape_linkedin_jobs():
    """Scrape all SEARCH_QUERIES via Apify in two regional batches."""
    india_locations = {"India", "Bangalore", "Hyderabad", "Pune", "Mumbai", "Chennai"}
    global_queries = [q for q in SEARCH_QUERIES if q["location"] not in india_locations]
    india_queries  = [q for q in SEARCH_QUERIES if q["location"] in india_locations]

    batches = []
    if global_queries:
        batches.append(("Global (Ireland/UK)", global_queries))
    if india_queries:
        batches.append(("India", india_queries))

    seen, unique = set(), []

    for batch_name, queries in batches:
        urls = [_build_search_url(q["title"], q["location"]) for q in queries]
        print(f"[Scraper] {batch_name}: {len(urls)} queries via Apify...")
        items = _run_actor(urls, count=JOBS_PER_BATCH)
        for item in items:
            job = _normalize_job(item)
            if job["job_id"] and job["title"] and job["job_id"] not in seen:
                seen.add(job["job_id"])
                unique.append(job)
        print(f"[Scraper]   -> {len(items)} raw, {len(unique)} unique so far")

    print(f"[Scraper] Total: {len(unique)} unique LinkedIn jobs")
    return unique
