from sqlalchemy.orm import Session

from app import models


def create_activity_log(
    db: Session,
    user_id: int,
    action: str,
    description: str | None = None,
    details: str | None = None,
) -> None:
    log_description = description if description is not None else details
    if log_description is None:
        log_description = action

    log = models.ActivityLog(
        user_id=user_id,
        action=action,
        description=log_description,
    )
    db.add(log)
