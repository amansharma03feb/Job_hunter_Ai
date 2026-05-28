"""
Application Tracker — logs every outreach to an Excel file.
Columns: Date | Company | Role | Location | AI Score | HR Name | HR Title |
         HR Email | Email Confidence | Email Status | Apply URL | Resume File |
         Resume Drive Link | Cover Letter Drive Link
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
    "AI Score %",
    "HR Name",
    "HR Title",
    "HR Email",
    "Email Confidence",
    "Email Status",
    "Apply URL",
    "Resume File",
    "Resume (Drive)",
    "Cover Letter (Drive)",
]

_HEADER_FILL  = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT  = Font(bold=True, color="FFFFFF", size=11)
_ALT_FILL     = PatternFill("solid", fgColor="D6E4F0")

COL_WIDTHS = [14, 22, 35, 18, 12, 22, 30, 36, 16, 14, 55, 45, 45, 45]


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


def log_application(job, hr_info, hr_email, email_confidence, email_status,
                    resume_file="", resume_drive_link="", cl_drive_link=""):
    """
    Append one row to the application log Excel file.
    Creates the file if it doesn't exist.
    """
    os.makedirs("output", exist_ok=True)

    if os.path.exists(LOG_FILE):
        wb = load_workbook(LOG_FILE)
        ws = wb.active
    else:
        wb, ws = _init_workbook()

    next_row = ws.max_row + 1
    use_alt  = (next_row % 2 == 0)

    values = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        job.get("company", ""),
        job.get("title", ""),
        job.get("location", ""),
        job.get("final_score", ""),
        hr_info.get("full_name", ""),
        hr_info.get("title", ""),
        hr_email or "",
        email_confidence or "",
        email_status,
        job.get("url", ""),
        os.path.basename(resume_file) if resume_file else "",
        resume_drive_link or "",
        cl_drive_link or "",
    ]

    for col, val in enumerate(values, start=1):
        cell = ws.cell(row=next_row, column=col, value=val)
        cell.alignment = Alignment(wrap_text=False, vertical="center")
        if use_alt:
            cell.fill = _ALT_FILL

    # Hyperlink on apply URL column (col 11)
    url = job.get("url", "")
    if url:
        ws.cell(row=next_row, column=11).hyperlink = url
        ws.cell(row=next_row, column=11).font = Font(color="0563C1", underline="single")

    # Hyperlinks on Drive columns (col 13, 14)
    if resume_drive_link:
        ws.cell(row=next_row, column=13).hyperlink = resume_drive_link
        ws.cell(row=next_row, column=13).font = Font(color="0563C1", underline="single")
    if cl_drive_link:
        ws.cell(row=next_row, column=14).hyperlink = cl_drive_link
        ws.cell(row=next_row, column=14).font = Font(color="0563C1", underline="single")

    wb.save(LOG_FILE)
    return LOG_FILE


def get_already_contacted():
    """Return set of company+role pairs already emailed (avoid duplicates)."""
    if not os.path.exists(LOG_FILE):
        return set()
    wb = load_workbook(LOG_FILE, read_only=True)
    ws = wb.active
    seen = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        company = str(row[1] or "").lower()
        role    = str(row[2] or "").lower()
        seen.add(f"{company}|{role}")
    wb.close()
    return seen
