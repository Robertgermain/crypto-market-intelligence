from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.schemas.market import PaginationMeta


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
    metadata: Optional[Dict[str, Any]]
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