# JobGuardAI — Full-stack demonstration project

Includes responsive HTML/CSS/JavaScript frontend, Python Flask API, trained scikit-learn TF-IDF + Logistic Regression fraud classifier, TF-IDF/cosine similarity CV matching, SQLite persistence, tests, and editable UML.

## Windows: start
Extract ZIP. Open PowerShell in `JobGuardAI_Complete_Project` folder:
```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```
Then open http://127.0.0.1:5000

## macOS / Linux
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

The ML model trains automatically on the first scan using `data/jobs.csv`. After installation, the demo works offline.

## Demonstration
1. Click Suspicious example → Analyse job advert.
2. Click Normal example → Analyse job advert.
3. Show SQLite persistence in Recent scans.
4. Click CV Matching → Load example → Calculate similarity.
5. Enter an invalid short description to demonstrate validation.
6. Open http://127.0.0.1:5000/api/health
7. Run `pytest -q` and report actual test results.

## API
GET `/`; GET `/api/health`; POST `/api/analyze` with `{"title":"...","description":"..."}`; POST `/api/match` with `{"cv":"...","job":"..."}`; GET `/api/history`.

## Important academic honesty
This is a **standalone replacement demo** because the earlier source ZIP was unavailable. It uses Flask and SQLite, **not** the earlier Node/Express + FastAPI + PostgreSQL stack. It does not include Adzuna. Update your UML to reflect this implementation and disclose the change.

The classifier is genuinely trained, but the 32 training examples are **illustrative, manually written**, not a verified real-world dataset. Do not claim measured real-world accuracy. Model scores are not calibrated fraud probabilities. CV matching is NLP text similarity, not a second trained classifier.

Privacy/security: local-only server, input length checks, safe HTML escaping, no credentials. No login or role-based access controls; do not deploy publicly. Avoid pasting private CV information in a demonstration. Delete `jobguard.db` to clear saved scan history.

Assignment 5 also requires presentation slides, editable UML, accessible repository, testing evidence and an offline fallback. This ZIP is not a published repository.

## Safety-focused v2 changes
- Expanded transparent warning categories: fees, money, bank details, identity requests, urgency, guaranteed work, messaging-only contact, unrealistic income, secrecy and unsafe meetings.
- **Hybrid decision:** high-severity warning rules cannot be overruled by a low ML score. The ML percentage remains separate and is NOT a real-world fraud probability.
- Optional location field; no automatic address verification. `CAUTION_LOCATIONS` can contain semicolon-separated, privately supplied caution strings, e.g. `Example street 1;Example area 2`. A match displays a caution only, not an accusation or proof. Do not publish identifying watchlists.
- Do not travel alone to an unverified interview; verify the employer through independently found official contact details.
- No automatic model retraining from user submissions: malicious reports could poison training data. Curate, label, audit, then retrain offline.
- Existing Adzuna and CV features are preserved.
