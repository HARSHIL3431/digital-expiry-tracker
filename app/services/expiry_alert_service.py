from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import joinedload

from app.core.config import (
    EMAIL_PASSWORD,
    EMAIL_USER,
    ENABLE_EXPIRY_ALERT_SCHEDULER,
    EXPIRY_ALERT_INTERVAL_HOURS,
    EXPIRY_ALERT_WINDOW_DAYS,
)
from app.models import Product
from app.utils.database import SessionLocal


_scheduler: BackgroundScheduler | None = None


def send_email(to_email: str, subject: str, message: str) -> bool:
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("[EMAIL ALERT] Skipped: EMAIL_USER/EMAIL_PASSWORD are not configured.")
        return False

    if not to_email or "@" not in to_email:
        print(f"[EMAIL ALERT] Skipped: invalid recipient '{to_email}'.")
        return False

    mime = MIMEMultipart()
    mime["From"] = EMAIL_USER
    mime["To"] = to_email
    mime["Subject"] = subject
    mime.attach(MIMEText(message, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_USER, [to_email], mime.as_string())
        return True
    except Exception as error:
        print(f"[ERROR] Failed to send email: {error}")
        return False


def check_expiring_products() -> None:
    today = date.today()
    db = SessionLocal()
    print("[ALERT] Checking expiring products...")

    try:
        products = (
            db.query(Product)
            .options(joinedload(Product.owner))
            .filter(Product.alert_sent.is_(False))
            .all()
        )

        has_updates = False

        for product in products:
            if product.expiry_date is None:
                continue

            days_left = (product.expiry_date - today).days
            if days_left < 0 or days_left > EXPIRY_ALERT_WINDOW_DAYS:
                continue

            owner_email = product.owner.email if product.owner else ""
            subject = "⚠️ Expiry Alert - Product Expiring Soon"
            message = (
                f"Hello,\n\n"
                f"Your product \"{product.product_name}\" is expiring on {product.expiry_date}.\n\n"
                f"Please take necessary action.\n\n"
                f"Regards,\n"
                f"Digital Expiry Tracker"
            )

            try:
                if send_email(owner_email, subject, message):
                    product.alert_sent = True
                    has_updates = True
                    print(f"[EMAIL SENT] {owner_email} - {product.product_name}")
            except Exception as error:
                # Keep scheduler resilient per-item so one bad email does not stop the batch.
                print(f"[ERROR] Failed to send email: {error}")

        if has_updates:
            db.commit()
    except Exception as error:
        db.rollback()
        print(f"[EMAIL ALERT] Expiry check failed: {error}")
    finally:
        db.close()


def start_expiry_alert_scheduler() -> None:
    global _scheduler

    if not ENABLE_EXPIRY_ALERT_SCHEDULER:
        print("[EMAIL ALERT] Scheduler disabled by configuration.")
        return

    if _scheduler is None:
        _scheduler = BackgroundScheduler(daemon=True)

    if _scheduler.get_job("expiry-alert-job") is None:
        _scheduler.add_job(
            check_expiring_products,
            trigger=IntervalTrigger(hours=EXPIRY_ALERT_INTERVAL_HOURS),
            id="expiry-alert-job",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    if not _scheduler.running:
        _scheduler.start()


def stop_expiry_alert_scheduler() -> None:
    global _scheduler

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
