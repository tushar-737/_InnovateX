"""End-to-end smoke tests for the API (no LLM key needed — rules engine)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def _session() -> str:
    r = client.post("/api/session", json={"consent_given": True, "locale": "hi-IN"})
    assert r.status_code == 200
    return r.json()["session_id"]


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_conversation_flow_and_recommend():
    sid = _session()
    answers = [
        "mera naam rahul hai",
        "28 saal",
        "gonda se hoon",
        "10th tak padha",
        "ghar mein kheti hoti hai",
        "abhi mazdoori karta hoon",
        "silai aati hai",
        "kapdo mein ruchi hai",
        "koi dikkat nahi",
        "apna kaam karna hai",
        "haan ja sakta hoon",
    ]
    for text in answers:
        r = client.post("/api/conversation/turn", json={"session_id": sid, "user_text": text})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["reply_text"]
        assert isinstance(body["missing_fields"], list)

    r = client.post("/api/conversation/turn", json={"session_id": sid, "user_text": "theek hai"})
    assert r.status_code == 200

    r = client.post("/api/conversation/confirm", json={"session_id": sid, "user_text": "haan sahi hai"})
    assert r.status_code == 200
    conf = r.json()
    assert conf["is_confirmed"] is True
    assert "आपने बताया" in conf["readback_text"]
    assert conf["profile"]["age"] == 28

    r = client.post("/api/recommend", json={"profile": conf["profile"]})
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    assert len(recs) == 3
    assert all(0 <= rec["score"] <= 100 for rec in recs)


def test_delete_my_data():
    sid = _session()
    client.post("/api/conversation/turn", json={"session_id": sid, "user_text": "25 saal"})
    r = client.delete(f"/api/session/{sid}")
    assert r.status_code == 200
    assert r.json()["deleted"] is True
    r = client.get(f"/api/session/{sid}")
    assert r.status_code == 404
