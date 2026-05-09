"""
AI Job Hunter — Multi-Source Validation Pipeline

Pipeline stages:
  1. SCRAPE  — LinkedIn jobs via Apify
  2. VERIFY  — Check URLs are still active (filter ghost postings)
  3. SCORE   — Hybrid keyword + Claude AI semantic matching
  4. FILTER  — Only deliver jobs scoring >= threshold
  5. DELIVER — Send formatted alerts via Telegram
"""

from datetime import datetime
from config import ATS_THRESHOLD, ANTHROPIC_API_KEY
from linkedin_scraper import scrape_linkedin_jobs
from portal_verifier import verify_jobs
from ats_matcher import filter_best_fits
from telegram_sender import send_message


def format_job_alert(best_fits, good_fits, stats):
    """Build Telegram message from scored results."""
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    lines = []

    lines.append(f"AI Job Hunter Report")
    lines.append(f"{now}")
    lines.append("")
    lines.append(f"Pipeline: {stats['scraped']} scraped -> "
                 f"{stats['verified']} verified -> "
                 f"{stats['best']} best fit | {stats['good']} good fit")
    lines.append(f"AI Scoring: {'Claude Haiku' if stats['ai_used'] else 'Keyword-only'}")
    lines.append("")

    good_min = 40 if ANTHROPIC_API_KEY else 15
    best_thr = ATS_THRESHOLD if ANTHROPIC_API_KEY else 25

    if best_fits:
        lines.append(f"--- BEST FIT (>={best_thr}%) ---")
        lines.append("")
        for i, job in enumerate(best_fits[:8], 1):
            lines.append(f"{i}. {job['title']}")
            lines.append(f"   Company: {job['company']}")
            lines.append(f"   Location: {job['location']}")
            sal = job.get('salary')
            if sal:
                lines.append(f"   Salary: {sal}")
            lines.append(f"   Score: {job['final_score']}% "
                         f"[KW:{job['keyword_score']}% "
                         f"AI:{job.get('ai_score', 'N/A')}%]")
            if job.get("ai_verdict") and job["ai_verdict"] not in ("SKIPPED", "NO_API_KEY"):
                lines.append(f"   AI Verdict: {job['ai_verdict']}")
            if job.get("ai_reason"):
                lines.append(f"   Why: {job['ai_reason']}")
            lines.append(f"   Apply: {job['url']}")
            if job.get("easy_apply"):
                lines.append(f"   [Easy Apply]")
            lines.append("")

    if good_fits:
        lines.append(f"--- GOOD FIT ({good_min}-{best_thr-1}%) ---")
        lines.append("")
        for i, job in enumerate(good_fits[:5], 1):
            lines.append(f"{i}. {job['title']} @ {job['company']}")
            lines.append(f"   Location: {job['location']} | Score: {job['final_score']}%")
            lines.append(f"   Apply: {job['url']}")
            lines.append("")

    if not best_fits and not good_fits:
        lines.append("No strong matches today. Pipeline will retry tomorrow.")
        lines.append("")

    lines.append("Powered by AI Job Hunter Agent")
    lines.append("github.com/amansharma03feb/job-hunter-ai")

    return "\n".join(lines)


def run_pipeline():
    """Execute the full multi-stage validation pipeline."""
    print("=" * 60)
    print("AI JOB HUNTER — Multi-Source Validation Pipeline")
    print("=" * 60)

    # ── Stage 1: Scrape ──
    print("\n[Stage 1/5] SCRAPE — LinkedIn via Apify")
    jobs = scrape_linkedin_jobs()
    if not jobs:
        print("[Pipeline] No jobs scraped. Exiting.")
        send_message("AI Job Hunter: No jobs found in today's scrape. Will retry tomorrow.")
        return

    # ── Stage 2: Verify ──
    print(f"\n[Stage 2/5] VERIFY — Checking {len(jobs)} job URLs")
    active_jobs, expired_count = verify_jobs(jobs)
    if not active_jobs:
        print("[Pipeline] All jobs expired. Exiting.")
        send_message("AI Job Hunter: All scraped jobs were expired/ghost postings. Will retry tomorrow.")
        return

    # ── Stage 3: Score ──
    print(f"\n[Stage 3/5] SCORE — Hybrid keyword + AI analysis on {len(active_jobs)} jobs")
    best_fits, good_fits, all_scored = filter_best_fits(active_jobs)

    # ── Stage 4: Filter ──
    print(f"\n[Stage 4/5] FILTER — {len(best_fits)} best fits, {len(good_fits)} good fits")

    # ── Stage 5: Deliver ──
    print(f"\n[Stage 5/5] DELIVER — Sending to Telegram")
    ai_used = any(j.get("ai_score") is not None for j in all_scored)
    stats = {
        "scraped": len(jobs),
        "expired": expired_count,
        "verified": len(active_jobs),
        "best": len(best_fits),
        "good": len(good_fits),
        "ai_used": ai_used,
    }
    message = format_job_alert(best_fits, good_fits, stats)

    # Telegram has 4096 char limit — split if needed
    if len(message) <= 4096:
        resp = send_message(message)
    else:
        chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
        for chunk in chunks:
            resp = send_message(chunk)

    if resp.get("ok"):
        print(f"\n[Pipeline] Delivered to Telegram (msg_id: {resp['result']['message_id']})")
    else:
        print(f"\n[Pipeline] Telegram error: {resp}")

    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print(f"  Scraped:  {stats['scraped']} LinkedIn jobs")
    print(f"  Expired:  {stats['expired']} ghost postings removed")
    print(f"  Verified: {stats['verified']} active jobs")
    print(f"  Best Fit: {stats['best']} jobs (>={ATS_THRESHOLD}%)")
    print(f"  Good Fit: {stats['good']} jobs (50-{ATS_THRESHOLD-1}%)")
    print(f"  AI Model: {'Claude Haiku 4.5' if stats['ai_used'] else 'Keyword-only (no API key)'}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
