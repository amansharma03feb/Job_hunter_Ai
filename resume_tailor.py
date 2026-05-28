"""
Resume Tailor — uses Claude API to:
  1. Tailor resume bullet points to match a JD
  2. Generate a personalised cover letter
  3. Save both as .docx files
"""

import os
import re
import json
import requests
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from config import ANTHROPIC_API_KEY, RESUME_FULL, SENDER_NAME

OUTPUT_DIR = "output"
RESUMES_DIR = os.path.join(OUTPUT_DIR, "resumes")
CL_DIR      = os.path.join(OUTPUT_DIR, "cover_letters")


# ── Claude API helper ─────────────────────────────────────────────────────────

def _claude(prompt, max_tokens=1500):
    if not ANTHROPIC_API_KEY:
        return None
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
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            text = text[text.find("\n")+1:].strip() if "\n" in text else text[4:].strip()
        return text
    except Exception as e:
        print(f"[Tailor] Claude error: {e}")
        return None


# ── Tailored Resume ───────────────────────────────────────────────────────────

RESUME_PROMPT = """You are a senior career coach and resume writer.

TASK: Tailor the candidate's resume for the specific job below.
- Keep the same structure (sections, companies, dates)
- Rewrite/reorder bullet points to match the JD keywords and requirements
- Add/highlight skills the JD asks for that the candidate has
- Keep it truthful — do not invent experience
- Output ONLY the tailored resume text, no commentary

CANDIDATE RESUME:
{resume}

JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION:
{jd}

Output the tailored resume as plain text with clear section headers."""


def tailor_resume_text(job_title, company, jd_text):
    prompt = RESUME_PROMPT.format(
        resume=RESUME_FULL,
        job_title=job_title,
        company=company,
        jd=jd_text[:3000],
    )
    return _claude(prompt, max_tokens=2000)


# ── Cover Letter ──────────────────────────────────────────────────────────────

CL_PROMPT = """You are an expert cover letter writer for tech/data roles.

Write a concise, compelling cover letter (3 paragraphs, max 250 words):
- Para 1: Hook — why THIS role at THIS company excites the candidate
- Para 2: 2-3 specific achievements from the resume that match the JD
- Para 3: Forward-looking close with call to action

Tone: professional but human. No generic filler. No "I am writing to apply for…"

CANDIDATE: {name}
JOB TITLE: {job_title}
COMPANY: {company}
HR NAME: {hr_name}
JOB DESCRIPTION:
{jd}

CANDIDATE RESUME SUMMARY:
{resume}

Output ONLY the cover letter body text (no subject line, no address block)."""


def generate_cover_letter(job_title, company, hr_name, jd_text):
    hr_greeting = hr_name.split()[0] if hr_name else "Hiring Manager"
    prompt = CL_PROMPT.format(
        name=SENDER_NAME,
        job_title=job_title,
        company=company,
        hr_name=hr_greeting,
        jd=jd_text[:3000],
        resume=RESUME_FULL[:1500],
    )
    return _claude(prompt, max_tokens=600)


# ── Email Draft ───────────────────────────────────────────────────────────────

EMAIL_PROMPT = """Write a short, personalized job application email (150 words max).

- Subject line on first line prefixed with "Subject: "
- Then blank line, then the email body
- Address the HR by first name
- One line about why this specific role/company
- One line referencing a concrete achievement
- End with clear CTA (resume + cover letter attached)

HR FIRST NAME: {hr_first}
JOB TITLE: {job_title}
COMPANY: {company}
SENDER: {name}

SENDER BACKGROUND (2 lines): Senior BA, 6+ yrs healthcare data/MDM/AI on AWS.
Led MDM golden-record platform for a Fortune-class US health insurer;
Kafka+Airflow ETL cut processing time 50%; CSPO certified.

Output ONLY the subject line + email body."""


def draft_email(job_title, company, hr_first_name):
    prompt = EMAIL_PROMPT.format(
        hr_first=hr_first_name or "Hiring Manager",
        job_title=job_title,
        company=company,
        name=SENDER_NAME,
    )
    result = _claude(prompt, max_tokens=400)
    if not result:
        return None, None
    lines = result.strip().split("\n", 2)
    subject = ""
    body = result
    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line[8:].strip()
            body = "\n".join(lines[i+1:]).strip()
            break
    return subject, body


# ── DOCX helpers ──────────────────────────────────────────────────────────────

def _safe_filename(s):
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", s)[:40]


def save_resume_docx(resume_text, job_title, company):
    os.makedirs(RESUMES_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    fname = f"Aman_Sharma_Resume_{_safe_filename(job_title)}_{_safe_filename(company)}_{date_str}.docx"
    path = os.path.join(RESUMES_DIR, fname)

    doc = Document()
    # Title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run(SENDER_NAME)
    run.bold = True
    run.font.size = Pt(16)

    doc.add_paragraph("amansharma03feb@gmail.com  |  LinkedIn: linkedin.com/in/amansharma03feb")

    doc.add_paragraph()  # spacer

    for line in (resume_text or "").split("\n"):
        p = doc.add_paragraph()
        if line.strip().isupper() or line.strip().endswith(":"):
            run = p.add_run(line.strip())
            run.bold = True
        else:
            p.add_run(line)

    doc.save(path)
    return path


def save_cover_letter_docx(cl_text, job_title, company, hr_name):
    os.makedirs(CL_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    fname = f"CoverLetter_{_safe_filename(job_title)}_{_safe_filename(company)}_{date_str}.docx"
    path = os.path.join(CL_DIR, fname)

    doc = Document()
    # Header
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    h.add_run(f"{SENDER_NAME}\namansharma03feb@gmail.com\n{datetime.now().strftime('%d %B %Y')}")

    doc.add_paragraph()

    greeting = f"Dear {hr_name.split()[0]}," if hr_name else "Dear Hiring Manager,"
    doc.add_paragraph(greeting)
    doc.add_paragraph()

    for para in (cl_text or "").split("\n\n"):
        if para.strip():
            doc.add_paragraph(para.strip())

    doc.add_paragraph()
    doc.add_paragraph("Warm regards,")
    doc.add_paragraph(SENDER_NAME)

    doc.save(path)
    return path
