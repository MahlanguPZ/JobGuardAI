import sqlite3
from unittest.mock import patch

import retraining


def test_retraining_starts_at_20_approvals(tmp_path):
    database = tmp_path / "retraining_test.db"

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        retraining.setup(connection)

        for i in range(19):
            connection.execute(
                """
                INSERT INTO training_feedback
                (created_at, title, description, reported_label, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    retraining.now(),
                    f"Test job {i}",
                    "Synthetic advertisement for testing.",
                    i % 2,
                    "approved",
                ),
            )

        result = retraining.attempt_retrain(connection)
        assert result["triggered"] is False
        assert result["approved_since_last_update"] == 19

        connection.execute(
            """
            INSERT INTO training_feedback
            (created_at, title, description, reported_label, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                retraining.now(),
                "Test job 20",
                "Synthetic advertisement for testing.",
                1,
                "approved",
            ),
        )

        with patch.object(retraining.ml_model, "train") as mock_train:
            mock_train.side_effect = RuntimeError("Training reached (test only)")

            try:
                retraining.attempt_retrain(connection)
            except RuntimeError as error:
                assert str(error) == "Training reached (test only)"
            else:
                raise AssertionError("Retraining did not start at 20 approvals")

            mock_train.assert_called_once()
