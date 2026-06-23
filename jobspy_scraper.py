"""
Unified Job Scraper — JobSpy (free) + Apify LinkedIn fallback (poster data).

Sources:
  - LinkedIn:      JobSpy first, Apify fallback (gets poster name for real HR emails)
  - Indeed:        JobSpy (may 403 from India without proxy)
  - ZipRecruiter:  JobSpy (replaces Naukri — actually supported)

Usage:
    from jobspy_scraper import scrape_linkedin_jobs, scrape_indeed_jobs, scrape_ziprecruiter_jobs
"""

import time
import hashlib
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import SEARCH_QUERIES, APIFY_TOKEN, APIFY_BASE_URL


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_job_id(source, title, company, url):
    raw = f"{source}|{title}|{company}|{url}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _normalize_jobspy(row, source_hint="jobspy"):
    """Convert a JobSpy DataFrame row to our unified job schema."""
    title    = str(row.get("title", "") or "")
    company  = str(row.get("company_name", "") or row.get("company", "") or "")
    location = str(row.get("location", "") or "")
    url      = str(row.get("job_url", "") or row.get("url", "") or "")
    desc     = str(row.get("description", "") or "")
    source   = str(row.get("site", "") or source_hint).lower()

    salary = ""
    sal_min = row.get("min_amount") or row.get("salary_min")
    sal_max = row.get("max_amount") or row.get("salary_max")
    currency = row.get("currency", "")
    if sal_min and sal_max:
        salary = f"{currency} {sal_min}-{sal_max}"
    elif sal_min:
        salary = f"{currency} {sal_min}+"

    job_id = str(row.get("id", "")) or _make_job_id(source, title, company, url)

    jd_emails = row.get("emails", "") or ""
    if isinstance(jd_emails, list):
        jd_emails = ",".join(jd_emails)

    return {
        "job_id":              f"{source}_{job_id}",
        "title":               title,
        "company":             company,
        "location":            location,
        "url":                 url,
        "apply_url":           url,
        "description":         desc,
        "salary":              salary.strip(),
        "seniority":           "",
        "employment_type":     str(row.get("job_type", "") or ""),
        "easy_apply":          bool(row.get("is_remote", False)),
        "posted_at":           str(row.get("date_posted", "") or ""),
        "source":              source,
        "companyLinkedinUrl":  str(row.get("company_url", "") or ""),
        "jd_emails":           str(jd_emails).strip(),
        "jobPosterName":       "",
        "jobPosterTitle":      "",
        "jobPosterProfileUrl": "",
    }


def _run_jobspy_search(site_names, search_term, location, results_wanted=20):
    """Run a single JobSpy search, return list of normalized job dicts."""
    try:
        from jobspy import scrape_jobs
        df = scrape_jobs(
            site_name=site_names,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
        )
        if df is None or df.empty:
            return []
        jobs = []
        for _, row in df.iterrows():
            jobs.append(_normalize_jobspy(row))
        return jobs
    except Exception as e:
        err_msg = str(e)
        if "403" in err_msg:
            print(f"[JobSpy] {site_names[0]} blocked (needs proxy) for '{search_term}' / '{location}'")
        else:
            print(f"[JobSpy] Error scraping '{search_term}' in '{location}': {e}")
        return []


# ── Apify LinkedIn fallback ─────────────────────────────────────────────────

APIFY_ACTOR = "curious_coder~linkedin-jobs-scraper"
APIFY_POLL_INTERVAL = 10
APIFY_MAX_POLLS = 36


def _build_linkedin_search_url(title, location):
    params = urllib.parse.urlencode({
        "keywords": title,
        "location": location,
        "f_TPR": "r86400",
        "position": 1,
        "pageNum": 0,
    })
    return f"https://www.linkedin.com/jobs/search/?{params}"


def _normalize_apify_job(item):
    """Map Apify curious_coder actor output to our schema — includes poster data."""
    salary_info = item.get("salaryInfo", {})
    salary_parts = salary_info.get("compensationBreakdown", []) if isinstance(salary_info, dict) else []
    salary_str = ""
    if salary_parts:
        b = salary_parts[0]
        currency = b.get("currencyCode", "")
        low  = b.get("minSalary", "")
        high = b.get("maxSalary", "")
        if low and high:
            salary_str = f"{currency} {low}-{high} / yr"
        elif low:
            salary_str = f"{currency} {low}+ / yr"

    poster_name = (
        item.get("posterFullName") or item.get("posterName")
        or item.get("jobPosterName") or item.get("postedBy") or ""
    )
    poster_title = (
        item.get("posterHeadline") or item.get("posterTitle")
        or item.get("jobPosterTitle") or ""
    )
    poster_url = (
        item.get("posterProfileUrl") or item.get("posterUrl")
        or item.get("jobPosterProfileUrl") or ""
    )

    desc = item.get("descriptionText", "") or item.get("description", "") or ""

    # Extract emails from JD text (Apify provides full HTML/text)
    import re
    all_text = desc + " " + (item.get("descriptionHtml", "") or "")
    found_emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", all_text)
    jd_emails = ",".join(set(found_emails)) if found_emails else ""

    return {
        "job_id":              f"linkedin_apify_{item.get('id', '')}",
        "title":               item.get("title", ""),
        "company":             item.get("companyName", "Unknown"),
        "location":            item.get("location", ""),
        "url":                 item.get("link", ""),
        "apply_url":           item.get("applyUrl", item.get("link", "")),
        "description":         desc,
        "salary":              salary_str or item.get("salary", ""),
        "seniority":           item.get("seniorityLevel", ""),
        "employment_type":     item.get("employmentType", ""),
        "easy_apply":          "easy apply" in str(item.get("benefits", [])).lower(),
        "posted_at":           item.get("postedAt", ""),
        "source":              "linkedin",
        "companyLinkedinUrl":  item.get("companyUrl", "") or item.get("companyLinkedinUrl", ""),
        "jd_emails":           jd_emails,
        "jobPosterName":       poster_name,
        "jobPosterTitle":      poster_title,
        "jobPosterProfileUrl": poster_url,
    }


def _apify_linkedin_search(queries, count=50):
    """Run Apify LinkedIn actor as fallback. Returns list of normalized jobs."""
    if not APIFY_TOKEN:
        print("[Apify] No APIFY_TOKEN — skipping fallback")
        return []

    urls = [_build_linkedin_search_url(q["title"], q["location"]) for q in queries]
    print(f"[Apify] LinkedIn fallback: {len(urls)} queries, requesting {count} jobs...")

    run_url = f"{APIFY_BASE_URL}/acts/{APIFY_ACTOR}/runs"
    try:
        resp = requests.post(run_url, json={"urls": urls, "count": count, "scrapeCompany": False},
                             params={"token": APIFY_TOKEN}, timeout=30)
        resp.raise_for_status()
        run_data = resp.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")

        if not run_id:
            print("[Apify] Failed to start actor run")
            return []

        status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
        status = None
        for _ in range(APIFY_MAX_POLLS):
            time.sleep(APIFY_POLL_INTERVAL)
            st = requests.get(status_url, params={"token": APIFY_TOKEN}, timeout=15)
            status = st.json().get("data", {}).get("status", "")
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break

        if status != "SUCCEEDED":
            print(f"[Apify] Actor ended with status: {status}")
            return []

        items_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
        items_resp = requests.get(items_url, params={"token": APIFY_TOKEN}, timeout=30)
        items_resp.raise_for_status()
        raw_items = items_resp.json()

        jobs = [_normalize_apify_job(item) for item in raw_items]
        poster_count = sum(1 for j in jobs if j.get("jobPosterName"))
        print(f"[Apify] Got {len(jobs)} jobs ({poster_count} with poster names)")
        return jobs

    except Exception as e:
        print(f"[Apify] LinkedIn fallback error: {e}")
        return []


# ── Public API ──────────────────────────────────────────────────────────────

def _scrape_one_query(q):
    """Scrape a single query — designed for ThreadPoolExecutor."""
    jobs = _run_jobspy_search(["linkedin"], q["title"], q["location"], results_wanted=15)
    for j in jobs:
        j["source"] = "linkedin"
    return q, jobs


def scrape_linkedin_jobs():
    """Scrape LinkedIn: parallel JobSpy + Apify fallback for failed queries."""
    all_jobs = {}
    failed_queries = []

    print(f"[LinkedIn/JobSpy] Running {len(SEARCH_QUERIES)} queries (parallel, 4 workers)...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_scrape_one_query, q): q for q in SEARCH_QUERIES}
        for future in as_completed(futures):
            q = futures[future]
            try:
                _, jobs = future.result()
                if jobs:
                    for job in jobs:
                        if job["job_id"] not in all_jobs and job["title"]:
                            all_jobs[job["job_id"]] = job
                    print(f"  [OK] {q['title']} / {q['location']}: {len(jobs)} jobs")
                else:
                    failed_queries.append(q)
                    print(f"  [--] {q['title']} / {q['location']}: 0 jobs")
            except Exception as e:
                failed_queries.append(q)
                print(f"  [ERR] {q['title']} / {q['location']}: {e}")

    print(f"[LinkedIn/JobSpy] {len(all_jobs)} jobs from JobSpy, {len(failed_queries)} queries failed")

    if failed_queries and APIFY_TOKEN:
        print(f"[LinkedIn] Trying Apify fallback for {len(failed_queries)} failed queries...")
        apify_jobs = _apify_linkedin_search(failed_queries, count=50)
        added = 0
        for job in apify_jobs:
            if job["job_id"] not in all_jobs and job["title"]:
                all_jobs[job["job_id"]] = job
                added += 1
        print(f"[LinkedIn/Apify] Added {added} new jobs from Apify fallback")

    print(f"[LinkedIn] Total: {len(all_jobs)} unique jobs")
    return list(all_jobs.values())


def scrape_indeed_jobs():
    """Scrape Indeed jobs via JobSpy. May return 403 from India IPs."""
    all_jobs = {}

    for q in SEARCH_QUERIES:
        print(f"[Indeed/JobSpy] {q['title']} / {q['location']}...")
        jobs = _run_jobspy_search(["indeed"], q["title"], q["location"], results_wanted=20)
        for job in jobs:
            if job["job_id"] not in all_jobs and job["title"]:
                job["source"] = "indeed"
                all_jobs[job["job_id"]] = job
        time.sleep(2)

    print(f"[Indeed/JobSpy] Total: {len(all_jobs)} unique jobs")
    return list(all_jobs.values())


def scrape_ziprecruiter_jobs():
    """Scrape ZipRecruiter via JobSpy (replaces Naukri — actually supported by JobSpy)."""
    all_jobs = {}

    for q in SEARCH_QUERIES:
        print(f"[ZipRecruiter/JobSpy] {q['title']} / {q['location']}...")
        jobs = _run_jobspy_search(["zip_recruiter"], q["title"], q["location"], results_wanted=15)
        for job in jobs:
            if job["job_id"] not in all_jobs and job["title"]:
                job["source"] = "ziprecruiter"
                all_jobs[job["job_id"]] = job
        time.sleep(2)

    print(f"[ZipRecruiter/JobSpy] Total: {len(all_jobs)} unique jobs")
    return list(all_jobs.values())


def scrape_naukri_jobs():
    """Deprecated — Naukri not supported by JobSpy. Returns empty list."""
    return []


if __name__ == "__main__":
    print("Testing JobSpy + Apify LinkedIn scraper...")
    jobs = scrape_linkedin_jobs()
    print(f"\nFound {len(jobs)} LinkedIn jobs")
    for j in jobs[:5]:
        poster = j.get("jobPosterName", "")
        print(f"  [{j['source']}] {j['title']} @ {j['company']} — {j['location']}")
        if poster:
            print(f"    Poster: {poster} ({j.get('jobPosterTitle', '')})")
        print(f"    {j['url'][:80]}")
