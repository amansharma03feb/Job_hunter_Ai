"""
AI Job Hunter — Full Multi-Source Outreach Pipeline  v3.4

Sources:   LinkedIn · RemoteOK  (Indeed/ZipRecruiter disabled from India)
           JobSpy free · Apify LinkedIn fallback · Apollo recruiter emails

Stages:
  1. SCRAPE       — LinkedIn (JobSpy parallel) + RemoteOK
  2. SCORE        — Hybrid keyword + Claude Haiku ATS scoring (cached)
  3. VERIFY       — Ghost-post filter (HTTP URL check)
  4. OUTREACH     — 7-tier email chain: JD > Apollo > poster > DDG > website > Hunter > alias
                    PDF resume + cover letter · Google Drive · Gmail SMTP · Excel tracker
  5. FOLLOW-UP    — Multi-touch sequence (Day 5 + Day 10)
  6. DELIVER      — Telegram alert with apply links
"""

import re
import time
from datetime import datetime

from config import (
    ATS_THRESHOLD, ANTHROPIC_API_KEY, GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD, MAX_EMAILS_PER_RUN, FOLLOWUP_AFTER_DAYS,
    ENABLE_LINKEDIN, ENABLE_INDEED, ENABLE_ZIPRECRUITER, ENABLE_REMOTE,
)
from jobspy_scraper import scrape_linkedin_jobs, scrape_indeed_jobs, scrape_ziprecruiter_jobs
from remote_scraper import scrape_remote_jobs
from portal_verifier import verify_jobs
from ats_matcher import filter_best_fits
from telegram_sender import send_message
from hr_finder import (
    extract_hr_info, guess_company_domain, find_agency_contact,
    enrich_with_poster_data, find_website_hr_contact, google_find_recruiter,
    apollo_find_recruiter,
)
from resume_tailor import draft_email, save_resume_pdf, save_cover_letter_pdf
from gdrive_uploader import upload_documents
from email_sender import send_application_email
from application_tracker import log_application, get_already_contacted, get_followup_candidates, update_status


# ── Telegram formatter ────────────────────────────────────────────────────────

def format_job_alert(best_fits, good_fits, stats):
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    ai_active = stats.get("ai_used", False)
    good_min = 30 if ai_active else 10
    best_thr = ATS_THRESHOLD if ai_active else 20
    lines = []

    source_summary = "  ".join(
        f"{k.capitalize()}:{v}"
        for k, v in stats.get("sources", {}).items() if v
    )

    lines += [
        "AI Job Hunter Report",
        now,
        "",
        f"Sources: {source_summary or 'LinkedIn'}",
        f"Pipeline: {stats['scraped']} scraped -> "
        f"{stats['best']} best | {stats['good']} good",
        f"Scoring: {'Claude Haiku' if stats['ai_used'] else 'Keyword-only'}",
        f"Emails sent: {stats.get('emails_sent', 0)}",
        "",
    ]

    # Action items section — what user should manually do
    easy_apply_jobs = [j for j in best_fits if j.get("easy_apply")]
    direct_portal_jobs = [j for j in best_fits
                          if j.get("apply_url") and "linkedin.com" not in str(j.get("apply_url", ""))]
    if easy_apply_jobs or direct_portal_jobs:
        lines.append("--- ACTION REQUIRED ---")
        lines.append("")
        if easy_apply_jobs:
            lines.append(f"Easy Apply ({len(easy_apply_jobs)} jobs):")
            for j in easy_apply_jobs[:5]:
                lines.append(f"  {j['title']} @ {j['company']}")
                lines.append(f"  {j['url']}")
            lines.append("")
        if direct_portal_jobs:
            lines.append(f"Direct Apply ({len(direct_portal_jobs)} portals):")
            for j in direct_portal_jobs[:5]:
                lines.append(f"  {j['title']} @ {j['company']}")
                lines.append(f"  {j.get('apply_url', j['url'])}")
            lines.append("")

    if best_fits:
        lines.append(f"--- BEST FIT (>={best_thr}%) ---")
        lines.append("")
        for i, job in enumerate(best_fits[:10], 1):
            src = str(job.get("source", "linkedin")).upper()
            lines.append(f"{i}. [{src}] {str(job.get('title',''))}")
            lines.append(f"   {str(job.get('company',''))} | {str(job.get('location',''))}")
            sal = job.get("salary")
            if sal:
                lines.append(f"   Salary: {str(sal)}")
            lines.append(
                f"   Score: {job['final_score']}% "
                f"[KW:{job['keyword_score']}% AI:{job.get('ai_score','N/A')}%]"
            )
            if job.get("ai_verdict") not in (None, "SKIPPED", "NO_API_KEY"):
                lines.append(f"   AI: {job['ai_verdict']} -- {job.get('ai_reason','')}")
            hr = job.get("_hr_info", {})
            if hr.get("full_name") and hr["full_name"] != "Hiring Team":
                lines.append(f"   HR: {hr['full_name']} ({hr.get('title','')})")
            email_status = job.get("_email_status", "")
            if email_status:
                lines.append(f"   Email: {email_status}")
            lines.append(f"   Apply: {job['url']}")
            if job.get("easy_apply"):
                lines.append("   >> Easy Apply - click above!")
            lines.append("")

    if good_fits:
        lines.append(f"--- GOOD FIT ({good_min}-{best_thr-1}%) ---")
        lines.append("")
        for i, job in enumerate(good_fits[:5], 1):
            src = job.get("source", "linkedin").upper()
            lines.append(f"{i}. [{src}] {job['title']} @ {job['company']}")
            lines.append(f"   {job['location']} | Score: {job['final_score']}%")
            lines.append(f"   Apply: {job['url']}")
            lines.append("")

    if not best_fits and not good_fits:
        lines.append("No strong matches today. Pipeline retries tomorrow.")
        lines.append("")

    lines += [
        "Powered by AI Job Hunter Agent v3.3",
        f"Runtime: {stats.get('runtime', '?')}",
    ]
    return "\n".join(lines)


# ── Outreach for one job ──────────────────────────────────────────────────────

def run_outreach(job, already_contacted):
    """
    Full outreach flow for a single BEST FIT job.
    Handles both named-poster (LinkedIn) and agency/no-poster jobs.
    Returns email_sent (bool).
    """
    title   = str(job.get("title", "") or "")
    company = str(job.get("company", "") or "")
    jd_text = str(job.get("description", "") or "")

    # Dedup check
    key = f"{company.lower()}|{title.lower()}"
    if key in already_contacted:
        print(f"   [Outreach] Already contacted {company} for {title} — skipping")
        job["_email_status"] = "already contacted"
        return False

    # 1. Extract HR info from job data (works for LinkedIn with poster info)
    hr_info = extract_hr_info(job)
    job["_hr_info"] = hr_info
    print(f"   [HR] {hr_info['full_name'] or 'No poster'} ({hr_info['title'] or 'unknown title'})")

    # 2. Resolve domain
    domain = guess_company_domain(company, job.get("companyLinkedinUrl", ""))

    # 3. Find email — 5-tier priority chain
    hr_email, confidence = None, None

    # Priority 1: Email found directly in job description (most reliable)
    jd_emails = str(job.get("jd_emails", "") or "").strip()
    if jd_emails:
        # Take first valid-looking email from JD
        for candidate in jd_emails.replace(",", " ").split():
            candidate = candidate.strip().lower()
            if "@" in candidate and "." in candidate.split("@")[1]:
                hr_email, confidence = candidate, "jd_direct"
                print(f"   [Email] Found in JD: {hr_email}")
                break

    # Priority 2: Apollo — verified recruiter emails (best source)
    if not hr_email:
        apollo = apollo_find_recruiter(company)
        if apollo:
            hr_info.update({
                "full_name":    apollo.get("full_name", "") or hr_info["full_name"],
                "first_name":   apollo.get("first_name", "") or hr_info["first_name"],
                "last_name":    apollo.get("last_name", "") or hr_info["last_name"],
                "title":        apollo.get("title", "") or hr_info["title"],
                "linkedin_url": apollo.get("linkedin_url", "") or hr_info.get("linkedin_url", ""),
            })
            job["_hr_info"] = hr_info
            if apollo.get("email"):
                hr_email = apollo["email"]
                confidence = "apollo_verified"
                print(f"   [Email] Apollo verified: {hr_email} ({hr_info['full_name']})")
            elif hr_info["first_name"] and hr_info["last_name"] and domain:
                f = re.sub(r"[^a-z]", "", hr_info["first_name"].lower())
                l = re.sub(r"[^a-z]", "", hr_info["last_name"].lower())
                if f and l:
                    hr_email = f"{f}.{l}@{domain}"
                    confidence = "apollo_pattern"
                    print(f"   [Email] Apollo name + pattern: {hr_email} ({hr_info['full_name']})")

    # Priority 3: Named poster — build firstname.lastname@domain
    if not hr_email and hr_info["first_name"] and hr_info["last_name"] and domain:
        f = re.sub(r"[^a-z]", "", hr_info["first_name"].lower())
        l = re.sub(r"[^a-z]", "", hr_info["last_name"].lower())
        if f and l:
            hr_email, confidence = f"{f}.{l}@{domain}", "pattern"
            print(f"   [Email] Pattern: {hr_email}")

    # Priority 4: Google/DuckDuckGo recruiter search (FREE)
    if not hr_email and domain:
        google_result = google_find_recruiter(company, domain)
        if google_result:
            f = re.sub(r"[^a-z]", "", google_result["first_name"].lower())
            l = re.sub(r"[^a-z]", "", google_result["last_name"].lower())
            if f and l:
                hr_email = f"{f}.{l}@{domain}"
                confidence = "google_recruiter"
                hr_info.update({
                    "full_name":  google_result["full_name"],
                    "first_name": google_result["first_name"],
                    "last_name":  google_result["last_name"],
                    "title":      google_result["title"],
                    "linkedin_url": google_result.get("linkedin_url", ""),
                })
                job["_hr_info"] = hr_info
                print(f"   [Email] Google recruiter: {hr_email} ({hr_info['full_name']})")

    # Priority 5: Scrape company website for real emails (FREE)
    if not hr_email and domain:
        web_result = find_website_hr_contact(domain, company)
        if web_result and web_result.get("email"):
            hr_email = web_result["email"]
            confidence = "website_scrape"
            if web_result.get("first_name"):
                hr_info.update({
                    "full_name":  web_result["full_name"],
                    "first_name": web_result["first_name"],
                    "last_name":  web_result["last_name"],
                    "title":      web_result["title"],
                })
                job["_hr_info"] = hr_info
            print(f"   [Email] Website scrape: {hr_email}")

    # Priority 6: Hunter.io domain search (if key available)
    if not hr_email and domain:
        hunter_result = find_agency_contact(company, domain)
        if hunter_result and hunter_result.get("email") and hunter_result.get("source") == "hunter_domain":
            hr_email = hunter_result["email"]
            confidence = "hunter_verified"
            hr_info.update({
                "full_name":  hunter_result["full_name"],
                "first_name": hunter_result["first_name"],
                "last_name":  hunter_result["last_name"],
                "title":      hunter_result["title"],
            })
            job["_hr_info"] = hr_info
            print(f"   [Email] Hunter.io: {hr_email} ({hr_info['full_name']}, {hr_info['title']})")

    # Priority 7: Try HR-role generic aliases (recruitment@, talent@, hr@)
    if not hr_email and domain:
        for alias in ["recruitment", "talent", "hr", "hiring", "careers"]:
            hr_email, confidence = f"{alias}@{domain}", "hr_alias"
            break
        hr_info.update({"full_name": "Hiring Team", "first_name": "Hiring",
                        "last_name": "Team", "title": "Recruitment"})
        job["_hr_info"] = hr_info
        print(f"   [Email] HR alias: {hr_email}")

    if not hr_email:
        print(f"   [Email] Could not find any contact for {company}")
        job["_email_status"] = "email not found"
        log_application(job, hr_info, None, None, "email_not_found")
        return False

    print(f"   [Email] {hr_email} (confidence: {confidence})")

    # Flag direct apply opportunities
    apply_url = job.get("apply_url") or job.get("url", "")
    if job.get("easy_apply"):
        print(f"   [Apply] Easy Apply available — {apply_url}")
    elif apply_url and "linkedin.com" not in apply_url:
        print(f"   [Apply] Direct portal: {apply_url}")
        job["_direct_applied"] = False  # user can manually apply

    desc = job.get("description", "")

    # 4. Save resume PDF (AI or healthcare based on JD)
    resume_path = save_resume_pdf(title, company, desc)

    # 5. Save cover letter PDF (AI or healthcare based on JD)
    cl_path = save_cover_letter_pdf("", title, company, hr_info["full_name"], desc)

    # 6. Template email (AI or healthcare based on JD)
    subject, body = draft_email(title, company, hr_info["first_name"], desc)

    # 7. Upload to Google Drive
    print(f"   [Drive] Uploading documents for {company}...")
    resume_link, cl_link = upload_documents(company, resume_path, cl_path)
    job["_resume_drive_link"] = resume_link or ""
    job["_cl_drive_link"]     = cl_link or ""

    # 8. Send email
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
        success      = False
        email_status = "drafted (Gmail not configured)"
        print(f"   [Send] Gmail not configured — email drafted only")

    job["_email_status"] = email_status

    # 9. Log to Excel
    log_application(
        job, hr_info, hr_email, confidence, email_status,
        resume_path or "", resume_link or "", cl_link or "",
    )

    return success


# ── Follow-up emails ─────────────────────────────────────────────────────────

def _followup_email(first_name, company, role, days, touch):
    """Generate subject + body for multi-touch follow-up sequence."""
    if touch == 1:
        # Touch 2: Warm follow-up (Day 5)
        subject = f"Quick follow-up — {role} at {company}"
        body = (
            f"Hi {first_name},\n\n"
            f"I reached out {days} days ago about the {role} position and wanted to "
            f"briefly follow up. I understand how busy hiring cycles can get.\n\n"
            f"I'm particularly excited about this role because my experience with "
            f"healthcare data platforms and AI-native BA workflows aligns closely "
            f"with what your team is building.\n\n"
            f"Happy to jump on a 15-minute call at your convenience — or if the "
            f"timing isn't right, no worries at all.\n\n"
            f"Best,\nAman Sharma\n"
            f"linkedin.com/in/amansharma03feb"
        )
    else:
        # Touch 3: Final value-add ping (Day 10)
        subject = f"One last note — {role} at {company}"
        body = (
            f"Hi {first_name},\n\n"
            f"Apologies for the extra ping — I'll keep this brief. I wanted to share "
            f"that I recently built an end-to-end agentic AI pipeline (LangGraph + RAG) "
            f"as a side project, which reinforced my conviction that BA/PO roles in AI "
            f"need someone who can bridge business requirements and technical execution.\n\n"
            f"If the {role} position is still open, I'd love to chat. If not, I'd "
            f"appreciate any referral to the right team.\n\n"
            f"Thanks for your time,\nAman Sharma\n"
            f"linkedin.com/in/amansharma03feb"
        )
    return subject, body


def run_followups(already_contacted):
    """
    Multi-touch follow-up sequence:
      Touch 2 (Day 5): Warm follow-up
      Touch 3 (Day 10): Final value-add ping
    Only for personal emails (skips generic careers@).
    Returns count of follow-ups sent.
    """
    candidates = get_followup_candidates(FOLLOWUP_AFTER_DAYS)
    if not candidates:
        print(f"\n[Follow-up] No candidates (need {FOLLOWUP_AFTER_DAYS}+ days, personal email)")
        return 0

    print(f"\n[Follow-up] {len(candidates)} candidates for follow-up")
    sent = 0

    for c in candidates[:10]:
        company = c["company"]
        role = c["role"]
        hr_email = c["hr_email"]
        hr_name = c["hr_name"] or "Hiring Team"
        days = c["days_ago"]
        touch = c.get("touch", 1)
        first_name = hr_name.split()[0] if hr_name else "Hi"

        subject, body = _followup_email(first_name, company, role, days, touch)

        if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
            try:
                success, msg = send_application_email(
                    to_email=hr_email,
                    subject=subject,
                    body=body,
                )
                if success:
                    sent += 1
                    new_status = "Followed Up" if touch == 1 else "Final Follow-up"
                    update_status(company, role, new_status, increment_touch=True)
                    print(f"   [Follow-up] Touch {touch+1} sent to {hr_email} ({company}, {days}d ago)")
                else:
                    print(f"   [Follow-up] Failed: {msg}")
            except Exception as e:
                print(f"   [Follow-up] Error: {e}")
        time.sleep(3)

    print(f"[Follow-up] Sent {sent}/{len(candidates)} follow-ups")
    return sent


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline():
    t_start = time.time()
    print("=" * 60)
    print("AI JOB HUNTER — Multi-Source Outreach Pipeline v3.4")
    print("=" * 60)

    # ── Stage 1: Scrape ──────────────────────────────────────────────────
    enabled = []
    if ENABLE_LINKEDIN:     enabled.append("LinkedIn")
    if ENABLE_INDEED:       enabled.append("Indeed")
    if ENABLE_ZIPRECRUITER: enabled.append("ZipRecruiter")
    if ENABLE_REMOTE:       enabled.append("RemoteOK")
    print(f"\n[Stage 1/6] SCRAPE — {' + '.join(enabled)}")

    linkedin_jobs, indeed_jobs, zip_jobs, remote_jobs = [], [], [], []
    scrapers = []
    if ENABLE_LINKEDIN:     scrapers.append(("LinkedIn",     lambda: scrape_linkedin_jobs()))
    if ENABLE_INDEED:       scrapers.append(("Indeed",        lambda: scrape_indeed_jobs()))
    if ENABLE_ZIPRECRUITER: scrapers.append(("ZipRecruiter",  lambda: scrape_ziprecruiter_jobs()))
    if ENABLE_REMOTE:       scrapers.append(("RemoteOK",      lambda: scrape_remote_jobs()))

    source_results = {}
    for name, fn in scrapers:
        try:
            t = time.time()
            result = fn()
            elapsed = time.time() - t
            source_results[name.lower()] = result
            print(f"  [{name}] {len(result)} jobs ({elapsed:.0f}s)")
        except Exception as e:
            source_results[name.lower()] = []
            print(f"  [{name}] FAILED: {e}")

    linkedin_jobs = source_results.get("linkedin", [])
    indeed_jobs = source_results.get("indeed", [])
    zip_jobs = source_results.get("ziprecruiter", [])
    remote_jobs = source_results.get("remoteok", [])

    # Merge and deduplicate
    seen_ids = set()
    all_jobs = []
    for job in linkedin_jobs + indeed_jobs + zip_jobs + remote_jobs:
        jid = job.get("job_id") or job.get("url", "")
        if jid and jid not in seen_ids:
            seen_ids.add(jid)
            all_jobs.append(job)

    source_counts = {
        "linkedin": len(linkedin_jobs), "indeed": len(indeed_jobs),
        "ziprecruiter": len(zip_jobs), "remote": len(remote_jobs),
    }
    print(f"\n  Total: {len(all_jobs)} unique jobs ({time.time()-t_start:.0f}s elapsed)")

    if not all_jobs:
        send_message("AI Job Hunter: No jobs scraped today. Check VPN/proxy or try later.")
        return

    # ── Stage 2: Score ───────────────────────────────────────────────────
    print(f"\n[Stage 2/6] SCORE — {len(all_jobs)} jobs")
    try:
        best_fits, good_fits, all_scored = filter_best_fits(all_jobs)
    except Exception as e:
        print(f"[SCORE] Failed: {e} — falling back to keyword-only")
        for job in all_jobs:
            from ats_matcher import keyword_score
            kw, cats, gaps = keyword_score(job.get("description", ""))
            job["keyword_score"] = kw
            job["final_score"] = kw
        best_fits = sorted([j for j in all_jobs if j["final_score"] >= 20], key=lambda j: j["final_score"], reverse=True)
        good_fits = sorted([j for j in all_jobs if 10 <= j["final_score"] < 20], key=lambda j: j["final_score"], reverse=True)
        all_scored = all_jobs

    if not best_fits and not good_fits:
        send_message(f"AI Job Hunter: Scraped {len(all_jobs)} jobs, 0 matched. Retrying tomorrow.")
        return

    # ── Stage 3: Verify ──────────────────────────────────────────────────
    # Verify best fits; if none survive, promote good fits
    expired_count = 0
    if best_fits:
        print(f"\n[Stage 3/6] VERIFY — {len(best_fits)} best-fit URLs")
        try:
            verified_best, expired_count = verify_jobs(best_fits)
            best_fits = verified_best
        except Exception as e:
            print(f"[VERIFY] Failed: {e} — using unverified best fits")

    if not best_fits and good_fits:
        print(f"[Pipeline] No best fits survived — promoting {len(good_fits)} GOOD FIT jobs")
        best_fits = good_fits[:15]
        good_fits = good_fits[15:]

    if not best_fits:
        send_message("AI Job Hunter: All matched jobs were ghost postings or expired.")
        return

    # Stage 3.5: Apify poster enrichment SKIPPED — Apollo replaces it (saves ~$0.05/run)
    # enrich_with_poster_data(best_fits)

    # ── Stage 4: Outreach ────────────────────────────────────────────────
    already_contacted = get_already_contacted()

    # Verify good fits too
    good_verified = []
    if good_fits:
        try:
            good_verified, _ = verify_jobs(good_fits[:20])
        except Exception as e:
            print(f"[VERIFY-Good] Failed: {e}")
            good_verified = good_fits[:20]

    outreach_pool = best_fits + good_verified
    new_jobs = [j for j in outreach_pool if f"{str(j.get('company','')).lower()}|{str(j.get('title','')).lower()}" not in already_contacted]

    print(f"\n[Stage 4/6] OUTREACH — {len(outreach_pool)} total ({len(best_fits)} best + {len(good_verified)} good), {len(new_jobs)} new")
    emails_sent = 0
    email_errors = 0

    for job in outreach_pool[:MAX_EMAILS_PER_RUN]:
        src = job.get("source", "linkedin").upper()
        print(f"\n  -> [{src}] {job['title']} @ {job['company']} ({job['final_score']}%)")
        try:
            sent = run_outreach(job, already_contacted)
            if sent:
                emails_sent += 1
                already_contacted.add(f"{str(job.get('company','')).lower()}|{str(job.get('title','')).lower()}")
        except Exception as e:
            email_errors += 1
            print(f"   [Outreach] ERROR: {e}")
        time.sleep(2)

    # ── Stage 5: Follow-ups ────────────────────────────────────────────
    print(f"\n[Stage 5/6] FOLLOW-UP")
    try:
        followup_sent = run_followups(already_contacted)
        emails_sent += followup_sent
    except Exception as e:
        print(f"[Follow-up] Failed: {e}")

    # ── Stage 6: Telegram ────────────────────────────────────────────────
    elapsed_total = time.time() - t_start
    print(f"\n[Stage 6/6] DELIVER — Telegram ({elapsed_total:.0f}s total)")
    ai_used = any(j.get("ai_score") is not None for j in all_scored)
    stats = {
        "scraped":      len(all_jobs),
        "expired":      expired_count,
        "verified":     len(best_fits),
        "best":         len(best_fits),
        "good":         len(good_fits),
        "ai_used":      ai_used,
        "emails_sent":  emails_sent,
        "sources":      source_counts,
        "runtime":      f"{elapsed_total/60:.1f} min",
    }

    message = format_job_alert(best_fits, good_fits, stats)
    chunks  = [message[i:i+4096] for i in range(0, len(message), 4096)]
    resp = {}
    for chunk in chunks:
        resp = send_message(chunk)

    if resp.get("ok"):
        msg_id = resp.get("result", {}).get("message_id", "?")
        print(f"\n[Pipeline] Telegram delivered (msg_id: {msg_id})")
    else:
        print(f"\n[Pipeline] Telegram response: {resp}")

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print(f"  LinkedIn:      {source_counts['linkedin']} jobs")
    print(f"  Indeed:        {source_counts['indeed']} jobs")
    print(f"  ZipRecruiter:  {source_counts['ziprecruiter']} jobs")
    print(f"  RemoteOK:      {source_counts['remote']} jobs")
    print(f"  Total scraped: {stats['scraped']}")
    print(f"  Ghost posts:   {stats['expired']} removed")
    print(f"  Verified:      {stats['verified']} active")
    print(f"  Best Fit:      {stats['best']} jobs (>={ATS_THRESHOLD}%)")
    print(f"  Good Fit:      {stats['good']} jobs (30-{ATS_THRESHOLD-1}%)")
    print(f"  Emails sent:   {emails_sent}")
    print(f"  AI Model:      {'Claude Haiku 4.5' if ai_used else 'Keyword-only'}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"\n[FATAL] Pipeline crashed:\n{tb}")
        # Always notify Telegram even on hard crash
        try:
            from datetime import datetime
            send_message(
                f"AI Job Hunter ERROR — {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
                f"Pipeline crashed:\n{str(e)}\n\n"
                f"Check GitHub Actions logs for full traceback."
            )
        except Exception:
            pass
        raise  # re-raise so GitHub Actions sees exit code 1
