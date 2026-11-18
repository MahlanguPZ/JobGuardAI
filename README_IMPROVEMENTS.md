# JobGuardAI: controlled retraining upgrade

## Included
- Restored **illustrative**, synthetic `data/jobs.csv` (48 examples) and separate illustrative `data/evaluation.csv` (10 examples). Neither is a real-world verified benchmark.
- Feedback form and `POST /api/feedback`. User feedback is **pending**, never automatically trusted.
- Admin-only review endpoints using `JOBGUARD_ADMIN_TOKEN`.
- On approval of the **20th new reviewed example**, candidate model training starts in the request process.
- A candidate activates only if F1, recall and precision do not decline on the fixed evaluation set, and F1 >= 0.70. Otherwise the current model remains active.
- Successful activation marks approved examples `used`, and stores model with atomic replacement.
- Status and update history in SQLite.

## Run locally (PowerShell)
```powershell
cd "PATH_TO_YOUR_PROJECT"
python -m pip install -r requirements.txt
$env:JOBGUARD_ADMIN_TOKEN = "replace-with-a-long-random-secret"
python -m pytest -q
python app.py
```

## Submit feedback
Use the **Report an incorrect prediction** form after pasting an advert.
Consent is required. Feedback contains the advert title and description.

## Review feedback (PowerShell)
```powershell
$headers = @{"X-Admin-Token" = $env:JOBGUARD_ADMIN_TOKEN}
Invoke-RestMethod http://127.0.0.1:5000/api/admin/feedback -Headers $headers
$body = @{decision="approve"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/admin/feedback/1/review -Headers $headers -ContentType "application/json" -Body $body
Invoke-RestMethod http://127.0.0.1:5000/api/admin/model-status -Headers $headers
```
Replace `1` with an actual pending feedback ID. Use `decision="reject"` to reject.

## Render deployment: important
- Set `JOBGUARD_ADMIN_TOKEN` as a secret environment variable. Never put it in GitHub or frontend JS.
- **Persist both the database and model**. Set `JOBGUARD_DB=/var/data/jobguard.db` and `JOBGUARD_MODEL_PATH=/var/data/fraud_model.joblib` **only if** your Render service has a persistent disk mounted at `/var/data`. Otherwise do not claim feedback or models survive redeploys.
- If using an ephemeral free service, the feature can be demonstrated locally but is **not reliable in production**. Consider a managed database and persistent model storage before deployment.
- Keep admin endpoints private; protect token, use HTTPS, rate limiting, backup and a proper administrator identity system for production.
- Retraining runs synchronously when the 20th example is approved. This can delay that admin request; a production deployment should use a background worker.
- Never commit `jobguard.db`, feedback data, `.joblib` models or secret keys.

## Limitations
- Training and evaluation examples are synthetic and small; evaluation metrics **do not prove real-world fraud detection accuracy**.
- The feedback form accepts user claims, but only an admin can approve them. Human review should verify evidence independently.
- Approval records and model replacement are not a distributed transaction. Single-instance demo only; use a proper worker and transactional model registry for production.
- Existing location checks remain unverified demonstration records; employer verification is not added.
- CV matching remains TF-IDF text similarity, not a hiring prediction.


## Version 3 safety-rule correction
Fixed double-escaped regex word boundaries and whitespace tokens in `ml_model.py`. These prevented payment, banking, and unsafe meeting warnings from triggering. Run the full test suite before deploying.
