from sqlalchemy.orm import Session

from app import models


def create_activity_log(
    db: Session,
    user_id: int,
    action: str,
    description: str,
) -> None:
    log = models.ActivityLog(
        user_id=user_id,
        action=action,
        description=description,
    )
    db.add(log)
