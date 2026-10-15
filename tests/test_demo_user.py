from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
from app.models import User
from app.utils.database import Base


def _test_session(tmp_path, name):
    engine = create_engine(f"sqlite:///{tmp_path / name}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_demo_user_disabled_in_production(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "ENABLE_DEMO_USER", False)

    db = _test_session(tmp_path, "disabled.db")
    try:
        assert main.ensure_demo_user(db) is False
        assert db.query(User).filter(User.email == "test@example.com").count() == 0
    finally:
        db.close()


def test_demo_user_disabled_when_explicitly_disabled(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "ENABLE_DEMO_USER", False)

    db = _test_session(tmp_path, "disabled2.db")
    try:
        main.ensure_demo_user(db)
        assert db.query(User).filter(User.email == "test@example.com").count() == 0
    finally:
        db.close()


def test_demo_user_enabled_in_development(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "ENABLE_DEMO_USER", True)
    monkeypatch.setattr(main, "DEMO_USER_PASSWORD", "test-only-demo-pass")

    db = _test_session(tmp_path, "enabled.db")
    try:
        assert main.ensure_demo_user(db) is True
        user = db.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.password_hash and "test-only-demo-pass" not in str(user.password_hash)
    finally:
        db.close()


def test_demo_user_skipped_when_password_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "ENABLE_DEMO_USER", True)
    monkeypatch.setattr(main, "DEMO_USER_PASSWORD", "")

    db = _test_session(tmp_path, "nopass.db")
    try:
        assert main.ensure_demo_user(db) is False
        assert db.query(User).filter(User.email == "test@example.com").count() == 0
    finally:
        db.close()


def test_demo_user_does_not_recreate_existing_user(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "ENABLE_DEMO_USER", True)
    monkeypatch.setattr(main, "DEMO_USER_PASSWORD", "test-only-demo-pass")

    db = _test_session(tmp_path, "idempotent.db")
    try:
        assert main.ensure_demo_user(db) is True
        assert main.ensure_demo_user(db) is False
    finally:
        db.close()