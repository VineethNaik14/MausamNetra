import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.source import SourceType


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: SourceType
    reliability_score: float
    is_active: bool
    created_at: datetime