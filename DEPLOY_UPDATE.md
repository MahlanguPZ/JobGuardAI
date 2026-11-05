# JobGuardAI update: Adzuna + CV uploads

## What changed
- `/api/jobs?title=developer&location=Pretoria`: fetches live Adzuna South Africa listings (country code `za`).
- Search results include a **Check fraud risk** button to copy the listing into the existing ML scanner, and a **Match my CV** button.
- `/api/match-file`: accepts PDF and DOCX CV uploads up to 5 MB and compares extracted text with job requirements.
- Legacy `.doc` is **not** supported: convert it to `.docx` in Microsoft Word or LibreOffice first.
- Encrypted/scanned-image PDFs without selectable text are not supported; no OCR.
- Uploaded CVs are processed in memory, not stored in SQLite.
- Model fraud scores remain illustrative and must not be described as verified fraud probabilities.

## Set Adzuna credentials on Render
Render dashboard → JobGuardAI web service → Environment → Add Environment Variable:
`ADZUNA_APP_ID` = your Adzuna application ID
`ADZUNA_APP_KEY` = your Adzuna application key
Save and redeploy. **Never commit these values to GitHub.**

## Deploy
Replace your existing project files with the contents of this update (keep your `.git` directory).
Then run:
```
git add .
git commit -m "Add Adzuna search and PDF DOCX CV uploads"
git push
```
Render should redeploy automatically when connected to GitHub.
Check Render logs for build errors. Start command: `gunicorn app:app`.
If Adzuna search fails with HTTP 401/403, verify your credentials and Adzuna access.
The Adzuna API must be reachable from Render.

## Run locally
```
pip install -r requirements.txt
```
Set environment variables in your terminal, then `python app.py`.
Tests: `pytest -q`.
