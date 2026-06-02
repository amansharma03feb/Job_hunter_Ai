"""
Application Tracker — logs every outreach to an Excel file.

Columns include JD summary, ATS score breakdown, HR details, Drive links,
and application status — per Rule 4.
"""

import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

LOG_FILE = os.path.join("output", "application_log.xlsx")

HEADERS = [
    "Date",
    "Company",
    "Role",
    "Location",
    "JD Summary",
    "JD Source URL",
    "ATS Score %",
    "Keyword Score %",
    "AI Score %",
    "AI Verdict",
    "HR Name",
    "HR Title",
    "HR Email",
    "Email Confidence",
    "Email Status",
    "Resume Version",
    "Resume (Drive)",
    "Cover Letter (Drive)",
    "Apply URL",
    "Status",
]

_HEADER_FILL  = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT  = Font(bold=True, color="FFFFFF", size=11)
_ALT_FILL     = PatternFill("solid", fgColor="D6E4F0")

COL_WIDTHS = [
    14,  # Date
    22,  # Company
    35,  # Role
    18,  # Location
    50,  # JD Summary
    40,  # JD Source URL
    12,  # ATS Score %
    12,  # Keyword Score %
    12,  # AI Score %
    14,  # AI Verdict
    22,  # HR Name
    30,  # HR Title
    36,  # HR Email
    16,  # Email Confidence
    14,  # Email Status
    20,  # Resume Version
    45,  # Resume (Drive)
    45,  # Cover Letter (Drive)
    55,  # Apply URL
    14,  # Status
]


def _init_workbook():
    wb = Workbook()
    ws = wb.active
    ws.title = "Applications"

    for col, (header, width) in enumerate(zip(HEADERS, COL_WIDTHS), start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font  = _HEADER_FONT
        cell.fill  = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = width

    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"
    return wb, ws


def _truncate_jd(description, max_words=100):
    """Truncate JD to max_words for the summary column."""
    if not description:
        return ""
    words = str(description).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "..."


def log_application(job, hr_info, hr_email, email_confidence, email_status,
                    resume_file="", resume_drive_link="", cl_drive_link=""):
    """
    Append one row to the application log Excel file.
    Creates the file with new headers if it doesn't exist.
    Includes JD summary, all score breakdowns, and status per Rule 4.
    """
    os.makedirs("output", exist_ok=True)

    if os.path.exists(LOG_FILE):
        wb = load_workbook(LOG_FILE)
        ws = wb.active
        # Check if headers match — if old format, recreate
        current_headers = [ws.cell(row=1, column=c).value for c in range(1, len(HEADERS) + 1)]
        if current_headers != HEADERS:
            # Old format — rename old file and create new
            backup = LOG_FILE.replace(".xlsx", "_backup.xlsx")
            wb.save(backup)
            wb.close()
            wb, ws = _init_workbook()
            print(f"   [Tracker] Old format backed up to {backup}, new tracker created")
    else:
        wb, ws = _init_workbook()

    next_row = ws.max_row + 1
    use_alt  = (next_row % 2 == 0)

    # Determine status
    if email_status == "sent":
        status = "Applied"
    elif email_status == "already contacted":
        status = "Duplicate"
    elif "failed" in str(email_status):
        status = "Failed"
    elif email_status == "email_not_found":
        status = "No Contact"
    else:
        status = "Drafted"

    values = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),                    # Date
        job.get("company", ""),                                        # Company
        job.get("title", ""),                                          # Role
        job.get("location", ""),                                       # Location
        _truncate_jd(job.get("description", "")),                      # JD Summary
        job.get("url", ""),                                            # JD Source URL
        job.get("final_score", ""),                                    # ATS Score %
        job.get("keyword_score", ""),                                  # Keyword Score %
        job.get("ai_score", "") if job.get("ai_score") is not None else "",  # AI Score %
        job.get("ai_verdict", ""),                                     # AI Verdict
        hr_info.get("full_name", ""),                                  # HR Name
        hr_info.get("title", ""),                                      # HR Title
        hr_email or "",                                                # HR Email
        email_confidence or "",                                        # Email Confidence
        email_status,                                                  # Email Status
        os.path.basename(resume_file) if resume_file else "master_resume.pdf",  # Resume Version
        resume_drive_link or "",                                       # Resume (Drive)
        cl_drive_link or "",                                           # Cover Letter (Drive)
        job.get("url", ""),                                            # Apply URL
        status,                                                        # Status
    ]

    for col, val in enumerate(values, start=1):
        cell = ws.cell(row=next_row, column=col, value=val)
        cell.alignment = Alignment(wrap_text=(col == 5), vertical="center")  # Wrap JD summary
        if use_alt:
            cell.fill = _ALT_FILL

    # Hyperlinks on URL columns
    url_columns = {6: job.get("url", ""), 19: job.get("url", "")}
    for col_idx, url in url_columns.items():
        if url:
            ws.cell(row=next_row, column=col_idx).hyperlink = url
            ws.cell(row=next_row, column=col_idx).font = Font(color="0563C1", underline="single")

    # Hyperlinks on Drive columns (17, 18)
    if resume_drive_link:
        ws.cell(row=next_row, column=17).hyperlink = resume_drive_link
        ws.cell(row=next_row, column=17).font = Font(color="0563C1", underline="single")
    if cl_drive_link:
        ws.cell(row=next_row, column=18).hyperlink = cl_drive_link
        ws.cell(row=next_row, column=18).font = Font(color="0563C1", underline="single")

    wb.save(LOG_FILE)
    return LOG_FILE


def get_already_contacted():
    """Return set of company+role pairs already emailed (avoid duplicates)."""
    if not os.path.exists(LOG_FILE):
        return set()
    try:
        wb = load_workbook(LOG_FILE, read_only=True)
        ws = wb.active
        seen = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            company = str(row[1] or "").lower()
            role    = str(row[2] or "").lower()
            seen.add(f"{company}|{role}")
        wb.close()
        return seen
    except Exception:
        return set()
