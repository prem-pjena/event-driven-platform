from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from uuid import UUID


class EventEnvelope(BaseModel):
    """
    Global event envelope used across the platform.

    This MUST remain backward compatible.
    """
    event_id: UUID
    event_type: str
    aggregate_id: UUID
    version: int
    occurred_at: datetime
    payload: Dict[str, Any]
