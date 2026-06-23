"""Hybrid ATS Matcher: Weighted keyword scoring + Claude API semantic analysis."""

import json
import requests
from config import ANTHROPIC_API_KEY, SKILL_WEIGHTS, RESUME_SUMMARY, ATS_THRESHOLD, AI_RESUME_SUMMARY, AI_JOB_KEYWORDS


# ── Stage 1: Keyword-based weighted scoring ──────────────────────────────────

def keyword_score(description):
    """Fast keyword scan returning (score, matched_categories, gaps)."""
    if not description:
        return 0, {}, []

    desc = str(description or "").lower()
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


def _pick_resume(description):
    """Choose AI resume or healthcare resume based on JD keywords."""
    desc_lower = (description or "").lower()
    ai_matches = sum(1 for kw in AI_JOB_KEYWORDS if kw in desc_lower)
    return AI_RESUME_SUMMARY if ai_matches >= 2 else RESUME_SUMMARY


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
                            resume=_pick_resume(desc_truncated),
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


MAX_CLAUDE_CALLS = 8    # ~$0.016/run max (Haiku ~$0.002/call)
MIN_KW_FOR_AI = 8       # Skip junk JDs — only score if keyword match >= 8%

# ── Score cache — avoid re-scoring same JD across runs ──────────────────────
import os, json, hashlib

_CACHE_FILE = os.path.join(os.path.dirname(__file__), "output", "score_cache.json")

def _load_cache():
    try:
        with open(_CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache):
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    try:
        with open(_CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass

def _desc_hash(desc):
    return hashlib.md5((desc or "")[:2000].encode()).hexdigest()


def filter_best_fits(jobs):
    """Score all jobs and return only those meeting threshold, sorted by score."""
    cache = _load_cache()

    # Stage 1: keyword-score everything (free, fast)
    for job in jobs:
        desc = job.get("description", "")
        kw, cats, gaps = keyword_score(desc)
        job["keyword_score"] = kw
        job["keyword_categories"] = cats
        job["keyword_gaps"] = gaps
        job["final_score"] = kw   # provisional

    # Stage 2: Claude AI only on top-N by keyword score (saves credits)
    # Skip jobs with very low keyword match — they won't score well anyway
    if ANTHROPIC_API_KEY:
        candidates = [j for j in jobs if j["keyword_score"] >= MIN_KW_FOR_AI]
        candidates.sort(key=lambda j: j["keyword_score"], reverse=True)
        top_jobs = candidates[:MAX_CLAUDE_CALLS]

        api_calls = 0
        cache_hits = 0
        for job in top_jobs:
            desc = job.get("description", "")
            dh = _desc_hash(desc)

            # Check cache first
            if dh in cache:
                ai_result = cache[dh]
                cache_hits += 1
            else:
                ai_result = claude_score(desc)
                if ai_result:
                    cache[dh] = ai_result
                api_calls += 1

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

        print(f"[ATS] AI scoring: {api_calls} API calls, {cache_hits} cache hits (saved credits)")
        _save_cache(cache)
        scored = jobs
    else:
        scored = jobs

    # Check if AI scoring actually succeeded
    ai_worked = any(j.get("ai_score") is not None for j in scored)

    if ai_worked:
        best_threshold = ATS_THRESHOLD   # 50%
        good_min = 30
    else:
        best_threshold = 20
        good_min = 10

    best = [j for j in scored if j["final_score"] >= best_threshold]
    best.sort(key=lambda j: j["final_score"], reverse=True)

    good = [j for j in scored if good_min <= j["final_score"] < best_threshold]
    good.sort(key=lambda j: j["final_score"], reverse=True)

    mode = f"AI+Keyword (threshold {best_threshold}%)" if ai_worked else f"Keyword-only (threshold {best_threshold}%)"
    print(f"[ATS] Scored {len(scored)} jobs [{mode}]: "
          f"{len(best)} BEST FIT (>={best_threshold}%), "
          f"{len(good)} GOOD FIT ({good_min}-{best_threshold-1}%)")

    return best, good, scored
