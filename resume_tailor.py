"""
Resume & Outreach Builder — PDF ONLY (never DOCX).

RULES:
  - Resume: always send the master PDF (assets/master_resume.pdf)
  - Cover letter: generated as PDF matching professional format
  - Email: personalized per JD, attachments are PDF only
  - Drive: upload PDF only, never Word

Generates:
  - Resume PDF (copy of master resume with company-specific filename)
  - Cover letter PDF (personalized per company/role)
  - Email subject + body (personalized per JD)
"""

import os
import re
import shutil
from datetime import datetime
from fpdf import FPDF
from config import SENDER_NAME, AI_JOB_KEYWORDS

OUTPUT_DIR  = "output"
RESUMES_DIR = os.path.join(OUTPUT_DIR, "resumes")
CL_DIR      = os.path.join(OUTPUT_DIR, "cover_letters")
_ASSETS     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
MASTER_RESUME    = os.path.join(_ASSETS, "master_resume.pdf")
AI_RESUME        = os.path.join(_ASSETS, "ai_resume.pdf")


def _is_ai_job(job_title, description=""):
    """Return True if the job matches AI/AdTech profile."""
    text = f"{job_title} {description}".lower()
    return sum(1 for kw in AI_JOB_KEYWORDS if kw in text) >= 2


def _safe_filename(s):
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", str(s or ""))[:40]


def _sanitize_latin1(text):
    """Replace Unicode chars that latin-1 can't encode."""
    replacements = {
        '–': '-',   # en-dash
        '—': '-',   # em-dash
        '‘': "'",   # left single quote
        '’': "'",   # right single quote
        '“': '"',   # left double quote
        '”': '"',   # right double quote
        '•': '-',   # bullet
        '▸': '>',   # triangle bullet
        '…': '...', # ellipsis
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Final safety net — drop anything still non-latin1
    return text.encode('latin-1', errors='replace').decode('latin-1')


# ── Resume PDF (master copy) ────────────────────────────────────────────────

def save_resume_pdf(job_title, company, description=""):
    """Copy the right resume PDF (AI or healthcare) with company-specific filename.
    NEVER generates DOCX. Always PDF."""
    os.makedirs(RESUMES_DIR, exist_ok=True)
    ai_job = _is_ai_job(job_title, description)
    source = AI_RESUME if ai_job and os.path.exists(AI_RESUME) else MASTER_RESUME
    tag = "AI" if ai_job else "Healthcare"
    fname = f"Aman_Sharma_Resume_{_safe_filename(company)}.pdf"
    path = os.path.join(RESUMES_DIR, fname)

    if os.path.exists(source):
        shutil.copy2(source, path)
        print(f"   [Resume] {tag} PDF ready: {fname}")
    else:
        _generate_fallback_resume_pdf(path)
        print(f"   [Resume] Fallback PDF generated: {fname}")

    return path


def _generate_fallback_resume_pdf(path):
    """Basic fallback PDF if master resume file is missing."""
    from config import RESUME_FULL

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Blue color matching master resume
    BLUE = (43, 87, 151)

    # Name header
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 12, "AMAN SHARMA", ln=True, align="C")

    # Subtitle
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6,
             "Sr. Business / System Analyst | Healthcare Data & AI | "
             "Claims - MDM - Agentic AI | Snowflake - SQL",
             ln=True, align="C")

    # Contact line
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6,
             "amansharma03feb@gmail.com | +91 8404902779 | "
             "linkedin.com/in/aman-sharma-a32577162 | Noida, UP, India",
             ln=True, align="C")
    pdf.ln(6)

    # Body
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for line in RESUME_FULL.strip().split("\n"):
        stripped = line.strip()
        if not stripped:
            pdf.ln(3)
            continue
        stripped = _sanitize_latin1(stripped)
        if stripped.isupper() or (stripped.endswith(":") and len(stripped) < 50):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*BLUE)
            pdf.cell(0, 7, stripped, ln=True)
            pdf.set_draw_color(*BLUE)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
        else:
            pdf.multi_cell(0, 5, stripped)

    pdf.output(path)


# ── Cover Letter PDF ─────────────────────────────────────────────────────────

def _healthcare_paragraphs(job_title, company):
    return [
        f"I am writing to express my strong interest in the {job_title} "
        f"position at {company}.",

        f"With 6+ years of experience in the US Healthcare domain - "
        f"delivering healthcare data platforms, member identity resolution (MDM), "
        f"claims and eligibility data analysis, and HIPAA-compliant reporting "
        f"workflows - I bring a proven track record across Fortune-class health "
        f"insurance clients. At CloudAngles, I own end-to-end requirements for a "
        f"Fortune-class US health insurer across claims, eligibility, member MDM, "
        f"and Snowflake governance, working with six cross-functional teams.",

        f"My core strengths include SQL-based data analysis and validation in "
        f"Snowflake, BRD/FRD documentation, ETL pipeline requirements (Kafka, "
        f"Airflow on AWS), and serving as the compliance anchor for HIPAA/PHI "
        f"governance. I hold a CSPO certification and an MBA in Business Analytics.",

        f"I am actively targeting Senior BA / Technical Product Owner roles in "
        f"Ireland, UK, UAE, and global teams with a relocation timeline of July 2026. "
        f"I believe my background closely aligns with what {company} is looking "
        f"for, and I would welcome the opportunity to discuss how I can contribute "
        f"to your team.",

        f"Please find my resume attached. I look forward to hearing from you.",
    ]


def _ai_paragraphs(job_title, company):
    return [
        f"I am writing to express my strong interest in the {job_title} "
        f"position at {company}.",

        f"I am an AI-Native Business Analyst with 6+ years of experience who "
        f"goes beyond documentation - building working RAG applications, agentic "
        f"AI prototypes, and AI-generated UI mockups. I am hands-on across the "
        f"full AI-native BA toolkit: LangGraph-orchestrated agentic workflows, "
        f"RAG pipeline architecture, state management, tool access patterns, "
        f"external memory design, and prompt engineering.",

        f"At CloudAngles, I applied an AI-native approach to MDM decision review "
        f"using LangGraph-orchestrated agentic workflows (candidate ingestion, "
        f"confidence scoring, auto-merge gate, steward review, audit memo), "
        f"RAG-based operational Q&A, and PII masking layers. Previously at "
        f"AdCuratio Media, I built requirements for a multi-channel addressable "
        f"TV platform covering audience targeting, ad delivery prediction, and "
        f"Experian demographic integration.",

        f"I am actively targeting AI/AdTech BA and Product Owner roles in "
        f"Ireland, UK, UAE, and global teams with a relocation timeline of July 2026. "
        f"I believe my hands-on AI experience closely aligns with what {company} "
        f"is looking for, and I would welcome the opportunity to discuss how I "
        f"can contribute to your team.",

        f"Please find my resume attached. I look forward to hearing from you.",
    ]


def save_cover_letter_pdf(cl_text, job_title, company, hr_name, description=""):
    """Generate a professional cover letter PDF. Never DOCX."""
    os.makedirs(CL_DIR, exist_ok=True)
    fname = f"CoverLetter_{_safe_filename(company)}.pdf"
    path = os.path.join(CL_DIR, fname)

    greeting_name = str(hr_name or "").split()[0] if hr_name else "Hiring Manager"
    date_str = datetime.now().strftime("%d %B %Y")
    ai_job = _is_ai_job(job_title, description)

    BLUE = (43, 87, 151)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    # Header
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 8, "AMAN SHARMA", ln=True, align="R")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "amansharma03feb@gmail.com", ln=True, align="R")
    pdf.cell(0, 6, "+91 8404902779", ln=True, align="R")
    pdf.cell(0, 6, "linkedin.com/in/aman-sharma-a32577162", ln=True, align="R")
    pdf.cell(0, 6, date_str, ln=True, align="R")
    pdf.ln(12)

    # Greeting
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, _sanitize_latin1(f"Dear {greeting_name},"), ln=True)
    pdf.ln(4)

    # Body paragraphs — AI or healthcare
    paragraphs = _ai_paragraphs(job_title, company) if ai_job else _healthcare_paragraphs(job_title, company)

    pdf.set_font("Helvetica", "", 11)
    for para in paragraphs:
        pdf.multi_cell(0, 6, _sanitize_latin1(para))
        pdf.ln(4)

    # Sign-off
    subtitle = "Sr. Business Analyst | AI & AdTech Domain" if ai_job else "Senior Business / System Analyst | US Healthcare Data"
    pdf.ln(4)
    pdf.cell(0, 7, "Warm regards,", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 7, "Aman Sharma", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, subtitle, ln=True)
    pdf.cell(0, 6, "amansharma03feb@gmail.com", ln=True)
    pdf.cell(0, 6, "linkedin.com/in/aman-sharma-a32577162", ln=True)

    pdf.output(path)
    tag = "AI" if ai_job else "Healthcare"
    print(f"   [CoverLetter] {tag} PDF ready: {fname}")
    return path


# ── Email template ───────────────────────────────────────────────────────────

def draft_email(job_title, company, hr_first_name, description=""):
    """Return (subject, body). Attachments are always PDF.
    Subject format per Rule 5: [Role] - [Name] - [Key Differentiator]"""
    first = str(hr_first_name or "").strip() or "Hiring Manager"
    ai_job = _is_ai_job(job_title, description)

    if ai_job:
        subject = (
            f"{job_title} - Aman Sharma - "
            f"AI-Native BA | Agentic AI & RAG"
        )
        body = (
            f"Dear {first},\n\n"
            f"I came across the {job_title} opening at {company} and would love "
            f"to be considered.\n\n"
            f"I'm an AI-Native Business Analyst with 6+ years of experience - "
            f"I go beyond documentation to build working RAG applications, "
            f"agentic AI prototypes (LangGraph), and AI-generated UI mockups. "
            f"At CloudAngles, I applied AI-native approaches to MDM decision "
            f"review using LangGraph-orchestrated agentic workflows and "
            f"RAG-based operational Q&A. Previously at AdCuratio Media, I "
            f"delivered a multi-channel addressable TV platform with audience "
            f"targeting and ad delivery prediction.\n\n"
            f"My resume and cover letter are attached as PDF. Happy to connect "
            f"for a quick call.\n\n"
            f"Best regards,\n"
            f"Aman Sharma\n"
            f"amansharma03feb@gmail.com | linkedin.com/in/aman-sharma-a32577162"
        )
    else:
        subject = (
            f"{job_title} - Aman Sharma - "
            f"Sr. BA | US Healthcare Data & MDM"
        )
        body = (
            f"Dear {first},\n\n"
            f"I came across the {job_title} opening at {company} and would love "
            f"to be considered.\n\n"
            f"I'm a Senior Business / System Analyst with 6+ years in the US "
            f"Healthcare domain - specialising in claims and eligibility data "
            f"analysis, member identity resolution (MDM), SQL-based data validation "
            f"in Snowflake, and HIPAA-compliant data governance. I currently own "
            f"end-to-end requirements for a Fortune-class US health insurer at "
            f"CloudAngles, working across six cross-functional teams on healthcare "
            f"data pipelines, Snowflake governance, and ETL integration (Kafka, "
            f"Airflow on AWS).\n\n"
            f"My resume and cover letter are attached as PDF. Happy to connect "
            f"for a quick call.\n\n"
            f"Best regards,\n"
            f"Aman Sharma\n"
            f"amansharma03feb@gmail.com | linkedin.com/in/aman-sharma-a32577162"
        )

    return subject, body


# ── Backward compatibility — redirect to PDF ────────────────────────────────

def save_resume_docx(resume_text, job_title, company):
    """DEPRECATED: Redirects to PDF. Never produces DOCX."""
    return save_resume_pdf(job_title, company)


def save_cover_letter_docx(cl_text, job_title, company, hr_name):
    """DEPRECATED: Redirects to PDF. Never produces DOCX."""
    return save_cover_letter_pdf(cl_text, job_title, company, hr_name)


def tailor_resume_text(job_title, company, jd_text):
    """No-op — master resume used."""
    return None


def generate_cover_letter(job_title, company, hr_name, jd_text):
    """No-op — template cover letter used."""
    return None
