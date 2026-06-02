"""
Unified Job Scraper — powered by JobSpy (FREE, no API keys needed).

Replaces all 3 Apify scrapers (LinkedIn, Indeed, Naukri) with a single
zero-cost local scraper. Currently LinkedIn works reliably without proxy.
Indeed/Naukri may need proxy from India IPs.

Usage:
    from jobspy_scraper import scrape_linkedin_jobs, scrape_indeed_jobs, scrape_naukri_jobs
"""

import time
import hashlib
from config import SEARCH_QUERIES


def _make_job_id(source, title, company, url):
    """Generate a deterministic job_id from key fields."""
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

    # Salary
    salary = ""
    sal_min = row.get("min_amount") or row.get("salary_min")
    sal_max = row.get("max_amount") or row.get("salary_max")
    currency = row.get("currency", "")
    if sal_min and sal_max:
        salary = f"{currency} {sal_min}-{sal_max}"
    elif sal_min:
        salary = f"{currency} {sal_min}+"

    job_id = str(row.get("id", "")) or _make_job_id(source, title, company, url)

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
        # Don't spam logs for expected blocks (403 = no proxy)
        if "403" in err_msg:
            print(f"[JobSpy] {site_names[0]} blocked (needs proxy) for '{search_term}' / '{location}'")
        else:
            print(f"[JobSpy] Error scraping '{search_term}' in '{location}': {e}")
        return []


# ── Public API — drop-in replacements ────────────────────────────────────────

def scrape_linkedin_jobs():
    """Scrape LinkedIn jobs via JobSpy (FREE, replaces Apify)."""
    all_jobs = {}

    for q in SEARCH_QUERIES:
        print(f"[LinkedIn/JobSpy] {q['title']} / {q['location']}...")
        jobs = _run_jobspy_search(["linkedin"], q["title"], q["location"], results_wanted=20)
        for job in jobs:
            if job["job_id"] not in all_jobs and job["title"]:
                job["source"] = "linkedin"  # normalize source name
                all_jobs[job["job_id"]] = job
        time.sleep(2)  # polite delay to avoid rate limits

    print(f"[LinkedIn/JobSpy] Total: {len(all_jobs)} unique jobs")
    return list(all_jobs.values())


def scrape_indeed_jobs():
    """Scrape Indeed jobs via JobSpy (FREE, replaces Apify).
    Note: May return 403 from India IPs without proxy."""
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


def scrape_naukri_jobs():
    """Naukri is not supported by JobSpy (only LinkedIn, Indeed, ZipRecruiter).
    Returns empty list. Naukri scraping would need a dedicated scraper or proxy."""
    print("[Naukri] Not supported by JobSpy — skipping (LinkedIn covers India jobs)")
    return []


if __name__ == "__main__":
    print("Testing JobSpy scraper (LinkedIn only — most reliable)...")
    jobs = scrape_linkedin_jobs()
    print(f"\nFound {len(jobs)} LinkedIn jobs")
    for j in jobs[:5]:
        print(f"  [{j['source']}] {j['title']} @ {j['company']} — {j['location']}")
        print(f"    {j['url'][:80]}")
