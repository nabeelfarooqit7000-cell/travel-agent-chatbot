from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.knowledge_store import KnowledgeStore

_LEAD_BODY = {
    "trip": {
        "origin": "JFK",
        "destination": "JED",
        "departure_date": "2026-06-14",
        "adults": 2,
        "currency": "USD",
    },
    "fare": {
        "rank": 1,
        "total_price": 499.0,
        "currency": "USD",
        "raw_offer_id": "offer-1",
    },
    "source": "test",
}


def test_booking_lead_config_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("KNOWLEDGE_JSON_PATH", str(tmp_path / "nonexistent-knowledge.json"))
    monkeypatch.delenv("BOOKING_LEAD_URL", raising=False)
    get_settings.cache_clear()

    client = TestClient(app)
    response = client.get("/api/public/booking-lead-config")
    assert response.status_code == 200
    assert response.json()["lead_delivery_enabled"] is False
    get_settings.cache_clear()


def test_create_lead_503_when_not_configured(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("KNOWLEDGE_JSON_PATH", str(tmp_path / "k.json"))
    monkeypatch.delenv("BOOKING_LEAD_URL", raising=False)
    get_settings.cache_clear()
    KnowledgeStore().save(
        {
            "initialized": True,
            "company": {"name": "T", "admin_email": ""},
            "faqs": [],
            "policies": {
                "terms_and_conditions": "x",
                "refund_policy": "x",
                "exchange_charges": "x",
                "refund_charges": "x",
            },
            "integrations": {"booking_lead_url": ""},
        }
    )

    client = TestClient(app)
    response = client.post("/api/leads", json=_LEAD_BODY)
    assert response.status_code == 503
    get_settings.cache_clear()


def test_create_lead_forwards_with_env_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOKING_LEAD_URL", "https://example.com/hooks/leads")
    get_settings.cache_clear()
    client = TestClient(app)

    with patch("app.api.routes.forward_booking_lead", new=AsyncMock(return_value=201)) as mocked:
        response = client.post("/api/leads", json=_LEAD_BODY)
    assert response.status_code == 200
    assert response.json()["downstream_status_code"] == 201
    mocked.assert_awaited_once()
    get_settings.cache_clear()


def test_create_lead_uses_knowledge_url(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "k.json"
    monkeypatch.setenv("KNOWLEDGE_JSON_PATH", str(path))
    monkeypatch.delenv("BOOKING_LEAD_URL", raising=False)
    get_settings.cache_clear()
    store = KnowledgeStore()
    store.save(
        {
            "initialized": True,
            "company": {"name": "T", "admin_email": ""},
            "faqs": [],
            "policies": {
                "terms_and_conditions": "terms " * 2,
                "refund_policy": "ref " * 2,
                "exchange_charges": "ex " * 2,
                "refund_charges": "rch " * 2,
            },
            "integrations": {"booking_lead_url": "https://site.test/api/inbox"},
        }
    )

    client = TestClient(app)
    with patch("app.api.routes.forward_booking_lead", new=AsyncMock(return_value=200)):
        response = client.post("/api/leads", json=_LEAD_BODY)
    assert response.status_code == 200
    assert client.get("/api/public/booking-lead-config").json()["lead_delivery_enabled"] is True
    get_settings.cache_clear()


def test_admin_saves_booking_lead_url(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    knowledge_path = tmp_path / "kb.json"
    monkeypatch.setenv("ADMIN_SETUP_KEY", "k")
    monkeypatch.setenv("KNOWLEDGE_JSON_PATH", str(knowledge_path))
    get_settings.cache_clear()
    client = TestClient(app)
    client.post(
        "/api/admin/setup/initialize",
        headers={"X-Admin-Key": "k"},
        json={"company_name": "Co", "admin_email": None},
    )
    response = client.post(
        "/api/admin/knowledge/update",
        headers={"X-Admin-Key": "k"},
        json={
            "faqs": [],
            "terms_and_conditions": "Bookings follow conditions.",
            "refund_policy": "Refunds depend on fare conditions.",
            "exchange_charges": "Exchange fees plus fare difference apply.",
            "refund_charges": "Refund charges depend on fare rules.",
            "booking_lead_url": "https://cms.example.com/api/booking-leads",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["integrations"]["booking_lead_url"] == "https://cms.example.com/api/booking-leads"

    get_response = client.get("/api/admin/knowledge", headers={"X-Admin-Key": "k"})
    assert get_response.json()["integrations"]["booking_lead_url"] == "https://cms.example.com/api/booking-leads"
    get_settings.cache_clear()
