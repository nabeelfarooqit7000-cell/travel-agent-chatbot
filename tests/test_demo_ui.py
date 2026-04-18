from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_ui_route_renders() -> None:
    response = client.get("/demo")

    assert response.status_code == 200
    assert "Travel Agent Chatbot Demo" in response.text
    assert "/api/chat" in response.text
