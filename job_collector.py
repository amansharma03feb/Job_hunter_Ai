import requests
from role_config import TARGET_ROLES, TARGET_CATEGORIES, TARGET_LOCATIONS

SOURCES = {
    "remotive": "https://remotive.com/api/remote-jobs",
    "arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
    "himalayas": "https://himalayas.app/jobs/api",
}


def _matches_role(title):
    t = title.lower()
    return any(role in t for role in TARGET_ROLES)


def _matches_category(category):
    c = category.lower()
    return any(cat in c for cat in TARGET_CATEGORIES)


def _matches_location(location):
    loc = location.lower()
    return any(target in loc for target in TARGET_LOCATIONS)


def _fetch_remotive():
    jobs = []
    try:
        resp = requests.get(SOURCES["remotive"], timeout=15)
        resp.raise_for_status()
        for job in resp.json().get("jobs", []):
            title = job.get("title", "")
            category = job.get("category", "")
            location = job.get("candidate_required_location", "")
            if _matches_role(title) or _matches_category(category):
                jobs.append({
                    "title": title,
                    "company": job.get("company_name", "Unknown"),
                    "location": location or "Remote",
                    "description": job.get("description", ""),
                    "url": job.get("url", ""),
                    "source": "Remotive",
                })
    except Exception as e:
        print(f"[Remotive] Error: {e}")
    return jobs


def _fetch_arbeitnow():
    jobs = []
    for page in range(1, 3):
        try:
            resp = requests.get(SOURCES["arbeitnow"], params={"page": page}, timeout=15)
            resp.raise_for_status()
            for job in resp.json().get("data", []):
                title = job.get("title", "")
                location = job.get("location", "")
                tags = " ".join(job.get("tags", [])).lower()
                desc = job.get("description", "")
                if _matches_role(title) or _matches_role(tags) or "analyst" in title.lower():
                    jobs.append({
                        "title": title,
                        "company": job.get("company_name", "Unknown"),
                        "location": location or "Europe",
                        "description": desc,
                        "url": job.get("url", ""),
                        "source": "Arbeitnow",
                    })
        except Exception as e:
            print(f"[Arbeitnow] Error page {page}: {e}")
    return jobs


def _fetch_himalayas():
    jobs = []
    try:
        resp = requests.get(SOURCES["himalayas"], params={"limit": 50}, timeout=15)
        resp.raise_for_status()
        for job in resp.json().get("jobs", []):
            title = job.get("title", "")
            categories = " ".join(job.get("categories", []))
            if _matches_role(title) or _matches_category(categories):
                jobs.append({
                    "title": title,
                    "company": job.get("companyName", "Unknown"),
                    "location": ", ".join(job.get("locationRestrictions", [])) or "Remote",
                    "description": job.get("description", ""),
                    "url": job.get("applicationLink") or job.get("url", ""),
                    "source": "Himalayas",
                })
    except Exception as e:
        print(f"[Himalayas] Error: {e}")
    return jobs


def fetch_jobs(limit=30):
    all_jobs = []
    all_jobs.extend(_fetch_remotive())
    all_jobs.extend(_fetch_arbeitnow())
    all_jobs.extend(_fetch_himalayas())

    seen = set()
    unique = []
    for job in all_jobs:
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(job)

    print(f"[Collector] Fetched {len(unique)} unique jobs from {len(SOURCES)} sources")
    return unique[:limit]
