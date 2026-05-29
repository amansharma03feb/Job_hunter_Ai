# Google Drive Setup Guide

One-time setup so the pipeline uploads resumes and cover letters to your
Google Drive as **your own Gmail account** (files count against your storage,
not a service account with zero quota).

---

## What you'll end up with

```
Aman- AI resumes/          ← your shared folder
  └── {Company Name}/
        ├── Aman_Sharma_Resume_...docx
        └── CoverLetter_...docx
```

---

## Step 1 — Enable the Drive API (if not already done)

1. Go to https://console.cloud.google.com/
2. Select your project: **job-hunter-ai-497720**
3. Go to **APIs & Services → Library** → search **Google Drive API** → Enable

---

## Step 2 — Create an OAuth Desktop Client

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. **Application type:** Desktop app
4. **Name:** `job-hunter-local`
5. Click **Create**
6. Click **Download JSON** on the popup
7. Rename the downloaded file to `oauth_client.json`
8. Move it into your project folder: `C:\Users\Dell\Documents\job-hunter-ai\`

> ⚠️ `oauth_client.json` is in `.gitignore` — it will never be committed.

---

## Step 3 — Run the one-time auth script

```bash
python gdrive_auth.py
```

- Your browser opens → sign in with **amansharma03feb@gmail.com**
- Allow Drive access
- The script prints three lines like:

```
GDRIVE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=GOCSPX-xxxxx
GDRIVE_REFRESH_TOKEN=1//0gxxxxxxxxxxxxxxx
```

---

## Step 4 — Add to .env and GitHub Secrets

**.env (local runs):**
```
GDRIVE_CLIENT_ID=<paste here>
GDRIVE_CLIENT_SECRET=<paste here>
GDRIVE_REFRESH_TOKEN=<paste here>
```

**GitHub Actions Secrets** (repo → Settings → Secrets → Actions):
- `GDRIVE_CLIENT_ID`
- `GDRIVE_CLIENT_SECRET`
- `GDRIVE_REFRESH_TOKEN`

---

## That's it!

Files will upload to your Drive on every outreach run.
The Excel log will have clickable Drive links for each file.
The `oauth_client.json` file stays local — never committed, never shared.
