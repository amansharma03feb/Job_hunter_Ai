# LinkedIn Post — AI Job Hunter Agent

---

## POST TEXT (copy-paste to LinkedIn)

---

I got tired of manually scrolling LinkedIn every morning and applying to jobs that were already closed.

So I built an AI agent that does it for me — every day at 8am.

Here's what it does (and what I learned building it):

---

**The Problem**
Job hunting manually is painful:
- Ghost postings (expired jobs still showing up)
- Keyword-filtered JDs that look relevant but aren't
- Wasting hours applying to roles that never reply

**The Solution: AI Job Hunter Pipeline**

A fully automated Python agent that:
1. Scrapes fresh LinkedIn jobs daily (Ireland, UK + India) via Apify
2. Filters ghost postings — checks every URL is still live before scoring
3. Scores each job using Claude Haiku AI — not just keywords, but semantic fit
4. Sends only the best matches straight to my Telegram at 8am IST

---

**Architecture**

```
LinkedIn (Public)
      ↓
  [Apify Scraper]          ← curious_coder/linkedin-jobs-scraper
  16 targeted queries       (Ireland + UK + India, past 24hrs)
      ↓
  [Ghost Post Filter]      ← concurrent HTTP verification
  Dead URLs removed         prevents wasting time on expired roles
      ↓
  [Hybrid ATS Scorer]      ← Stage 1: Weighted keyword matching
  2 stages                  Stage 2: Claude Haiku semantic scoring
  Final = 20% KW + 80% AI  (domain fit, seniority, role alignment)
      ↓
  [Telegram Bot]           ← @AmanJobHunterBot
  Daily 8am IST alert       BEST FIT (≥60%) + GOOD FIT (≥40%)
      ↓
  [GitHub Actions]         ← cron: 02:30 UTC = 8am IST
  Fully automated           runs even when laptop is off
```

**Tech Stack**
- Python · requests · python-dotenv
- Apify (LinkedIn scraping without login)
- Claude Haiku API (semantic job-resume matching)
- Telegram Bot API (real-time alerts)
- GitHub Actions (daily scheduler)

---

**Key Learnings**

1. **Ghost postings are a real problem** — 10-20% of LinkedIn jobs shown are already closed. Verifying URLs before scoring saves hours of wasted applications.

2. **Keywords alone lie** — A job mentioning "Snowflake" and "Agile" doesn't mean it's right for you. Claude's semantic scoring understands context: domain fit, seniority match, actual day-to-day alignment.

3. **20% keyword + 80% AI is the right mix** — Keyword scores cap out around 25% for real jobs (descriptions don't repeat your exact resume terms). Trusting Claude more gave accurate results.

4. **Apify actor IDs change** — The actor I originally hardcoded (`worldunboxer/rapid-linkedin-scraper`) was gone. Always validate actors before scheduling. Switched to `curious_coder/linkedin-jobs-scraper` which has 97% success rate and 44k+ users.

5. **dotenv `override=True` matters on Windows** — If `ANTHROPIC_API_KEY` is already set (even blank) in system environment variables, `load_dotenv()` silently skips it. `override=True` fixes this.

6. **Batch regional scraping** — Sending India + Ireland/UK queries in separate batches prevents the actor from hitting its result cap and skipping entire regions.

---

**What's next**
- Add visa sponsorship signal detection in JD text
- Track application history (avoid re-alerting same jobs)
- Expand to EU: Netherlands, Germany

---

**Why I built this publicly**

I'm a Senior Business Analyst (6+ yrs, healthcare data/MDM/AI) actively seeking roles in Ireland, UK, and EU. Rather than just applying, I wanted to demonstrate what I can build — combining data pipeline thinking, AI APIs, and automation.

This is a real tool running real searches on my real profile. Not a demo. Not a tutorial copy.

If you're hiring for Senior BA / Technical Product Owner / Data Product Owner roles in Ireland, UK, or India (global teams with travel) — I'd love to connect.

---

**GitHub**: [github.com/amansharma03feb/job-hunter-ai]
**Bot**: @AmanJobHunterBot (live on Telegram)

#Python #AI #JobSearch #ClaudeAI #Automation #DataEngineering #BusinessAnalyst #OpenToWork #AIAgent #LinkedIn #Apify #TelegramBot #GitHubActions

---

## ARCHITECTURE DIAGRAM (for the post image)

Create this as a visual using Canva / draw.io / Excalidraw:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI JOB HUNTER PIPELINE                        │
│                  Built with Python + Claude AI                   │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │   LinkedIn   │────▶│    Apify     │────▶│  Ghost Post      │
  │  (Public)    │     │   Scraper    │     │  Filter          │
  │              │     │              │     │  (HTTP Verify)   │
  │ 16 queries:  │     │ curious_coder│     │                  │
  │ - Ireland    │     │ /linkedin-   │     │ Removes expired  │
  │ - UK         │     │ jobs-scraper │     │ job postings     │
  │ - India      │     │              │     │ before scoring   │
  └──────────────┘     └──────────────┘     └────────┬─────────┘
                                                      │
                                                      ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                   HYBRID ATS SCORER                          │
  │                                                              │
  │  Stage 1: Keyword Matching          Stage 2: Claude Haiku   │
  │  • Healthcare (4x weight)           • Domain fit (0-25)     │
  │  • Data Platform (4x weight)        • Seniority fit (0-25)  │
  │  • Core BA (3x weight)              • Skills match (0-25)   │
  │  • AI/ML (3x weight)                • Role alignment (0-25) │
  │  • Integration (3x weight)                                  │
  │  • Reporting/BI (2x weight)         Final = 20% KW + 80% AI│
  └──────────────────────────────────────────────────────────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
      ┌─────────────┐  ┌───────────┐  ┌──────────────┐
      │  BEST FIT   │  │ GOOD FIT  │  │  LOW FIT     │
      │   ≥ 60%     │  │  40-59%   │  │   < 40%      │
      │  Delivered  │  │ Delivered │  │  Discarded   │
      └──────┬──────┘  └─────┬─────┘  └──────────────┘
             └───────┬────────┘
                     ▼
          ┌─────────────────────┐
          │   Telegram Bot      │
          │  @AmanJobHunterBot  │
          │  Daily 8am IST      │
          │  (GitHub Actions    │
          │   cron 02:30 UTC)   │
          └─────────────────────┘
```

---

## CAROUSEL SLIDES (optional — 5 slides for better reach)

**Slide 1 (Hook)**
"I automated my job search with AI.
Here's the full pipeline I built in Python."

**Slide 2 (Problem)**
"Ghost postings waste your time.
I built a verifier that checks every URL before scoring."

**Slide 3 (AI Scoring)**
"Keywords lie. Context doesn't.
Claude Haiku scores semantic fit — domain, seniority, role alignment."

**Slide 4 (Architecture)**
[Architecture diagram above]

**Slide 5 (Result)**
"Every morning at 8am IST, I get a Telegram alert
with only the jobs that actually match my profile.
No noise. Just signal."

---
