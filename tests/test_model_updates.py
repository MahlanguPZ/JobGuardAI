import sqlite3
from pathlib import Path
from unittest.mock import patch

import retraining


def make_database(tmp_path):
    database = tmp_path / "test_feedback.db"
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    retraining.setup(connection)

    for i in range(20):
        connection.execute(
            """
            INSERT INTO training_feedback
            (created_at, title, description, reported_label, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                retraining.now(),
                f"Test job {i}",
                "Synthetic training example.",
                i % 2,
                "approved",
            ),
        )

    connection.commit()
    return connection


def test_rejected_model_keeps_approved_feedback(tmp_path):
    connection = make_database(tmp_path)

    with connection:
        with patch.object(retraining, "metrics") as mock_metrics:
            mock_metrics.side_effect = [
                {"f1": 0.9, "precision": 0.9, "recall": 0.9},
                {"f1": 0.5, "precision": 0.5, "recall": 0.5},
            ]

            result = retraining.attempt_retrain(connection)

    assert result["triggered"] is True
    assert result["status"] == "rejected"

    remaining = connection.execute(
        "SELECT COUNT(*) FROM training_feedback WHERE status='approved'"
    ).fetchone()[0]

    assert remaining == 20
    connection.close()


def test_accepted_model_marks_feedback_used(tmp_path):
    connection = make_database(tmp_path)

    with patch.object(retraining, "metrics") as mock_metrics:
        mock_metrics.side_effect = [
            {"f1": 0.7, "precision": 0.7, "recall": 0.7},
            {"f1": 0.9, "precision": 0.9, "recall": 0.9},
        ]

        with patch.object(retraining.ml_model, "MODEL_PATH", tmp_path / "test_model.joblib"):
            with connection:
                result = retraining.attempt_retrain(connection)

    assert result["triggered"] is True
    assert result["status"] == "activated"

    used = connection.execute(
        "SELECT COUNT(*) FROM training_feedback WHERE status='used'"
    ).fetchone()[0]

    assert used == 20
    assert (tmp_path / "test_model.joblib").exists()

    connection.close()