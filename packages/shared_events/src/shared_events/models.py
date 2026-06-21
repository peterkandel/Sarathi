from datetime import datetime

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    aggregate_id: str
    payload: dict[str, object]
