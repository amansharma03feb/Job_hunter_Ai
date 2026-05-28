# Product Requirements Document
## AI Job Hunter Agent
**Version**: 2.0  
**Author**: Aman Sharma  
**Last Updated**: May 2026  
**Status**: Active Development  
**Repo**: https://github.com/amansharma03feb/Job_hunter_Ai

---

## 1. Product Overview

AI Job Hunter is an autonomous, end-to-end job application agent built in Python. It scrapes LinkedIn daily, scores jobs using Claude AI, finds recruiter contact info, tailors resume and cover letter per role, sends cold emails, tracks all activity in Excel, uploads documents to Google Drive, and delivers curated alerts to Telegram — all without manual intervention.

The system runs automatically every morning at 8 AM IST via GitHub Actions.

---

## 2. Problem Statement

| Pain Point | Impact |
|---|---|
| Manual LinkedIn job search takes 1–2 hrs/day | Lost productivity |
| Ghost postings (expired jobs still showing) | Wasted applications |
| Generic resume submitted to every role | Low response rate |
| No personalized outreach to recruiters | Missed warm-contact opportunities |
| No tracking of applications sent | Chaotic, duplicates, no follow-up |
| Documents scattered across local machine | Can't access from phone/tablet |

---

## 3. Goals & Success Metrics

### Primary Goal
Automate the full job application funnel from discovery → outreach → tracking for a Senior BA actively relocating to Ireland/UK/EU.

### Success Metrics
| Metric | Target |
|---|---|
| Daily jobs scraped (Ireland + UK + India) | ≥ 80 |
| Ghost posting removal rate | 100% before scoring |
| AI scoring accuracy (BEST FIT relevance) | ≥ 85% |
| Cold emails sent per day (capped) | ≤ 5 |
| Resume tailoring time per role | < 30 seconds |
| Time to Telegram delivery after scrape | < 10 minutes |
| Duplicate outreach prevention | 100% |
| Drive upload success rate | ≥ 99% |

---

## 4. Target User

**Aman Sharma** — Senior Business Analyst (6+ years)  
- Domain: Healthcare Data, MDM, AWS/Kafka/Snowflake, HIPAA, AI/LLM  
- Seeking: Senior BA / Technical Product Owner / Data Product Owner  
- Target Markets: Ireland 🇮🇪 · UK 🇬🇧 · India 🇮🇳 (global teams with travel)  
- Timeline: Relocation by Jul 2026  

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI JOB HUNTER — v2.0                            │
│              GitHub Actions cron: 02:30 UTC (8AM IST)               │
└─────────────────────────────────────────────────────────────────────┘

Stage 1: SCRAPE
  LinkedIn (Public) ──► Apify Actor ──► 16 targeted queries
  [curious_coder/linkedin-jobs-scraper]   Ireland · UK · India (24hr filter)
  Two regional batches (50 jobs each) → ~100 raw jobs

Stage 2: VERIFY
  Concurrent HTTP GET on all job URLs
  Removes ghost postings (expired/404/no-longer-accepting)
  → ~95-100 active jobs

Stage 3: SCORE
  All jobs: fast weighted keyword scan (6 categories)
  Top 15 by keyword: Claude Haiku AI semantic scoring
  Final score = 20% keyword + 80% AI
  → BEST FIT ≥60% | GOOD FIT 40-59%

Stage 4: OUTREACH (BEST FIT only, max 5/day)
  ├─ HR Finder     Extract poster name/title from Apify job data
  ├─ Email Finder  Guess pattern → validate MX + Hunter.io
  ├─ Resume Tailor Claude Haiku → tailored bullets → save DOCX
  ├─ Cover Letter  Claude Haiku → personalised letter → save DOCX
  ├─ Email Draft   Claude Haiku → subject + body
  ├─ Gmail Send    SMTP SSL with both DOCX attached
  ├─ Drive Upload  Company folder → Resume + Cover Letter saved
  └─ Excel Log     Append row to application_log.xlsx

Stage 5: DELIVER
  Telegram Bot (@AmanJobHunterBot)
  → BEST FIT jobs with score, HR info, email status, apply link
  → GOOD FIT shortlist
```

---

## 6. Module Inventory

| File | Purpose | External API |
|---|---|---|
| `main.py` | Pipeline orchestrator | — |
| `config.py` | All settings + env vars + full resume text | — |
| `linkedin_scraper.py` | LinkedIn job scraping in regional batches | Apify |
| `portal_verifier.py` | Concurrent HTTP ghost-post filter | HTTP |
| `ats_matcher.py` | Hybrid keyword + Claude AI ATS scorer | Anthropic |
| `hr_finder.py` | Extract HR info, resolve company domain | DNS |
| `email_finder.py` | Generate + validate email patterns | Hunter.io (opt) |
| `resume_tailor.py` | Tailor resume, cover letter, email draft | Anthropic |
| `email_sender.py` | Gmail SMTP sender with attachments | Gmail SMTP |
| `gdrive_uploader.py` | Upload DOCX to Google Drive by company folder | Google Drive API |
| `application_tracker.py` | Excel application log | — |
| `telegram_sender.py` | Telegram Bot alerts | Telegram Bot API |

---

## 7. Feature Requirements

### F1 — LinkedIn Scraping
- **F1.1** Scrape using `curious_coder/linkedin-jobs-scraper` Apify actor
- **F1.2** Run two regional batches: Global (Ireland/UK) and India
- **F1.3** Filter to jobs posted in last 24 hours (`f_TPR=r86400`)
- **F1.4** Deduplicate by job ID across all queries
- **F1.5** Target 16 query combinations covering all target roles

### F2 — Ghost Post Verification
- **F2.1** Concurrent HTTP GET on all job URLs (max 5 workers)
- **F2.2** Mark as expired if: HTTP 404, "no longer accepting", "job not found"
- **F2.3** Remove all expired jobs before scoring
- **F2.4** Log expired count in pipeline summary

### F3 — AI Scoring
- **F3.1** Stage 1: Keyword scan across 6 weighted categories (free, all jobs)
- **F3.2** Stage 2: Claude Haiku semantic scoring on top 15 by keyword rank
- **F3.3** Score = domain fit + seniority fit + skills match + role alignment (0–100)
- **F3.4** Final = 20% keyword + 80% AI
- **F3.5** BEST FIT ≥ 60% | GOOD FIT 40–59% | LOW < 40%
- **F3.6** Fall back to keyword-only if `ANTHROPIC_API_KEY` not set

### F4 — HR Discovery
- **F4.1** Extract poster name + title from Apify job data (no extra API call)
- **F4.2** Resolve company email domain from LinkedIn company URL slug
- **F4.3** Try TLDs in order: `.com`, `.ie`, `.co.uk`, `.co.in`, `.io`, `.net`
- **F4.4** Validate domain has MX records before generating patterns

### F5 — Email Finding
- **F5.1** Generate email patterns: `firstname.lastname@`, `f.lastname@`, `firstname@`
- **F5.2** Validate via Hunter.io if API key configured (25 free/month)
- **F5.3** Fall back to MX-verified "likely" guess if no API key
- **F5.4** Return confidence: `verified` | `likely` | `guess`
- **F5.5** Skip outreach if no email can be found

### F6 — Resume Tailoring
- **F6.1** Prompt Claude Haiku to rewrite bullets matching JD keywords
- **F6.2** Preserve all factual experience — no hallucination policy
- **F6.3** Save tailored resume as `.docx` with formatted header
- **F6.4** Generate personalised cover letter (3 paragraphs, max 250 words)
- **F6.5** Save cover letter as `.docx`
- **F6.6** Draft cold email subject + body (max 150 words)

### F7 — Google Drive Upload
- **F7.1** Parent folder: `Aman- AI resumes` (ID: `1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp`)
- **F7.2** Auto-create company subfolder if it doesn't exist
- **F7.3** Upload resume DOCX to `{Company Name}/` folder
- **F7.4** Upload cover letter DOCX to `{Company Name}/` folder
- **F7.5** Return shareable Drive link for each uploaded file
- **F7.6** Authenticate via Google Service Account JSON (stored in env)
- **F7.7** Gracefully skip Drive upload if credentials not configured

### F8 — Gmail Outreach
- **F8.1** Send via Gmail SMTP SSL (port 465)
- **F8.2** Attach tailored resume + cover letter as DOCX
- **F8.3** Use Claude-drafted personalised subject + body
- **F8.4** Cap at `MAX_EMAILS_PER_RUN = 5` per day
- **F8.5** Deduplication: never re-email same company + role
- **F8.6** Log send status (sent / failed reason) to Excel

### F9 — Application Tracker (Excel)
- **F9.1** File: `output/application_log.xlsx`
- **F9.2** Columns: Date, Company, Role, Location, AI Score, HR Name, HR Title, HR Email, Confidence, Email Status, Apply URL, Resume File
- **F9.3** Alternating row shading, frozen header, hyperlinked apply URLs
- **F9.4** `get_already_contacted()` deduplication check before each outreach

### F10 — Telegram Delivery
- **F10.1** Send formatted alert on every run (even with 0 matches)
- **F10.2** BEST FIT section: score breakdown, HR name, email status, apply URL
- **F10.3** GOOD FIT section: top 5 shortlist with apply links
- **F10.4** Split message at 4096-char Telegram limit
- **F10.5** Include emails-sent count in header stats

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Cost** | Claude API: ≤ 15 calls/run (top keyword-filtered only) |
| **Cost** | Apify: free tier sufficient for 2 × 50 jobs/day |
| **Runtime** | Full pipeline ≤ 12 minutes |
| **Security** | `.env` never committed; all secrets in GitHub Actions secrets |
| **Reliability** | Each stage fails gracefully; pipeline continues to Telegram delivery |
| **Deduplication** | Excel tracker prevents re-contacting same company+role |
| **Rate limiting** | 3-second delay between outreach actions |
| **Spam protection** | Max 5 cold emails per day; Gmail App Password only |

---

## 9. Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `APIFY_TOKEN` | ✅ | LinkedIn scraping via Apify |
| `ANTHROPIC_API_KEY` | ✅ | Claude AI scoring + resume tailoring |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram alert delivery |
| `TELEGRAM_CHAT_ID` | ✅ | Target chat for alerts |
| `GMAIL_ADDRESS` | ⚡ Optional | Gmail sender address |
| `GMAIL_APP_PASSWORD` | ⚡ Optional | Gmail App Password (not real password) |
| `GDRIVE_SERVICE_ACCOUNT_JSON` | ⚡ Optional | Base64-encoded service account JSON |
| `GDRIVE_FOLDER_ID` | ⚡ Optional | Parent Drive folder ID |
| `HUNTER_API_KEY` | ⚡ Optional | Hunter.io email verification (25/month free) |

---

## 10. Folder & Output Structure

```
job-hunter-ai/
├── main.py                    Pipeline entry point
├── config.py                  All settings + resume text
├── linkedin_scraper.py        Apify scraper
├── portal_verifier.py         Ghost-post filter
├── ats_matcher.py             Hybrid ATS scorer
├── hr_finder.py               HR name + domain resolver
├── email_finder.py            Email pattern generator + validator
├── resume_tailor.py           Claude-powered resume/CL/email drafter
├── gdrive_uploader.py         Google Drive upload module
├── email_sender.py            Gmail SMTP sender
├── application_tracker.py     Excel application log
├── telegram_sender.py         Telegram Bot alerts
├── requirements.txt
├── .env.example               Template (safe to commit)
├── .env                       ⛔ NEVER COMMIT
├── PRD.md                     This document
├── linkedin_post.md           LinkedIn post content
├── .github/
│   └── workflows/
│       └── daily_job_hunt.yml  GitHub Actions cron
└── output/                    ⛔ gitignored
    ├── resumes/               Local copies of tailored resumes
    ├── cover_letters/         Local copies of cover letters
    └── application_log.xlsx   Master outreach log

Google Drive (cloud):
└── Aman- AI resumes/          (ID: 1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp)
    ├── Accenture/
    │   ├── Aman_Sharma_Resume_SeniorBA_Accenture_YYYYMMDD.docx
    │   └── CoverLetter_SeniorBA_Accenture_YYYYMMDD.docx
    ├── McKesson/
    │   ├── Aman_Sharma_Resume_AIAutomationBA_McKesson_YYYYMMDD.docx
    │   └── CoverLetter_AIAutomationBA_McKesson_YYYYMMDD.docx
    └── ...
```

---

## 11. GitHub Actions Workflow

```yaml
Schedule: 02:30 UTC daily = 8:00 AM IST
Trigger:  cron + manual workflow_dispatch
Secrets:  APIFY_TOKEN, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN,
          TELEGRAM_CHAT_ID, GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
          GDRIVE_SERVICE_ACCOUNT_JSON, GDRIVE_FOLDER_ID
```

---

## 12. Roadmap

| Phase | Feature | Status |
|---|---|---|
| v1.0 | Scrape + score + Telegram | ✅ Done |
| v1.1 | Ghost-post filter | ✅ Done |
| v1.2 | India job queries | ✅ Done |
| v2.0 | HR finder + email outreach + resume tailoring | ✅ Done |
| v2.1 | Google Drive upload (Company folder structure) | ✅ Done |
| v2.2 | Excel application tracker | ✅ Done |
| v2.3 | Visa sponsorship signal detection in JD | 🔲 Planned |
| v2.4 | Application status follow-up (7-day reminder) | 🔲 Planned |
| v2.5 | EU expansion: Netherlands, Germany | 🔲 Planned |
| v3.0 | LinkedIn Easy Apply automation | 🔲 Planned |

---

## 13. Setup Guide (Quick Start)

```bash
# 1. Clone
git clone https://github.com/amansharma03feb/Job_hunter_Ai.git
cd Job_hunter_Ai

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Fill in APIFY_TOKEN, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# 4. (Optional) Gmail outreach
# Add GMAIL_ADDRESS + GMAIL_APP_PASSWORD to .env
# App Password: myaccount.google.com → Security → App passwords

# 5. (Optional) Google Drive upload
# See GDRIVE_SETUP.md for one-time service account setup

# 6. Run
python main.py
```

---

*Built with Python · Apify · Claude AI · Telegram Bot API · Gmail SMTP · Google Drive API*  
*Maintained by Aman Sharma — amansharma03feb@gmail.com*
