"""Reviewed-feedback workflow. Administrator-only labels, 20-example retraining gate."""
import csv
import hmac
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import ml_model

THRESHOLD = 20

def now():
    return datetime.now(timezone.utc).isoformat()

def setup(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS training_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        reported_label INTEGER NOT NULL CHECK(reported_label IN (0,1)),
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','used')),
        reviewed_at TEXT
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS model_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        approved_count INTEGER NOT NULL,
        old_f1 REAL NOT NULL,
        new_f1 REAL NOT NULL,
        new_precision REAL NOT NULL,
        new_recall REAL NOT NULL,
        status TEXT NOT NULL,
        note TEXT NOT NULL
    )""")

def authorized(req):
    expected = os.environ.get("JOBGUARD_ADMIN_TOKEN", "")
    supplied = req.headers.get("X-Admin-Token", "")
    return bool(expected and supplied and hmac.compare_digest(supplied, expected))

def metrics(model, holdout):
    x = [text for text, _ in holdout]
    y = [label for _, label in holdout]
    predicted = model.predict(x)
    return {
        "accuracy": round(float(accuracy_score(y, predicted)), 4),
        "precision": round(float(precision_score(y, predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(y, predicted, zero_division=0)), 4),
        "f1": round(float(f1_score(y, predicted, zero_division=0)), 4),
    }

def attempt_retrain(connection):
    """Call while holding SQLite BEGIN IMMEDIATE lock. A failed candidate remains approved."""
    approved = connection.execute(
        "SELECT id,title,description,reported_label FROM training_feedback WHERE status='approved' ORDER BY id"
    ).fetchall()
    if len(approved) < THRESHOLD:
        return {"triggered": False, "approved_since_last_update": len(approved)}
    base = ml_model.read_examples(ml_model.BASE / "data" / "jobs.csv")
    previously_used = connection.execute(
        "SELECT title,description,reported_label FROM training_feedback WHERE status='used'"
    ).fetchall()
    training = base + [(r["title"] + " " + r["description"], r["reported_label"]) for r in previously_used]
    candidate_data = training + [(r["title"] + " " + r["description"], r["reported_label"]) for r in approved]
    holdout = ml_model.read_examples(ml_model.BASE / "data" / "evaluation.csv")
    incumbent = ml_model.current_model()
    old = metrics(incumbent, holdout)
    candidate = ml_model.train(candidate_data)
    new = metrics(candidate, holdout)
    # Conservative gate; tiny illustrative holdout is NOT real-world proof of performance.
    accepted = (new["f1"] >= old["f1"] and new["recall"] >= old["recall"]
                and new["precision"] >= old["precision"] and new["f1"] >= 0.7)
    status = "activated" if accepted else "rejected"
    note = ("Candidate met illustrative evaluation gate."
            if accepted else "Candidate failed evaluation gate; incumbent retained.")
    if accepted:
        path = ml_model.MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".candidate-", suffix=".joblib", dir=str(path.parent))
        os.close(fd)
        try:
            joblib.dump(candidate, temp)
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        ml_model.refresh_model()
        connection.executemany(
            "UPDATE training_feedback SET status='used' WHERE id=?",
            [(r["id"],) for r in approved]
        )
    connection.execute(
        """INSERT INTO model_updates(created_at,approved_count,old_f1,new_f1,
           new_precision,new_recall,status,note) VALUES (?,?,?,?,?,?,?,?)""",
        (now(), len(approved), old["f1"], new["f1"], new["precision"],
         new["recall"], status, note)
    )
    return {"triggered": True, "status": status, "reviewed_examples": len(approved),
            "old_metrics": old, "candidate_metrics": new, "note": note}
