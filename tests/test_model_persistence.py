from unittest.mock import patch

import joblib

import ml_model


def test_saved_model_loads_after_restart(tmp_path):
    model_path = tmp_path / "persistent_model.joblib"

    # Train a model using the project's example data.
    trained_model = ml_model.train()

    # Save it to a temporary location.
    joblib.dump(trained_model, model_path)

    assert model_path.exists()

    # Simulate a fresh process by clearing the cached model.
    with patch.object(ml_model, "MODEL_PATH", model_path):
        ml_model.refresh_model()

        try:
            with patch.object(
                ml_model,
                "train",
                side_effect=AssertionError(
                    "Model was retrained instead of loaded from disk"
                ),
            ):
                loaded_model = ml_model.current_model()

            prediction = loaded_model.predict_proba(
                ["Office administrator position with regular working hours"]
            )

            assert prediction.shape == (1, 2)

        finally:
            ml_model.refresh_model()