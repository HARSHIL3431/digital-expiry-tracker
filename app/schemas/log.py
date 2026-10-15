from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    description: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityLogListResponse(BaseModel):
    data: list[ActivityLogResponse]