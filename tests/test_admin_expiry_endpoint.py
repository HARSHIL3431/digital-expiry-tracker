from fastapi.testclient import TestClient

from app.main import app

# Clearly non-secret placeholder credentials. Do not replace these with data
# drawn from production environment variables or real operator accounts.
TEST_ADMIN_EMAIL = "ci-pipeline-admin@expiry-tracker.invalid"
TEST_ADMIN_PASSWORD = "unit-test-password-only"


def test_manual_expiry_check_endpoint_calls_service(monkeypatch):
    called = {"count": 0}

    def fake_check():
        called["count"] += 1

    from app.api.v1 import admin as admin_routes

    # The endpoint's admin check is authorization logic; exercising that path
    # through a hardcoded production email or live ADMIN_EMAIL setting is out of
    # scope for this unit test. Grant authorization deterministically here.
    monkeypatch.setattr(admin_routes, "is_admin", lambda _email: True)
    monkeypatch.setattr(admin_routes, "check_expiring_products", fake_check)

    with TestClient(app) as client:
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "CI Pipeline Test Admin",
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD,
            },
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
        )
        token = login.json()["access_token"]

        response = client.post(
            "/api/v1/admin/run-expiry-check",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "Expiry check executed successfully"}
    assert called["count"] == 1
