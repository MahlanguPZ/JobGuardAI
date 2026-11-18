import os
import tempfile
from pathlib import Path

def test_feedback_and_admin_review():
    with tempfile.TemporaryDirectory() as temp:
        os.environ["JOBGUARD_DB"] = str(Path(temp) / "feedback.db")
        os.environ["JOBGUARD_MODEL_PATH"] = str(Path(temp) / "model.joblib")
        os.environ["JOBGUARD_ADMIN_TOKEN"] = "test-secret"
        import importlib
        import app as module
        module.DB = Path(os.environ["JOBGUARD_DB"])
        with module.db() as c:
            module.retraining.setup(c)
        client = module.app.test_client()
        body = {"title": "Example role", "description": "Example advertisement description long enough to submit.",
                "reported_label": 1, "consent": True}
        submitted = client.post("/api/feedback", json=body)
        assert submitted.status_code == 201
        item_id = submitted.json["id"]
        assert client.get("/api/admin/feedback").status_code == 401
        headers = {"X-Admin-Token": "test-secret"}
        pending = client.get("/api/admin/feedback", headers=headers)
        assert pending.status_code == 200
        assert len(pending.json["pending"]) == 1
        reviewed = client.post(f"/api/admin/feedback/{item_id}/review",
                               json={"decision": "approve"}, headers=headers)
        assert reviewed.status_code == 200
        assert reviewed.json["model_update"]["approved_since_last_update"] == 1
        assert reviewed.json["model_update"]["triggered"] is False
        assert client.post(f"/api/admin/feedback/{item_id}/review",
                           json={"decision": "approve"}, headers=headers).status_code == 404
        assert client.post("/api/feedback", json={**body, "consent": False}).status_code == 400
