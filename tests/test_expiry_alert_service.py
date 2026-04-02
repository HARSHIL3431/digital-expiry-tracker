from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.services import expiry_alert_service
from app.utils.database import Base


def _build_test_session(tmp_path):
    db_path = tmp_path / "expiry_alert_test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestSessionLocal


def test_check_expiring_products_no_products(tmp_path, monkeypatch):
    test_session = _build_test_session(tmp_path)

    monkeypatch.setattr(expiry_alert_service, "SessionLocal", test_session)
    monkeypatch.setattr(expiry_alert_service, "EXPIRY_ALERT_WINDOW_DAYS", 2, raising=False)

    sent_emails = []

    def fake_send_email(to_email, subject, message):
        sent_emails.append((to_email, subject, message))
        return True

    monkeypatch.setattr(expiry_alert_service, "send_email", fake_send_email)

    expiry_alert_service.check_expiring_products()

    assert sent_emails == []


def test_check_expiring_products_sends_once_and_sets_flag(tmp_path, monkeypatch):
    test_session = _build_test_session(tmp_path)

    db = test_session()
    user = models.User(name="U", email="u@example.com", password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)

    product = models.Product(
        product_name="Milk",
        category="Dairy",
        quantity=1,
        manufacture_date=date.today(),
        expiry_date=date.today() + timedelta(days=1),
        price=100.0,
        user_id=user.id,
        alert_sent=False,
    )
    db.add(product)
    db.commit()
    product_id = product.id
    db.close()

    monkeypatch.setattr(expiry_alert_service, "SessionLocal", test_session)
    monkeypatch.setattr(expiry_alert_service, "EXPIRY_ALERT_WINDOW_DAYS", 2, raising=False)

    call_count = {"count": 0}

    def fake_send_email(to_email, subject, message):
        call_count["count"] += 1
        return True

    monkeypatch.setattr(expiry_alert_service, "send_email", fake_send_email)

    expiry_alert_service.check_expiring_products()
    expiry_alert_service.check_expiring_products()

    verify_db = test_session()
    saved_product = verify_db.query(models.Product).filter(models.Product.id == product_id).first()

    assert call_count["count"] == 1
    assert saved_product is not None
    assert saved_product.alert_sent is True

    verify_db.close()


def test_check_expiring_products_handles_send_failure(tmp_path, monkeypatch):
    test_session = _build_test_session(tmp_path)

    db = test_session()
    user = models.User(name="Bad Email", email="invalid-email", password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)

    product = models.Product(
        product_name="Bread",
        category="Bakery",
        quantity=1,
        manufacture_date=date.today(),
        expiry_date=date.today() + timedelta(days=1),
        price=50.0,
        user_id=user.id,
        alert_sent=False,
    )
    db.add(product)
    db.commit()
    product_id = product.id
    db.close()

    monkeypatch.setattr(expiry_alert_service, "SessionLocal", test_session)
    monkeypatch.setattr(expiry_alert_service, "EXPIRY_ALERT_WINDOW_DAYS", 2, raising=False)

    def fake_send_email(to_email, subject, message):
        raise ValueError("Invalid recipient")

    monkeypatch.setattr(expiry_alert_service, "send_email", fake_send_email)

    expiry_alert_service.check_expiring_products()

    verify_db = test_session()
    saved_product = verify_db.query(models.Product).filter(models.Product.id == product_id).first()

    assert saved_product is not None
    assert saved_product.alert_sent is False

    verify_db.close()
