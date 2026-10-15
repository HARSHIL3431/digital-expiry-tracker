from uuid import uuid4

from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from app.main import app
from app.models import Subscription, User
from app.utils.database import SessionLocal


class FakeGoogleClient:
    def __init__(self, userinfo: dict, fail_access_token: bool = False):
        self._userinfo = userinfo
        self._fail_access_token = fail_access_token

    async def authorize_redirect(self, request, redirect_uri):
        return RedirectResponse(url="https://accounts.google.com/o/oauth2/v2/auth?mock=1")

    async def authorize_access_token(self, request):
        if self._fail_access_token:
            from authlib.integrations.base_client.errors import OAuthError

            raise OAuthError("invalid_state")
        return {"userinfo": self._userinfo}

    async def parse_id_token(self, request, token):
        return self._userinfo


def _extract_token_from_session(client: TestClient) -> str:
    resp = client.get("/api/v1/auth/session-token")
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    assert token
    return token


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


def test_google_oauth_callback_creates_user_and_redirects_without_token(monkeypatch):
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
        assert redirect_location == "/app/dashboard" or redirect_location.endswith("/app/dashboard")
        assert "token=" not in redirect_location
        assert "access_token" not in redirect_location

        token = _extract_token_from_session(client)

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        payload = me_response.json()
        assert payload["email"] == email

        # The one-time session value cannot be reused.
        reuse_response = client.get("/api/v1/auth/session-token")
        assert reuse_response.status_code == 401

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None

        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert subscription is not None
        assert subscription.plan_type == "free"
    finally:
        db.close()


def test_google_oauth_invalid_state_returns_error(monkeypatch):
    from app.api.v1 import auth as auth_routes

    monkeypatch.setattr(
        auth_routes,
        "get_google_oauth_client",
        lambda: FakeGoogleClient({"email": "ignored@example.com", "email_verified": True}, fail_access_token=True),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/google/callback", follow_redirects=False)
        assert response.status_code == 400


def test_existing_email_password_login_still_works(client):
    from uuid import uuid4 as _uuid4

    email = f"login-{_uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": email, "password": password},
    )
    assert reg.status_code == 200, reg.text
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
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
    assert me_response.json()["email"] == email