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
from config import SENDER_NAME

OUTPUT_DIR  = "output"
RESUMES_DIR = os.path.join(OUTPUT_DIR, "resumes")
CL_DIR      = os.path.join(OUTPUT_DIR, "cover_letters")
MASTER_RESUME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "master_resume.pdf")


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

def save_resume_pdf(job_title, company):
    """Copy master resume PDF with company-specific filename.
    NEVER generates DOCX. Always PDF."""
    os.makedirs(RESUMES_DIR, exist_ok=True)
    fname = f"Aman_Sharma_Resume_{_safe_filename(company)}.pdf"
    path = os.path.join(RESUMES_DIR, fname)

    if os.path.exists(MASTER_RESUME):
        shutil.copy2(MASTER_RESUME, path)
        print(f"   [Resume] PDF ready: {fname}")
    else:
        # Fallback: generate basic PDF if master not found
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
             "Sr. Business / System Analyst | US Healthcare Data | "
             "Claims - Eligibility - MDM | Snowflake - SQL - HIPAA",
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

def save_cover_letter_pdf(cl_text, job_title, company, hr_name):
    """Generate a professional cover letter PDF. Never DOCX."""
    os.makedirs(CL_DIR, exist_ok=True)
    fname = f"CoverLetter_{_safe_filename(company)}.pdf"
    path = os.path.join(CL_DIR, fname)

    greeting_name = str(hr_name or "").split()[0] if hr_name else "Hiring Manager"
    date_str = datetime.now().strftime("%d %B %Y")

    BLUE = (43, 87, 151)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    # Header — right aligned, matching resume blue
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

    # Body paragraphs
    paragraphs = [
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
        f"Ireland, UK, and global teams with a relocation timeline of July 2026. "
        f"I believe my background closely aligns with what {company} is looking "
        f"for, and I would welcome the opportunity to discuss how I can contribute "
        f"to your team.",

        f"Please find my resume attached. I look forward to hearing from you.",
    ]

    pdf.set_font("Helvetica", "", 11)
    for para in paragraphs:
        pdf.multi_cell(0, 6, _sanitize_latin1(para))
        pdf.ln(4)

    # Sign-off
    pdf.ln(4)
    pdf.cell(0, 7, "Warm regards,", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 7, "Aman Sharma", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Senior Business / System Analyst | US Healthcare Data", ln=True)
    pdf.cell(0, 6, "amansharma03feb@gmail.com", ln=True)
    pdf.cell(0, 6, "linkedin.com/in/aman-sharma-a32577162", ln=True)

    pdf.output(path)
    print(f"   [CoverLetter] PDF ready: {fname}")
    return path


# ── Email template ───────────────────────────────────────────────────────────

def draft_email(job_title, company, hr_first_name):
    """Return (subject, body). Attachments are always PDF.
    Subject format per Rule 5: [Role] - [Name] - [Key Differentiator]"""
    first = str(hr_first_name or "").strip() or "Hiring Manager"

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
