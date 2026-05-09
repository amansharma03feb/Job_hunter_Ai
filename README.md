# AI Job Hunter Agent

An autonomous AI-powered job hunting pipeline that scrapes LinkedIn daily, filters ghost postings, scores jobs using Claude AI, and delivers curated alerts to Telegram every morning at 8am IST.

## Pipeline Architecture

```
LinkedIn (Public)
      │
      ▼
[Apify Scraper]           ← curious_coder/linkedin-jobs-scraper
16 targeted queries        Ireland · UK · India (past 24 hrs)
      │
      ▼
[Ghost Post Filter]       ← concurrent HTTP URL verification
Removes expired jobs       before wasting time scoring them
      │
      ▼
[Hybrid ATS Scorer]       ← Stage 1: Weighted keyword scan
                               Stage 2: Claude Haiku semantic scoring
Final = 20% KW + 80% AI   Domain fit · Seniority · Role alignment
      │
      ▼
[Telegram Bot]            ← @AmanJobHunterBot
Daily 8am IST alert        BEST FIT (≥60%) · GOOD FIT (≥40%)
      │
      ▼
[GitHub Actions]          ← cron: 02:30 UTC = 8:00 AM IST
Fully automated            runs even when laptop is off
```

## Features

- **Anti-ghost-posting** — every URL is verified live before scoring
- **Semantic AI scoring** — Claude Haiku understands context (domain fit, seniority, role alignment), not just keywords
- **Dual-region search** — Ireland/UK + India batched separately to maximise results
- **Telegram delivery** — formatted alerts with score breakdown, AI verdict, and apply link
- **GitHub Actions scheduler** — runs hands-free every morning

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LinkedIn scraping | Apify (`curious_coder/linkedin-jobs-scraper`) |
| AI scoring | Claude Haiku API (`claude-haiku-4-5`) |
| Notifications | Telegram Bot API |
| Scheduler | GitHub Actions cron |
| Config | Python-dotenv |
| Language | Python 3.10+ |

## Setup

### 1. Clone and install

```bash
git clone https://github.com/amansharma03feb/job-hunter-ai.git
cd job-hunter-ai
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your keys
```

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
APIFY_TOKEN=your_apify_api_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

**Get your keys:**
- Apify token → https://console.apify.com/account/integrations
- Anthropic key → https://console.anthropic.com/settings/keys
- Telegram bot → message @BotFather on Telegram

### 3. Customise your profile

Edit `config.py`:
- `TARGET_TITLES` — roles you're targeting
- `SEARCH_QUERIES` — location + role combinations
- `SKILL_WEIGHTS` — keyword categories weighted by your profile
- `RESUME_SUMMARY` — plain-text resume summary for Claude scoring
- `ATS_THRESHOLD` — minimum score to deliver (default: 60%)

### 4. Run manually

```bash
python main.py
```

### 5. Automate (GitHub Actions)

Add secrets to your GitHub repo:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `APIFY_TOKEN`
- `ANTHROPIC_API_KEY`

The workflow `.github/workflows/daily_job_hunt.yml` runs automatically at 02:30 UTC (8:00 AM IST) every day.

## Scoring Logic

```python
# Stage 1: Keyword scan (6 categories, weighted by profile)
keyword_score = weighted_match(description, SKILL_WEIGHTS)

# Stage 2: Claude Haiku semantic scoring
ai_score = claude_haiku_score(description, resume_summary)
# Returns: skills_match + domain_fit + seniority_fit + role_alignment

# Final hybrid score
final_score = 0.20 * keyword_score + 0.80 * ai_score
```

### Skill Weight Categories

| Category | Weight | Why |
|----------|--------|-----|
| Healthcare / MDM | 4x | Core domain expertise |
| Data Platform (AWS/Kafka/Snowflake) | 4x | Primary technical stack |
| Core BA (Agile/BRD/UAT) | 3x | Foundational skills |
| AI/ML | 3x | Growing area |
| Integration (API/REST) | 3x | Daily work |
| Reporting / BI | 2x | Supporting skill |

## Project Motivation

Built as a real tool (not a demo) while actively job hunting for Senior BA / Technical Product Owner roles in Ireland, UK, and India (global teams with travel exposure).

The goal: demonstrate data pipeline thinking + AI API integration on a genuinely useful problem.

---

**Author**: Aman Sharma — Senior Business Analyst | Healthcare Data & MDM | AWS · Snowflake · Claude AI  
**Open to**: Senior BA · Technical Product Owner · Data Product Owner roles — Ireland · UK · EU · India (global teams)  
**LinkedIn**: [linkedin.com/in/amansharma03feb](https://linkedin.com/in/amansharma03feb)
