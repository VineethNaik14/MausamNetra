import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DuplicateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID
    master_report_id: uuid.UUID
    similarity_score: float
    created_at: datetime
