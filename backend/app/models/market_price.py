from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Index

from app.core.database import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)

    price_usd = Column(Numeric(18, 8), nullable=False)
    volume_24h = Column(Numeric(24, 8), nullable=True)
    market_cap = Column(Numeric(24, 2), nullable=True)

    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship (useful later)
    asset = relationship("Asset")

    __table_args__ = (
        Index("idx_asset_time", "asset_id", "observed_at"),
    )