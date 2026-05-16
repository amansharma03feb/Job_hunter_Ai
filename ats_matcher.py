"""Hybrid ATS Matcher: Weighted keyword scoring + Claude API semantic analysis."""

import json
import requests
from config import ANTHROPIC_API_KEY, SKILL_WEIGHTS, RESUME_SUMMARY, ATS_THRESHOLD


# ── Stage 1: Keyword-based weighted scoring ──────────────────────────────────

def keyword_score(description):
    """Fast keyword scan returning (score, matched_categories, gaps)."""
    if not description:
        return 0, {}, []

    desc = description.lower()
    total_weight = 0
    earned_weight = 0
    matched_cats = {}
    all_gaps = []

    for cat_name, config in SKILL_WEIGHTS.items():
        w = config["weight"]
        skills = config["skills"]
        matched = [s for s in skills if s in desc]
        missed = [s for s in skills if s not in desc]

        if skills:
            ratio = len(matched) / len(skills)
            earned_weight += ratio * w
            total_weight += w

            if matched:
                matched_cats[cat_name] = {
                    "matched": matched[:5],
                    "pct": round(ratio * 100),
                }
            all_gaps.extend(missed[:2])

    score = int((earned_weight / total_weight) * 100) if total_weight else 0
    return score, matched_cats, all_gaps[:6]


# ── Stage 2: Claude API semantic scoring ─────────────────────────────────────

CLAUDE_SCORING_PROMPT = """You are an expert career advisor and ATS (Applicant Tracking System) analyst.

TASK: Score how well the CANDIDATE's resume matches the JOB DESCRIPTION on a scale of 0-100.

SCORING CRITERIA (weight each equally):
1. SKILLS MATCH (0-25): How many required/preferred skills does the candidate have?
2. DOMAIN FIT (0-25): Does the candidate's industry experience align (healthcare, data, fintech)?
3. SENIORITY FIT (0-25): Does the candidate's experience level match the role's expectations?
4. ROLE ALIGNMENT (0-25): Does the candidate's day-to-day work match what this role demands?

CANDIDATE RESUME:
{resume}

JOB DESCRIPTION:
{job_description}

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "score": <0-100>,
  "skills_match": <0-25>,
  "domain_fit": <0-25>,
  "seniority_fit": <0-25>,
  "role_alignment": <0-25>,
  "verdict": "<STRONG FIT | GOOD FIT | PARTIAL FIT | LOW FIT>",
  "reason": "<one sentence explaining the score>",
  "missing_skills": ["<skill1>", "<skill2>", "<skill3>"]
}}"""


def claude_score(description):
    """Use Claude API to semantically score job-resume fit. Returns dict or None."""
    if not ANTHROPIC_API_KEY:
        return None

    # Truncate description to avoid token waste
    desc_truncated = description[:4000] if description else ""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": CLAUDE_SCORING_PROMPT.format(
                            resume=RESUME_SUMMARY,
                            job_description=desc_truncated,
                        ),
                    }
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)

    except Exception as e:
        print(f"[ATS-AI] Claude scoring error: {e}")
        return None


# ── Combined scoring pipeline ────────────────────────────────────────────────

def score_job(job):
    """Run hybrid scoring: keyword + Claude AI. Returns enriched job dict."""
    desc = job.get("description", "")

    # Stage 1: Fast keyword pre-filter
    kw_score, kw_cats, kw_gaps = keyword_score(desc)
    job["keyword_score"] = kw_score
    job["keyword_categories"] = kw_cats
    job["keyword_gaps"] = kw_gaps

    # Stage 2: Claude AI scoring on all jobs (Haiku is cheap; don't pre-filter)
    if ANTHROPIC_API_KEY:
        ai_result = claude_score(desc)
        if ai_result:
            job["ai_score"] = ai_result.get("score", 0)
            job["ai_verdict"] = ai_result.get("verdict", "UNKNOWN")
            job["ai_reason"] = ai_result.get("reason", "")
            job["ai_missing"] = ai_result.get("missing_skills", [])
            # Final score = 20% keyword + 80% AI (Claude semantic is far more reliable)
            job["final_score"] = int(kw_score * 0.2 + job["ai_score"] * 0.8)
        else:
            job["ai_score"] = None
            job["ai_verdict"] = "SKIPPED"
            job["ai_reason"] = "Claude API unavailable"
            job["final_score"] = kw_score
    else:
        job["ai_score"] = None
        job["ai_verdict"] = "NO_API_KEY"
        job["ai_reason"] = ""
        job["final_score"] = kw_score

    return job


MAX_CLAUDE_CALLS = 15   # Cap Claude API calls per run to control costs


def filter_best_fits(jobs):
    """Score all jobs and return only those meeting threshold, sorted by score."""
    # Stage 1: keyword-score everything (free, fast)
    for job in jobs:
        desc = job.get("description", "")
        kw, cats, gaps = keyword_score(desc)
        job["keyword_score"] = kw
        job["keyword_categories"] = cats
        job["keyword_gaps"] = gaps
        job["final_score"] = kw   # provisional

    # Stage 2: Claude AI only on top-N by keyword score (saves credits)
    if ANTHROPIC_API_KEY:
        top_jobs = sorted(jobs, key=lambda j: j["keyword_score"], reverse=True)[:MAX_CLAUDE_CALLS]
        print(f"[ATS] Sending top {len(top_jobs)} keyword-filtered jobs to Claude AI...")
        for job in top_jobs:
            desc = job.get("description", "")
            ai_result = claude_score(desc)
            if ai_result:
                job["ai_score"] = ai_result.get("score", 0)
                job["ai_verdict"] = ai_result.get("verdict", "UNKNOWN")
                job["ai_reason"] = ai_result.get("reason", "")
                job["ai_missing"] = ai_result.get("missing_skills", [])
                job["final_score"] = int(job["keyword_score"] * 0.2 + job["ai_score"] * 0.8)
            else:
                job["ai_score"] = None
                job["ai_verdict"] = "SKIPPED"
                job["ai_reason"] = "Claude API unavailable"
        # remaining jobs stay at keyword-only final_score
        scored = jobs
    else:
        scored = jobs

    # When no API key, AI scoring is skipped so keyword scores are naturally lower.
    # Use a lower threshold (25% best / 15% good) to surface relevant jobs.
    if ANTHROPIC_API_KEY:
        best_threshold = ATS_THRESHOLD   # 60%
        good_min = 40
    else:
        best_threshold = 25
        good_min = 15

    best = [j for j in scored if j["final_score"] >= best_threshold]
    best.sort(key=lambda j: j["final_score"], reverse=True)

    good = [j for j in scored if good_min <= j["final_score"] < best_threshold]
    good.sort(key=lambda j: j["final_score"], reverse=True)

    mode = f"AI+Keyword (threshold {best_threshold}%)" if ANTHROPIC_API_KEY else f"Keyword-only (threshold {best_threshold}%)"
    print(f"[ATS] Scored {len(scored)} jobs [{mode}]: "
          f"{len(best)} BEST FIT (>={best_threshold}%), "
          f"{len(good)} GOOD FIT ({good_min}-{best_threshold-1}%)")

    return best, good, scored
