"""
Email Sender — Gmail SMTP with resume + cover letter attachments.
Uses App Password (not your real Gmail password).

Setup:
  1. Enable 2FA on your Gmail account
  2. Go to myaccount.google.com/apppasswords
  3. Create app password for "Mail"
  4. Put it in .env as GMAIL_APP_PASSWORD
"""

import os
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SENDER_NAME


def send_application_email(
    to_email,
    subject,
    body,
    resume_path=None,
    cover_letter_path=None,
):
    """
    Send a job application email via Gmail SMTP.

    Returns:
        (success: bool, message: str)
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False, "GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set in .env"

    try:
        msg = MIMEMultipart()
        msg["From"]    = f"{SENDER_NAME} <{GMAIL_ADDRESS}>"
        msg["To"]      = to_email
        msg["Subject"] = subject

        # Body
        msg.attach(MIMEText(body, "plain"))

        # Attachments
        for fpath in filter(None, [resume_path, cover_letter_path]):
            if not os.path.exists(fpath):
                continue
            mime_type, _ = mimetypes.guess_type(fpath)
            mime_type = mime_type or "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)

            with open(fpath, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(fpath),
            )
            msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)

        return True, "sent"

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed — check GMAIL_APP_PASSWORD"
    except smtplib.SMTPRecipientsRefused:
        return False, f"Recipient refused: {to_email}"
    except Exception as e:
        return False, str(e)
