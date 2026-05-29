# Product Requirements Document
## AI Job Hunter Agent
**Version**: 2.1  
**Author**: Aman Sharma  
**Last Updated**: May 2026  
**Status**: ✅ Live — runs daily at 8 AM IST via GitHub Actions  
**Repo**: https://github.com/amansharma03feb/Job_hunter_Ai

---

## 1. Product Overview

AI Job Hunter is an autonomous, end-to-end job application agent built in Python. Every morning at 8 AM IST it scrapes LinkedIn, scores jobs using Claude AI, finds recruiter contact info, tailors a resume and cover letter per role, sends cold emails with attachments, uploads documents to Google Drive, tracks all activity in Excel, and delivers curated alerts to Telegram — zero manual intervention required.

---

## 2. Problem Statement

| Pain Point | Impact |
|---|---|
| Manual LinkedIn job search takes 1–2 hrs/day | Lost productivity |
| Ghost postings (expired jobs still showing) | Wasted applications |
| Generic resume submitted to every role | Low response rate |
| No personalised outreach to recruiters | Missed warm-contact opportunities |
| No tracking of applications sent | Chaotic, duplicates, no follow-up |
| Documents scattered across local machine | Can't access from phone/tablet |

---

## 3. Goals & Success Metrics

### Primary Goal
Automate the full job application funnel — discovery → AI scoring → personalised outreach → document storage → tracking — for a Senior BA actively relocating to Ireland/UK/EU.

### Success Metrics
| Metric | Target |
|---|---|
| Daily jobs scraped (Ireland + UK + India) | ≥ 80 |
| Ghost posting removal rate | 100% before scoring |
| AI scoring accuracy (BEST FIT relevance) | ≥ 85% |
| Cold emails sent per day | ≤ 20 |
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
╔══════════════════════════════════════════════════════════════════════════╗
║              AI JOB HUNTER — v2.1  (FULLY AUTOMATED)                    ║
║         GitHub Actions cron: 02:30 UTC daily = 8:00 AM IST              ║
╚══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 1 · SCRAPE                                                        │
│                                                                          │
│  LinkedIn (Public) ──► Apify Actor ──► 16 targeted search queries       │
│  curious_coder/linkedin-jobs-scraper    Ireland · UK · India (24h)      │
│                                                                          │
│  Batch A: Global (Ireland/UK) — 50 jobs                                  │
│  Batch B: India               — 50 jobs                                  │
│                              ──────────                                  │
│                              ~100 raw jobs (deduplicated by job ID)      │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 2 · VERIFY  (Ghost-Post Filter)                                   │
│                                                                          │
│  Concurrent HTTP GET on all job URLs  (max 5 workers)                   │
│  Removes: 404 · "no longer accepting" · "job not found"                 │
│                              ──────────                                  │
│                              ~95–100 active jobs                         │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 3 · SCORE  (Hybrid ATS — 20% Keyword + 80% Claude AI)            │
│                                                                          │
│  ALL jobs  ──► Weighted keyword scan (6 categories, free)               │
│  Top 15    ──► Claude Haiku semantic scoring (≤15 API calls/run)        │
│                                                                          │
│  final_score = 0.2 × keyword_score + 0.8 × ai_score                    │
│                                                                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────┐      │
│  │  BEST FIT ≥60%  │  │  GOOD FIT 40–59% │  │   LOW FIT  <40%   │      │
│  │  → Full outreach│  │  → Telegram only │  │   → Discarded     │      │
│  └─────────────────┘  └──────────────────┘  └───────────────────┘      │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │  BEST FIT only (max 20/day)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 4 · OUTREACH  (per BEST FIT job)                                  │
│                                                                          │
│  ① HR Finder      Extract poster name + title from Apify data           │
│  ② Domain Finder  Resolve company email domain (MX-validated)           │
│  ③ Email Finder   Generate patterns → validate via Hunter.io / MX       │
│  ④ Resume Tailor  Claude Haiku rewrites bullets to match JD keywords    │
│  ⑤ Cover Letter   Claude Haiku — 3-para personalised letter (250 words) │
│  ⑥ Email Draft    Claude Haiku — subject + body (150 words)             │
│  ⑦ Drive Upload   OAuth2 → Company/ subfolder → Resume + CL uploaded   │
│  ⑧ Gmail Send     SMTP SSL port 465 — both DOCX attached                │
│  ⑨ Excel Log      Append row with Drive links + email status            │
│                                                                          │
│  Rate limit: 3-second delay between jobs · 20 emails/day cap            │
│  Dedup: never re-email same company + role (Excel lookup)               │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 5 · DELIVER  (Telegram Bot @AmanJobHunterBot)                     │
│                                                                          │
│  BEST FIT section  — score breakdown, HR name, email status,            │
│                       Drive link, apply URL                              │
│  GOOD FIT section  — top 5 shortlist with apply links                   │
│  Pipeline summary  — scraped / verified / scored / emails sent          │
│  Split at 4096-char Telegram limit                                       │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────┐
                    │       CLOUD OUTPUTS               │
                    │                                   │
                    │  Google Drive                     │
                    │  └── Aman- AI resumes/            │
                    │       └── {Company}/              │
                    │            ├── Resume.docx        │
                    │            └── CoverLetter.docx   │
                    │                                   │
                    │  Excel: output/application_log    │
                    │  Cols: Date · Company · Role ·    │
                    │        Score · HR · Email ·       │
                    │        Status · Apply URL ·       │
                    │        Drive Links (resume + CL)  │
                    └──────────────────────────────────┘
```

---

## 6. Module Inventory

| File | Purpose | External API |
|---|---|---|
| `main.py` | Pipeline orchestrator (5 stages) | — |
| `config.py` | All settings, env vars, full resume text | — |
| `linkedin_scraper.py` | LinkedIn scraping in two regional batches | Apify |
| `portal_verifier.py` | Concurrent HTTP ghost-post filter | HTTP |
| `ats_matcher.py` | Hybrid keyword + Claude AI ATS scorer | Anthropic |
| `hr_finder.py` | Extract HR info, resolve company domain | DNS |
| `email_finder.py` | Generate + validate email patterns | Hunter.io (opt) |
| `resume_tailor.py` | Tailor resume, cover letter, email draft | Anthropic |
| `gdrive_uploader.py` | Upload DOCX to Drive via OAuth2 | Google Drive API |
| `gdrive_auth.py` | One-time OAuth2 refresh-token generator | Google OAuth2 |
| `email_sender.py` | Gmail SMTP sender with DOCX attachments | Gmail SMTP |
| `application_tracker.py` | Excel application log with Drive links | — |
| `telegram_sender.py` | Telegram Bot alerts | Telegram Bot API |

---

## 7. Feature Requirements

### F1 — LinkedIn Scraping
- **F1.1** Scrape using `curious_coder/linkedin-jobs-scraper` Apify actor
- **F1.2** Two regional batches: Global (Ireland/UK) and India — 50 jobs each
- **F1.3** Filter to jobs posted in last 24 hours (`f_TPR=r86400`)
- **F1.4** Deduplicate by job ID across all queries
- **F1.5** 16 query combinations covering all target roles and locations

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
- **F4.1** Extract poster name + title from Apify job data (zero extra API calls)
- **F4.2** Resolve company email domain from LinkedIn company URL slug
- **F4.3** Try TLDs in order: `.com`, `.ie`, `.co.uk`, `.co.in`, `.io`, `.net`
- **F4.4** Validate domain has MX records before generating patterns

### F5 — Email Finding
- **F5.1** Generate patterns: `firstname.lastname@`, `f.lastname@`, `firstname@`
- **F5.2** Validate via Hunter.io if API key configured (25 free/month)
- **F5.3** Fall back to MX-verified "likely" guess if no API key
- **F5.4** Return confidence: `verified` | `likely` | `guess`
- **F5.5** Skip outreach if no email can be found

### F6 — Resume Tailoring
- **F6.1** Claude Haiku rewrites bullets matching JD keywords
- **F6.2** Preserve all factual experience — no hallucination policy
- **F6.3** Save tailored resume as `.docx` with formatted header
- **F6.4** Generate personalised cover letter (3 paragraphs, max 250 words)
- **F6.5** Save cover letter as `.docx`
- **F6.6** Draft cold email subject + body (max 150 words)

### F7 — Google Drive Upload
- **F7.1** Parent folder: `Aman- AI resumes` (ID: `1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp`)
- **F7.2** Auto-create `{Company Name}/` subfolder if it doesn't exist
- **F7.3** Upload tailored resume DOCX to `{Company Name}/`
- **F7.4** Upload cover letter DOCX to `{Company Name}/`
- **F7.5** Return shareable Drive view link for each uploaded file
- **F7.6** Authenticate via **OAuth2 refresh token** (files owned by Gmail account, uses personal Drive storage)
- **F7.7** Gracefully skip if `GDRIVE_REFRESH_TOKEN` not configured

### F8 — Gmail Outreach
- **F8.1** Send via Gmail SMTP SSL (port 465)
- **F8.2** Attach tailored resume + cover letter as DOCX
- **F8.3** Use Claude-drafted personalised subject + body
- **F8.4** Cap at `MAX_EMAILS_PER_RUN = 20` per day
- **F8.5** Deduplication: never re-email same company + role
- **F8.6** Log send status (sent / failed reason) to Excel

### F9 — Application Tracker (Excel)
- **F9.1** File: `output/application_log.xlsx`
- **F9.2** Columns: Date, Company, Role, Location, AI Score, HR Name, HR Title, HR Email, Confidence, Email Status, Apply URL, Resume File, Resume (Drive), Cover Letter (Drive)
- **F9.3** Alternating row shading, frozen header, hyperlinked URLs and Drive links
- **F9.4** `get_already_contacted()` deduplication check before each outreach

### F10 — Telegram Delivery
- **F10.1** Send formatted alert on every run (even with 0 matches)
- **F10.2** BEST FIT: score breakdown, HR name, email status, Drive link, apply URL
- **F10.3** GOOD FIT: top 5 shortlist with apply links
- **F10.4** Split message at 4096-char Telegram limit
- **F10.5** Pipeline summary stats in every message header

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Cost** | Claude API: ≤ 15 calls/run (Haiku, keyword-filtered) |
| **Cost** | Apify: free tier (2 × 50 jobs/day) |
| **Cost** | Google Drive API: free (personal OAuth2) |
| **Cost** | Gmail SMTP: free |
| **Runtime** | Full pipeline ≤ 12 minutes |
| **Security** | `.env` never committed; all secrets in GitHub Actions |
| **Reliability** | Each stage fails gracefully; pipeline always reaches Telegram |
| **Deduplication** | Excel tracker prevents re-contacting same company+role |
| **Rate limiting** | 3-second delay between outreach actions |
| **Spam protection** | Max 20 cold emails per day; Gmail App Password only |

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
| `GDRIVE_FOLDER_ID` | ⚡ Optional | Parent Drive folder ID (has default) |
| `GDRIVE_CLIENT_ID` | ⚡ Optional | OAuth2 client ID (from Google Cloud) |
| `GDRIVE_CLIENT_SECRET` | ⚡ Optional | OAuth2 client secret |
| `GDRIVE_REFRESH_TOKEN` | ⚡ Optional | OAuth2 refresh token (run gdrive_auth.py once) |
| `HUNTER_API_KEY` | ⚡ Optional | Hunter.io email verification (25/month free) |

---

## 10. Folder & Output Structure

```
job-hunter-ai/
├── main.py                    Pipeline entry point
├── config.py                  All settings + resume text
├── linkedin_scraper.py        Apify scraper (2 regional batches)
├── portal_verifier.py         Ghost-post filter
├── ats_matcher.py             Hybrid ATS scorer (keyword + Claude)
├── hr_finder.py               HR name + domain resolver
├── email_finder.py            Email pattern generator + validator
├── resume_tailor.py           Claude-powered resume/CL/email drafter
├── gdrive_uploader.py         Google Drive upload (OAuth2)
├── gdrive_auth.py             One-time OAuth2 refresh-token setup
├── email_sender.py            Gmail SMTP sender with attachments
├── application_tracker.py     Excel application log
├── telegram_sender.py         Telegram Bot alerts
├── requirements.txt
├── .env.example               Safe template (committed)
├── .env                       ⛔ NEVER COMMIT (in .gitignore)
├── oauth_client.json          ⛔ NEVER COMMIT (in .gitignore)
├── service_account.json       ⛔ NEVER COMMIT (in .gitignore)
├── PRD.md                     This document
├── GDRIVE_SETUP.md            Drive OAuth2 one-time setup guide
├── .github/
│   └── workflows/
│       └── daily_job_hunt.yml  GitHub Actions cron (02:30 UTC = 8AM IST)
└── output/                    ⛔ gitignored
    ├── resumes/               Local copies of tailored resumes
    ├── cover_letters/         Local copies of cover letters
    └── application_log.xlsx   Master outreach log (14 columns)

Google Drive (cloud):
└── Aman- AI resumes/          (ID: 1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp)
    ├── Accenture/
    │   ├── Aman_Sharma_Resume_SeniorBA_Accenture_YYYYMMDD.docx
    │   └── CoverLetter_SeniorBA_Accenture_YYYYMMDD.docx
    ├── McKesson/
    │   ├── Aman_Sharma_Resume_DataProductOwner_McKesson_YYYYMMDD.docx
    │   └── CoverLetter_DataProductOwner_McKesson_YYYYMMDD.docx
    └── ...
```

---

## 11. GitHub Actions Workflow

```yaml
Schedule:  cron: '30 2 * * *'   →  02:30 UTC = 8:00 AM IST
Trigger:   cron + manual workflow_dispatch
Runner:    ubuntu-latest, Python 3.11
Secrets:   APIFY_TOKEN, ANTHROPIC_API_KEY,
           TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
           GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
           GDRIVE_FOLDER_ID, GDRIVE_CLIENT_ID,
           GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN
```

---

## 12. Scoring Logic

```
Keyword Categories (Stage 1 — all jobs, free):
  ┌─────────────────────┬────────┬────────────────────────────────────────┐
  │ Category            │ Weight │ Key signals                            │
  ├─────────────────────┼────────┼────────────────────────────────────────┤
  │ core_ba             │   3    │ agile, scrum, BRD, user stories, UAT  │
  │ data_platform       │   4    │ Kafka, Snowflake, AWS, ETL, S3         │
  │ healthcare          │   4    │ HIPAA, MDM, claims, HL7, golden record │
  │ ai_ml               │   3    │ LLM, prompt engineering, GenAI         │
  │ reporting_bi        │   2    │ Power BI, Tableau, SQL, MSTR           │
  │ integration         │   3    │ REST API, JSON, microservices          │
  └─────────────────────┴────────┴────────────────────────────────────────┘

Claude AI Scoring (Stage 2 — top 15 by keyword rank):
  Evaluates: domain fit · seniority fit · skills match · role alignment
  Returns: score 0–100, verdict (STRONG/GOOD/WEAK/SKIP), reason

Final Score Formula:
  final_score = round(0.20 × keyword_score + 0.80 × ai_score)

Thresholds:
  BEST FIT  ≥ 60%  →  Full outreach (resume + email + Drive upload)
  GOOD FIT  40–59% →  Telegram shortlist only
  LOW FIT   < 40%  →  Discarded
```

---

## 13. Roadmap

| Phase | Feature | Status |
|---|---|---|
| v1.0 | Scrape + score + Telegram | ✅ Done |
| v1.1 | Ghost-post filter | ✅ Done |
| v1.2 | India job queries | ✅ Done |
| v2.0 | HR finder + email outreach + resume tailoring | ✅ Done |
| v2.1 | Google Drive upload (OAuth2, Company folder structure) | ✅ Done |
| v2.2 | Excel application tracker with Drive links | ✅ Done |
| v2.3 | Visa sponsorship signal detection in JD | 🔲 Planned |
| v2.4 | Application status follow-up (7-day reminder) | 🔲 Planned |
| v2.5 | EU expansion: Netherlands, Germany | 🔲 Planned |
| v3.0 | LinkedIn Easy Apply automation | 🔲 Planned |

---

## 14. Setup Guide (Quick Start)

```bash
# 1. Clone
git clone https://github.com/amansharma03feb/Job_hunter_Ai.git
cd Job_hunter_Ai

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Fill in: APIFY_TOKEN, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# 4. (Optional) Gmail outreach
# Add GMAIL_ADDRESS + GMAIL_APP_PASSWORD to .env
# App Password: myaccount.google.com → Security → App passwords

# 5. (Optional) Google Drive upload
# See GDRIVE_SETUP.md — one-time OAuth2 setup (10 min)
# Then add GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN

# 6. Run
python main.py
```

---

## 15. Cost Summary

| Service | Plan | Cost |
|---|---|---|
| Apify | Free tier | $0 |
| Claude Haiku | Pay-per-use (~15 calls/run) | ~$0.01–0.03/run |
| Telegram Bot API | Free | $0 |
| Gmail SMTP | Free (App Password) | $0 |
| Google Drive API | Free (personal OAuth2) | $0 |
| Hunter.io | Free tier (25 verifications/month) | $0 |
| GitHub Actions | Free tier (2000 min/month) | $0 |

**Total running cost: ~$0.30–0.90/month** (Claude API only)

---

*Built with Python · Apify · Claude AI · Telegram Bot API · Gmail SMTP · Google Drive API*  
*Maintained by Aman Sharma — amansharma03feb@gmail.com*  
*"Automate the grind. Own the outcome."*
