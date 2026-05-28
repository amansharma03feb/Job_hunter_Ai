"""
AI Job Hunter — Full Outreach Pipeline

Stages:
  1. SCRAPE       — LinkedIn jobs via Apify (Ireland / UK / India)
  2. VERIFY       — Ghost-post filter (HTTP URL check)
  3. SCORE        — Hybrid keyword + Claude AI ATS scoring
  4. OUTREACH     — For BEST FIT jobs:
                      a. Extract HR name from job poster info
                      b. Guess + validate HR email
                      c. Tailor resume to JD via Claude
                      d. Generate cover letter via Claude
                      e. Draft personalised email via Claude
                      f. Send email with attachments (Gmail SMTP)
                      g. Log to Excel application tracker
  5. DELIVER      — Telegram: BEST + GOOD FIT alerts + apply links
"""

import time
from datetime import datetime

from config import (
    ATS_THRESHOLD, ANTHROPIC_API_KEY, GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD, MAX_EMAILS_PER_RUN
)
from linkedin_scraper import scrape_linkedin_jobs
from portal_verifier import verify_jobs
from ats_matcher import filter_best_fits
from telegram_sender import send_message
from hr_finder import extract_hr_info, guess_company_domain, build_email_patterns
from email_finder import find_best_email
from resume_tailor import (
    tailor_resume_text, generate_cover_letter, draft_email,
    save_resume_docx, save_cover_letter_docx
)
from email_sender import send_application_email
from application_tracker import log_application, get_already_contacted


# ── Telegram formatter ────────────────────────────────────────────────────────

def format_job_alert(best_fits, good_fits, stats):
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    good_min = 40 if ANTHROPIC_API_KEY else 15
    best_thr = ATS_THRESHOLD if ANTHROPIC_API_KEY else 25
    lines = []

    lines += [
        "AI Job Hunter Report",
        now,
        "",
        f"Pipeline: {stats['scraped']} scraped -> {stats['verified']} verified -> "
        f"{stats['best']} best fit | {stats['good']} good fit",
        f"AI Scoring: {'Claude Haiku' if stats['ai_used'] else 'Keyword-only'}",
        f"Emails sent: {stats.get('emails_sent', 0)}",
        "",
    ]

    if best_fits:
        lines.append(f"--- BEST FIT (>={best_thr}%) ---")
        lines.append("")
        for i, job in enumerate(best_fits[:8], 1):
            lines.append(f"{i}. {job['title']}")
            lines.append(f"   {job['company']} | {job['location']}")
            sal = job.get("salary")
            if sal:
                lines.append(f"   Salary: {sal}")
            lines.append(
                f"   Score: {job['final_score']}% "
                f"[KW:{job['keyword_score']}% AI:{job.get('ai_score','N/A')}%]"
            )
            if job.get("ai_verdict") not in (None, "SKIPPED", "NO_API_KEY"):
                lines.append(f"   AI: {job['ai_verdict']} — {job.get('ai_reason','')}")
            hr = job.get("_hr_info", {})
            if hr.get("full_name"):
                lines.append(f"   HR: {hr['full_name']} ({hr.get('title','')})")
            email_status = job.get("_email_status", "")
            if email_status:
                lines.append(f"   Email: {email_status}")
            lines.append(f"   Apply: {job['url']}")
            if job.get("easy_apply"):
                lines.append("   [Easy Apply available]")
            lines.append("")

    if good_fits:
        lines.append(f"--- GOOD FIT ({good_min}-{best_thr-1}%) ---")
        lines.append("")
        for i, job in enumerate(good_fits[:5], 1):
            lines.append(f"{i}. {job['title']} @ {job['company']}")
            lines.append(f"   {job['location']} | Score: {job['final_score']}%")
            lines.append(f"   Apply: {job['url']}")
            lines.append("")

    if not best_fits and not good_fits:
        lines.append("No strong matches today. Pipeline retries tomorrow.")
        lines.append("")

    lines += ["Powered by AI Job Hunter Agent", "github.com/amansharma03feb/Job_hunter_Ai"]
    return "\n".join(lines)


# ── Outreach for one job ──────────────────────────────────────────────────────

def run_outreach(job, already_contacted):
    """
    Run the full outreach flow for a single BEST FIT job.
    Mutates job dict with _hr_info, _email_status keys.
    Returns email_sent (bool).
    """
    title   = job.get("title", "")
    company = job.get("company", "")
    jd_text = job.get("description", "")

    # Skip if we already emailed this company+role
    key = f"{company.lower()}|{title.lower()}"
    if key in already_contacted:
        print(f"   [Outreach] Already contacted {company} for {title} — skipping")
        job["_email_status"] = "already contacted"
        return False

    # 1. Extract HR info
    hr_info = extract_hr_info(job)
    job["_hr_info"] = hr_info
    print(f"   [HR] {hr_info['full_name'] or 'No poster'} ({hr_info['title'] or 'unknown title'})")

    # 2. Find email
    hr_email, confidence = None, None
    if hr_info["first_name"] and hr_info["last_name"]:
        domain = guess_company_domain(company, job.get("companyLinkedinUrl", ""))
        patterns = build_email_patterns(hr_info["first_name"], hr_info["last_name"], domain)
        hr_email, confidence = find_best_email(
            hr_info["first_name"], hr_info["last_name"], domain, patterns
        )

    if not hr_email:
        print(f"   [Email] Could not find email for {hr_info['full_name'] or company}")
        job["_email_status"] = "email not found"
        log_application(job, hr_info, None, None, "email_not_found")
        return False

    print(f"   [Email] {hr_email} (confidence: {confidence})")

    # 3. Tailor resume
    print(f"   [Resume] Tailoring for {title} @ {company}...")
    tailored = tailor_resume_text(title, company, jd_text)
    resume_path = save_resume_docx(tailored or "", title, company) if tailored else None

    # 4. Cover letter
    print(f"   [CL] Generating cover letter...")
    cl_text = generate_cover_letter(title, company, hr_info["full_name"], jd_text)
    cl_path = save_cover_letter_docx(cl_text or "", title, company, hr_info["full_name"]) if cl_text else None

    # 5. Draft email
    print(f"   [Draft] Writing email...")
    subject, body = draft_email(title, company, hr_info["first_name"])
    if not subject or not body:
        subject = f"Application: {title} — Aman Sharma"
        body = (
            f"Dear {hr_info['first_name'] or 'Hiring Manager'},\n\n"
            f"I'm applying for the {title} role at {company}. "
            f"Please find my tailored resume and cover letter attached.\n\n"
            f"Best regards,\nAman Sharma"
        )

    # 6. Send email (only if Gmail is configured)
    if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        success, msg = send_application_email(
            to_email=hr_email,
            subject=subject,
            body=body,
            resume_path=resume_path,
            cover_letter_path=cl_path,
        )
        email_status = "sent" if success else f"failed: {msg}"
        print(f"   [Send] {email_status}")
    else:
        success = False
        email_status = "drafted (Gmail not configured)"
        print(f"   [Send] Gmail not configured — email drafted but not sent")

    job["_email_status"] = email_status

    # 7. Log to Excel
    log_application(job, hr_info, hr_email, confidence, email_status, resume_path or "")

    return success


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline():
    print("=" * 60)
    print("AI JOB HUNTER — Full Outreach Pipeline")
    print("=" * 60)

    # Stage 1: Scrape
    print("\n[Stage 1/5] SCRAPE — LinkedIn via Apify")
    jobs = scrape_linkedin_jobs()
    if not jobs:
        send_message("AI Job Hunter: No jobs scraped today. Retrying tomorrow.")
        return

    # Stage 2: Verify
    print(f"\n[Stage 2/5] VERIFY — Checking {len(jobs)} job URLs")
    active_jobs, expired_count = verify_jobs(jobs)
    if not active_jobs:
        send_message("AI Job Hunter: All scraped jobs were ghost postings.")
        return

    # Stage 3: Score
    print(f"\n[Stage 3/5] SCORE — {len(active_jobs)} active jobs")
    best_fits, good_fits, all_scored = filter_best_fits(active_jobs)

    # Stage 4: Outreach (BEST FIT only, capped per run)
    print(f"\n[Stage 4/5] OUTREACH — {len(best_fits)} best fit jobs")
    already_contacted = get_already_contacted()
    emails_sent = 0

    for job in best_fits[:MAX_EMAILS_PER_RUN]:
        print(f"\n  -> {job['title']} @ {job['company']} ({job['final_score']}%)")
        sent = run_outreach(job, already_contacted)
        if sent:
            emails_sent += 1
        time.sleep(3)   # small delay between API calls + emails

    # Stage 5: Telegram delivery
    print(f"\n[Stage 5/5] DELIVER — Telegram")
    ai_used = any(j.get("ai_score") is not None for j in all_scored)
    stats = {
        "scraped": len(jobs),
        "expired": expired_count,
        "verified": len(active_jobs),
        "best": len(best_fits),
        "good": len(good_fits),
        "ai_used": ai_used,
        "emails_sent": emails_sent,
    }

    message = format_job_alert(best_fits, good_fits, stats)
    chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
    for chunk in chunks:
        resp = send_message(chunk)

    if resp.get("ok"):
        print(f"\n[Pipeline] Telegram delivered (msg_id: {resp['result']['message_id']})")

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print(f"  Scraped:       {stats['scraped']} LinkedIn jobs")
    print(f"  Ghost posts:   {stats['expired']} removed")
    print(f"  Verified:      {stats['verified']} active")
    print(f"  Best Fit:      {stats['best']} jobs (>={ATS_THRESHOLD}%)")
    print(f"  Good Fit:      {stats['good']} jobs (40-{ATS_THRESHOLD-1}%)")
    print(f"  Emails sent:   {emails_sent}")
    print(f"  AI Model:      {'Claude Haiku 4.5' if ai_used else 'Keyword-only'}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
