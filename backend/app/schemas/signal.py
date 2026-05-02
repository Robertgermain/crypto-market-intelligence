from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class SignalResponse(BaseModel):
    id: int
    asset_id: int
    signal_type: str
    strength: float
    signal_metadata: Optional[Dict[str, Any]]
    detected_at: datetime

    class Config:
        from_attributes = True