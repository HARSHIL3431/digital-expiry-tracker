from fastapi.testclient import TestClient

from app.main import app


def test_manual_expiry_check_endpoint_calls_service(monkeypatch):
    called = {"count": 0}

    def fake_check():
        called["count"] += 1

    from app.api.v1 import admin as admin_routes

    monkeypatch.setattr(admin_routes, "check_expiring_products", fake_check)

    with TestClient(app) as client:
        client.post(
            "/api/v1/auth/register",
            json={"name": "Admin", "email": "admin@det.com", "password": "pass123"},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@det.com", "password": "pass123"},
        )
        token = login.json()["access_token"]

        response = client.post(
            "/api/v1/admin/run-expiry-check",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "Expiry check executed successfully"}
    assert called["count"] == 1
