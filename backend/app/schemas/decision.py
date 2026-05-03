from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

from app.schemas.market import PaginationMeta


# --------------------------------------------------
# METADATA SCHEMA
# --------------------------------------------------
class DecisionMetadata(BaseModel):
    signals: List[str] = Field(default_factory=list)
    signal_count: int = 0
    generated_at: Optional[str] = None
    explanation: Optional[str] = None


# --------------------------------------------------
# DECISION SCHEMA
# --------------------------------------------------
class DecisionData(BaseModel):
    id: int
    asset_id: int
    symbol: str
    decision: str
    confidence: int
    score: int
    metadata: DecisionMetadata
    created_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------
# RESPONSE WRAPPER
# --------------------------------------------------
class DecisionsResponse(BaseModel):
    status: str
    message: str
    data: List[DecisionData]
    pagination: PaginationMeta