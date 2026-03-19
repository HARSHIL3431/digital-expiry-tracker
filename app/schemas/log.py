from pydantic import BaseModel
from datetime import datetime


class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    description: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ActivityLogListResponse(BaseModel):
    data: list[ActivityLogResponse]