from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from app.main import app
from app.models import Subscription, User
from app.utils.database import SessionLocal


class FakeGoogleClient:
    def __init__(self, userinfo: dict):
        self._userinfo = userinfo

    async def authorize_redirect(self, request, redirect_uri):
        return RedirectResponse(url="https://accounts.google.com/o/oauth2/v2/auth?mock=1")

    async def authorize_access_token(self, request):
        return {"userinfo": self._userinfo}

    async def parse_id_token(self, request, token):
        return self._userinfo


def _extract_token_from_location(location: str) -> str:
    parsed = urlparse(location)
    query = parse_qs(parsed.query)
    token_values = query.get("token")
    assert token_values, "token query parameter missing"
    return token_values[0]


def test_frontend_google_login_contract_present():
    with open("frontend/pages/login.html", "r", encoding="utf-8") as html_file:
        login_html = html_file.read()

    with open("frontend/assets/js/auth.js", "r", encoding="utf-8") as js_file:
        auth_js = js_file.read()

    assert "Continue with Google" in login_html
    assert "auth-divider" in login_html
    assert "onclick=\"loginWithGoogle()\"" in login_html
    assert "function loginWithGoogle()" in auth_js
    assert 'window.location.href = "/api/v1/auth/google/login";' in auth_js


def test_google_oauth_callback_creates_user_and_redirects_with_jwt(monkeypatch):
    from app.api.v1 import auth as auth_routes

    email = f"google-{uuid4().hex[:10]}@example.com"
    fake_userinfo = {
        "email": email,
        "name": "Google OAuth User",
        "email_verified": True,
    }

    monkeypatch.setattr(auth_routes, "get_google_oauth_client", lambda: FakeGoogleClient(fake_userinfo))

    with TestClient(app) as client:
        login_response = client.get("/api/v1/auth/google/login", follow_redirects=False)
        assert login_response.status_code in (302, 307)
        assert "accounts.google.com" in login_response.headers.get("location", "")

        callback_response = client.get("/api/v1/auth/google/callback", follow_redirects=False)
        assert callback_response.status_code in (302, 307)

        redirect_location = callback_response.headers.get("location", "")
        assert redirect_location.startswith("/app/dashboard?token=")

        token = _extract_token_from_location(redirect_location)

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        payload = me_response.json()
        assert payload["email"] == email

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None

        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert subscription is not None
        assert subscription.plan_type == "free"
    finally:
        db.close()


def test_existing_email_password_login_still_works():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "123456"},
        )
        assert response.status_code == 200

        body = response.json()
        assert "access_token" in body
        assert body.get("token_type") == "bearer"

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "test@example.com"
