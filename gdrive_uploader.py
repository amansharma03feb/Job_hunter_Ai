"""
Google Drive Uploader — uploads tailored resume + cover letter into a
per-company subfolder inside the parent 'Aman- AI resumes' folder.

Folder structure created:
  Aman- AI resumes/           (parent, ID in GDRIVE_FOLDER_ID)
    └── {Company Name}/
          ├── Aman_Sharma_Resume_...docx
          └── CoverLetter_...docx

Authentication: OAuth2 refresh token (files are owned by your Gmail account,
using your Drive storage). Store three env vars:
  GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN

Run  python gdrive_auth.py  once to generate the refresh token.

Returns shareable "view" links for each uploaded file.
Gracefully skips (returns None, None) if credentials are not configured.
"""

import os
from config import (
    GDRIVE_FOLDER_ID,
    GDRIVE_CLIENT_ID,
    GDRIVE_CLIENT_SECRET,
    GDRIVE_REFRESH_TOKEN,
)

MIME_PDF    = "application/pdf"
MIME_FOLDER = "application/vnd.google-apps.folder"


# ── Build Drive service ───────────────────────────────────────────────────────

def _build_service():
    if not all([GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN]):
        return None
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        creds = Credentials(
            token=None,
            refresh_token=GDRIVE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GDRIVE_CLIENT_ID,
            client_secret=GDRIVE_CLIENT_SECRET,
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except ImportError:
        print("[Drive] google-api-python-client not installed — skipping Drive upload")
        return None
    except Exception as e:
        print(f"[Drive] Auth error: {e}")
        return None


# ── Folder helpers ────────────────────────────────────────────────────────────

def _get_or_create_folder(service, folder_name, parent_id):
    query = (
        f"mimeType='{MIME_FOLDER}' "
        f"and name='{folder_name}' "
        f"and '{parent_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(
        q=query, fields="files(id, name)", spaces="drive",
    ).execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    meta = {"name": folder_name, "mimeType": MIME_FOLDER, "parents": [parent_id]}
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _upload_file(service, local_path, folder_id):
    from googleapiclient.http import MediaFileUpload
    file_name = os.path.basename(local_path)
    meta = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(local_path, mimetype=MIME_PDF, resumable=False)
    uploaded = service.files().create(
        body=meta, media_body=media, fields="id, webViewLink",
    ).execute()
    return uploaded.get("webViewLink", "")


# ── Public API ────────────────────────────────────────────────────────────────

def upload_documents(company, resume_path=None, cover_letter_path=None):
    """
    Upload resume and/or cover letter into <GDRIVE_FOLDER_ID>/{company}/
    Returns (resume_link, cover_letter_link) or (None, None) if not configured.
    """
    if not GDRIVE_FOLDER_ID:
        return None, None

    service = _build_service()
    if not service:
        return None, None

    try:
        safe_company = company.replace("/", "-").replace("\\", "-").strip()
        company_folder_id = _get_or_create_folder(service, safe_company, GDRIVE_FOLDER_ID)
        print(f"[Drive] Folder '{safe_company}' ready (id={company_folder_id})")

        resume_link, cl_link = None, None

        if resume_path and os.path.exists(resume_path):
            resume_link = _upload_file(service, resume_path, company_folder_id)
            print(f"[Drive] Resume uploaded: {resume_link}")

        if cover_letter_path and os.path.exists(cover_letter_path):
            cl_link = _upload_file(service, cover_letter_path, company_folder_id)
            print(f"[Drive] Cover letter uploaded: {cl_link}")

        return resume_link, cl_link

    except Exception as e:
        print(f"[Drive] Upload error: {e}")
        return None, None
