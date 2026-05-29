"""
One-time Google Drive OAuth2 setup.

Run this script ONCE to generate a refresh token that the pipeline uses
to upload files to your Google Drive as your own Gmail account.

Usage:
    python gdrive_auth.py

Prerequisites:
    1. Go to https://console.cloud.google.com/
    2. Your project (job-hunter-ai-497720) → APIs & Services → Credentials
    3. Click "+ Create Credentials" → OAuth client ID
    4. Application type: Desktop app  →  Name: job-hunter-local  →  Create
    5. Download the JSON → rename to oauth_client.json → place in this folder

The script will:
    - Open your browser for Google sign-in
    - Print GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN
    - You paste all three into your .env (and GitHub Actions secrets)
"""

import json, os, sys

CLIENT_FILE = "oauth_client.json"

if not os.path.exists(CLIENT_FILE):
    print(f"ERROR: {CLIENT_FILE} not found.")
    print("Download OAuth Desktop client JSON from Google Cloud Console and save it here.")
    sys.exit(1)

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Installing google-auth-oauthlib...")
    os.system("pip install google-auth-oauthlib --quiet")
    from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
creds = flow.run_local_server(port=0)

with open(CLIENT_FILE) as f:
    client_info = json.load(f).get("installed", {})

print("\n" + "=" * 60)
print("Add these three lines to your .env and GitHub Actions secrets:")
print("=" * 60)
print(f"GDRIVE_CLIENT_ID={client_info.get('client_id', '')}")
print(f"GDRIVE_CLIENT_SECRET={client_info.get('client_secret', '')}")
print(f"GDRIVE_REFRESH_TOKEN={creds.refresh_token}")
print("=" * 60)
