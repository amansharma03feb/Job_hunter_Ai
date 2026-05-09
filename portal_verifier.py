"""Verify that LinkedIn job postings are still active (not ghost/expired)."""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

EXPIRED_SIGNALS = [
    "no longer accepting applications",
    "this job is no longer available",
    "this job has expired",
    "job not found",
    "page not found",
]


def _check_single_job(job):
    """Check if a single LinkedIn job URL is still active.

    Returns (job, is_active, reason).
    """
    url = job.get("url", "")
    if not url:
        return job, False, "no_url"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)

        if resp.status_code == 404:
            return job, False, "404"

        if resp.status_code != 200:
            # Non-404 errors — give benefit of doubt (LinkedIn rate limiting)
            return job, True, f"status_{resp.status_code}"

        page_text = resp.text.lower()
        for signal in EXPIRED_SIGNALS:
            if signal in page_text:
                return job, False, signal

        return job, True, "active"

    except requests.Timeout:
        return job, True, "timeout_assumed_active"
    except Exception as e:
        return job, True, f"error_assumed_active: {e}"


def verify_jobs(jobs, max_workers=5):
    """Verify a list of jobs concurrently. Returns (active_jobs, expired_count)."""
    active = []
    expired = 0
    errors = 0

    print(f"[Verifier] Checking {len(jobs)} job URLs...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_check_single_job, job): job for job in jobs}

        for future in as_completed(futures):
            job, is_active, reason = future.result()
            if is_active:
                job["verification_status"] = reason
                active.append(job)
            else:
                expired += 1
                print(f"[Verifier]   EXPIRED: {job['title']} @ {job['company']} ({reason})")

    print(f"[Verifier] Result: {len(active)} active, {expired} expired, {errors} errors")
    return active, expired
