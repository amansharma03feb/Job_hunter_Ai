# Google Drive Setup Guide

One-time setup to allow the AI Job Hunter pipeline to upload resumes and cover letters
into your shared Drive folder automatically.

---

## What you'll end up with

Each time the pipeline runs outreach for a BEST FIT job, it will create:

```
Aman- AI resumes/          ← your shared folder
  └── {Company Name}/
        ├── Aman_Sharma_Resume_...docx
        └── CoverLetter_...docx
```

---

## Step 1 — Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click **Select a project → New Project**
3. Name it `job-hunter-ai` (or anything you like)
4. Click **Create**

---

## Step 2 — Enable the Google Drive API

1. In your project, go to **APIs & Services → Library**
2. Search for **Google Drive API**
3. Click **Enable**

---

## Step 3 — Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → Service Account**
3. Name: `job-hunter-uploader`
4. Click **Create and Continue** (no special roles needed)
5. Click **Done**

---

## Step 4 — Download the JSON Key

1. On the Credentials page, click the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key → Create new key → JSON**
4. Save the downloaded `.json` file somewhere safe (e.g., `service_account.json`)

> ⚠️ **Never commit this file to Git.** It is already in `.gitignore`.

---

## Step 5 — Share your Drive folder with the service account

1. Open https://drive.google.com/drive/u/0/folders/1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp
2. Click the **⋮ menu → Share**
3. In the "Add people" box, paste the service account **email** from the JSON file
   (looks like `job-hunter-uploader@your-project.iam.gserviceaccount.com`)
4. Set permission to **Editor**
5. Click **Share**

---

## Step 6 — Encode the JSON key as base64

**On Linux/Mac:**
```bash
base64 -w 0 service_account.json
```

**On Windows (PowerShell):**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("service_account.json"))
```

Copy the entire output (one long string — no line breaks).

---

## Step 7 — Add to your .env / GitHub Secrets

**.env (local runs):**
```
GDRIVE_SERVICE_ACCOUNT_JSON=<paste base64 string here>
GDRIVE_FOLDER_ID=1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp
```

**GitHub Actions Secrets (for automated runs):**
- Go to your repo → Settings → Secrets and variables → Actions
- Add `GDRIVE_SERVICE_ACCOUNT_JSON` with the base64 string
- `GDRIVE_FOLDER_ID` is already hard-coded as the default in `config.py`

---

## That's it!

On the next pipeline run, documents will appear in your Drive folder automatically.
The Excel log will include clickable Drive links for each uploaded file.
