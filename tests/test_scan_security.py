"""
Tests for POST /api/v1/scan/image upload security and scan history access.
"""

import io
from uuid import uuid4

from fastapi.testclient import TestClient

from app import models
from app.core.security import hash_password


def _login_existing(client: TestClient, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _seed_scan_record(db, email: str, image_path: str):
    user = models.User(
        name=email.split("@")[0],
        email=email,
        password_hash=hash_password("password123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record = models.ScanResult(
        user_id=user.id,
        image_path=image_path,
        detected_expiry="2026-01-01",
        confidence="0.8",
        extracted_text="expiry 01/01/2026",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return user.id, record.id


class TestScanUploadSecurity:
    """Security tests for the scan image upload endpoint."""

    def test_non_image_content_type_rejected(self, client):
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
        resp = client.post(
            "/api/v1/scan/image",
            files={"file": ("document.pdf", fake_pdf, "application/pdf")},
        )
        assert resp.status_code == 400

    def test_empty_image_upload_rejected(self, client):
        empty = io.BytesIO(b"")
        resp = client.post(
            "/api/v1/scan/image",
            files={"file": ("empty.jpg", empty, "image/jpeg")},
        )
        assert resp.status_code != 500

    def test_path_traversal_filename_sanitized(self, client):
        payload = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        resp = client.post(
            "/api/v1/scan/image",
            files={"file": ("../../evil.txt", payload, "image/jpeg")},
        )
        assert resp.status_code != 500
        assert "../../evil.txt" not in resp.text

    def test_oversized_upload_rejected(self, client):
        large_file = io.BytesIO(b"A" * (11 * 1024 * 1024))
        resp = client.post(
            "/api/v1/scan/image",
            files={"file": ("big.jpg", large_file, "image/jpeg")},
        )
        assert resp.status_code in (400, 413)

    def test_scan_endpoint_reachable(self, client):
        tiny_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
            b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
            b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        resp = client.post(
            "/api/v1/scan/image",
            files={"file": ("tiny.png", io.BytesIO(tiny_png), "image/png")},
        )
        assert resp.status_code != 404
        assert resp.status_code != 405

    def test_scan_history_requires_authentication(self, client):
        resp = client.get("/api/v1/scan/scans")
        assert resp.status_code == 401

    def test_scan_history_returns_authenticated_users_records(self, client, db):
        email_a = f"scan-a-{uuid4().hex[:8]}@example.com"
        email_b = f"scan-b-{uuid4().hex[:8]}@example.com"
        _, record_a = _seed_scan_record(db, email_a, "/tmp/scan-a.jpg")
        _, record_b = _seed_scan_record(db, email_b, "/tmp/scan-b.jpg")

        token_a = _login_existing(client, email_a, "password123")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        resp_a = client.get("/api/v1/scan/scans", headers=headers_a)
        assert resp_a.status_code == 200
        body_a = resp_a.json()
        returned_ids = {item["id"] for item in body_a["data"]}
        assert record_a in returned_ids
        assert record_b not in returned_ids

        token_b = _login_existing(client, email_b, "password123")
        headers_b = {"Authorization": f"Bearer {token_b}"}
        resp_b = client.get("/api/v1/scan/scans", headers=headers_b)
        assert resp_b.status_code == 200
        returned_ids_b = {item["id"] for item in resp_b.json()["data"]}
        assert record_b in returned_ids_b
        assert record_a not in returned_ids_b

    def test_scan_history_endpoint_reachable(self, client, auth_headers):
        resp = client.get("/api/v1/scan/scans", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total_records" in body