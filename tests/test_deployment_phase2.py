"""Focused deployment/CORS/configuration tests for Phase 2 preparation."""


from app.core.config import parse_cors_allowed_origins


def test_cors_parser_splits_trims_and_deduplicates():
    raw = " https://app.example.com/ , https://app.example.com , http://localhost:3000 "
    assert parse_cors_allowed_origins(raw, environment="production") == [
        "https://app.example.com",
        "http://localhost:3000",
    ]


def test_cors_parser_ignores_wildcard_with_credentials():
    origins = parse_cors_allowed_origins(
        "https://safe.example.com, * , https://other.example.com",
        environment="production",
    )
    assert "*" not in origins
    assert origins == ["https://safe.example.com", "https://other.example.com"]


def test_cors_parser_uses_dev_defaults_without_explicit_env(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.delenv("VERCEL_FRONTEND_URL", raising=False)

    origins = parse_cors_allowed_origins(environment="development")
    assert "http://localhost:8000" in origins
    assert "http://localhost:3000" in origins


def test_cors_parser_has_no_defaults_in_production_without_origin(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.delenv("VERCEL_FRONTEND_URL", raising=False)

    assert parse_cors_allowed_origins(environment="production") == []


def test_cors_preflight_works_for_configured_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_health_endpoint_remains_liveness_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_health_endpoint_remains_available(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_returns_ready_json(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["database"] == "ok"
    assert "upload_storage" in payload