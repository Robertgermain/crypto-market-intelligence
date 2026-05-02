from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# --------------------------------------------------
# PRICE SCHEMA
# --------------------------------------------------
class MarketPriceResponse(BaseModel):
    id: int
    asset_id: int
    price_usd: float
    observed_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy compatibility


# --------------------------------------------------
# SIGNAL SCHEMA
# --------------------------------------------------
class MarketSignalResponse(BaseModel):
    id: int
    asset_id: int
    signal_type: str
    strength: float
    metadata: Optional[dict]
    detected_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------
# PAGINATION WRAPPER
# --------------------------------------------------
class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int
    returned: int


# --------------------------------------------------
# GENERIC RESPONSE WRAPPERS
# --------------------------------------------------
class PricesResponse(BaseModel):
    status: str
    message: str
    data: List[MarketPriceResponse]
    pagination: PaginationMeta


class SignalsResponse(BaseModel):
    status: str
    message: str
    data: List[MarketSignalResponse]
    pagination: PaginationMeta