from fastapi.testclient import TestClient

from app.main import app


def test_manual_expiry_check_endpoint_calls_service(monkeypatch):
    called = {"count": 0}

    def fake_check():
        called["count"] += 1

    from app.api.v1 import admin as admin_routes

    monkeypatch.setattr(admin_routes, "check_expiring_products", fake_check)

    with TestClient(app) as client:
        response = client.post("/api/v1/admin/run-expiry-check")

    assert response.status_code == 200
    assert response.json() == {"status": "Expiry check executed successfully"}
    assert called["count"] == 1
