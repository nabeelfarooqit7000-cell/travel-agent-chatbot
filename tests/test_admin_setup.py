from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_admin_initialize_and_update_knowledge(tmp_path: Path, monkeypatch) -> None:
    knowledge_path = tmp_path / "knowledge_base.json"
    monkeypatch.setenv("ADMIN_SETUP_KEY", "test-secret")
    monkeypatch.setenv("KNOWLEDGE_JSON_PATH", str(knowledge_path))
    get_settings.cache_clear()

    client = TestClient(app)

    status_response = client.get("/api/admin/setup/status")
    assert status_response.status_code == 200
    assert status_response.json()["initialized"] is False

    initialize_response = client.post(
        "/api/admin/setup/initialize",
        headers={"X-Admin-Key": "test-secret"},
        json={"company_name": "Acme Travel", "admin_email": "admin@acme.test"},
    )
    assert initialize_response.status_code == 200
    assert initialize_response.json()["initialized"] is True

    update_response = client.post(
        "/api/admin/knowledge/update",
        headers={"X-Admin-Key": "test-secret"},
        json={
            "faqs": [{"topic": "baggage", "keywords": ["baggage"], "answer": "20kg checked baggage included."}],
            "terms_and_conditions": "Bookings follow airline and supplier conditions.",
            "refund_policy": "Refunds depend on fare conditions.",
            "exchange_charges": "Exchange fees plus fare difference apply.",
            "refund_charges": "Refund charges depend on fare rules.",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["policies"]["refund_policy"] == "Refunds depend on fare conditions."

    assert knowledge_path.exists()
    get_settings.cache_clear()
