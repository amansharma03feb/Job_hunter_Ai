"""
Google Drive Uploader — uploads tailored resume + cover letter into a
per-company subfolder inside the parent 'Aman- AI resumes' folder.

Folder structure created:
  Aman- AI resumes/           (parent, ID in GDRIVE_FOLDER_ID)
    └── {Company Name}/
          ├── Aman_Sharma_Resume_...docx
          └── CoverLetter_...docx

Authentication: Google Service Account JSON stored as a base64-encoded
string in the GDRIVE_SERVICE_ACCOUNT_JSON environment variable.

Returns shareable "view" links for each uploaded file.
Gracefully skips (returns None, None) if credentials are not configured.
"""

import base64
import json
import os

from config import GDRIVE_FOLDER_ID, GDRIVE_SERVICE_ACCOUNT_JSON

MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_FOLDER = "application/vnd.google-apps.folder"


# ── Build Drive service ───────────────────────────────────────────────────────

def _build_service():
    """
    Returns an authenticated Google Drive v3 service, or None if credentials
    are not configured or google-api-python-client is not installed.
    """
    if not GDRIVE_SERVICE_ACCOUNT_JSON:
        return None
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        # Decode base64 → JSON string → dict
        json_str = base64.b64decode(GDRIVE_SERVICE_ACCOUNT_JSON).decode("utf-8")
        sa_info = json.loads(json_str)

        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/drive"],
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
    """
    Return the Drive folder ID for `folder_name` inside `parent_id`.
    Creates it if it doesn't exist.
    """
    # Search for existing folder
    query = (
        f"mimeType='{MIME_FOLDER}' "
        f"and name='{folder_name}' "
        f"and '{parent_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        spaces="drive",
    ).execute()

    files = results.get("files", [])
    if files:
        return files[0]["id"]

    # Create folder
    meta = {
        "name": folder_name,
        "mimeType": MIME_FOLDER,
        "parents": [parent_id],
    }
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _upload_file(service, local_path, folder_id):
    """
    Upload a local DOCX file into `folder_id`.
    Returns the shareable 'view' link.
    """
    from googleapiclient.http import MediaFileUpload

    file_name = os.path.basename(local_path)
    meta = {
        "name": file_name,
        "parents": [folder_id],
    }
    media = MediaFileUpload(local_path, mimetype=MIME_DOCX, resumable=False)
    uploaded = service.files().create(
        body=meta,
        media_body=media,
        fields="id, webViewLink",
    ).execute()
    return uploaded.get("webViewLink", "")


# ── Public API ────────────────────────────────────────────────────────────────

def upload_documents(company, resume_path=None, cover_letter_path=None):
    """
    Upload resume and/or cover letter into:
      <GDRIVE_FOLDER_ID>/{company}/

    Parameters
    ----------
    company         : str  — company name used as subfolder name
    resume_path     : str  — local path to resume DOCX (or None)
    cover_letter_path: str — local path to cover letter DOCX (or None)

    Returns
    -------
    (resume_link, cover_letter_link)  — Drive view URLs, or (None, None) if
    Drive is not configured or upload fails.
    """
    if not GDRIVE_FOLDER_ID:
        return None, None

    service = _build_service()
    if not service:
        return None, None

    try:
        # Sanitise company name for Drive folder (Drive allows most chars but
        # strip slashes / backslashes that break paths)
        safe_company = company.replace("/", "-").replace("\\", "-").strip()

        # Ensure company subfolder exists
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
