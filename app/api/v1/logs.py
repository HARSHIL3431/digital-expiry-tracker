from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.core.dependencies import get_current_user
from app.schemas.log import ActivityLogListResponse
from app.utils.database import get_db


router = APIRouter(tags=["Logs"])


@router.get("", response_model=ActivityLogListResponse)
def get_logs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    records = (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.user_id == current_user.id)
        .order_by(models.ActivityLog.timestamp.desc())
        .limit(limit)
        .all()
    )

    return {"data": records}
