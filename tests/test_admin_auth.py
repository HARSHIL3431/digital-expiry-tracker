"""
Tests for admin authorization on /api/v1/admin/run-expiry-check.
"""

from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str, password: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"name": "Admin Test", "email": email, "password": password},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


class TestAdminEndpointAuthorization:
    def test_unauthenticated_request_rejected(self, client):
        resp = client.post("/api/v1/admin/run-expiry-check")
        assert resp.status_code == 401

    def test_non_admin_user_rejected(self, client):
        token = _register_and_login(client, "regular@example.com", "pass123")
        resp = client.post(
            "/api/v1/admin/run-expiry-check",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_admin_user_accepted(self, client, monkeypatch):
        from app.api.v1 import admin as admin_routes

        called = {"count": 0}

        def fake_check():
            called["count"] += 1

        monkeypatch.setattr(admin_routes, "check_expiring_products", fake_check)

        token = _register_and_login(client, "admin@det.com", "pass123")
        resp = client.post(
            "/api/v1/admin/run-expiry-check",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "Expiry check executed successfully"}
        assert called["count"] == 1
