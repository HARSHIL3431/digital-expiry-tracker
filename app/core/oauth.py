from authlib.integrations.starlette_client import OAuth

from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


oauth = OAuth()


def _is_configured(value: str) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized != ""


if _is_configured(GOOGLE_CLIENT_ID) and _is_configured(GOOGLE_CLIENT_SECRET):
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        client_kwargs={"scope": "openid email profile"},
    )


def get_google_oauth_client():
    if not (_is_configured(GOOGLE_CLIENT_ID) and _is_configured(GOOGLE_CLIENT_SECRET)):
        return None
    return oauth.create_client("google")
