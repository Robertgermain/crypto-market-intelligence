from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(
        Integer,
        ForeignKey("assets.id"),
        nullable=False,
        index=True
    )

    decision = Column(
        String(20),
        nullable=False
    )  # BUY / SELL / HOLD

    confidence = Column(
        Integer,
        nullable=False
    )

    score = Column(
        Integer,
        nullable=False
    )

    decision_metadata = Column(
        JSON,
        nullable=True
    )  # store signals used + future inputs

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # -----------------------------
    # Relationships
    # -----------------------------
    signals = relationship(
        "MarketSignal",
        back_populates="decision",
        cascade="all, delete-orphan"
    )

    # Optional (nice to have for future)
    asset = relationship("Asset")

    # -----------------------------
    # Indexes
    # -----------------------------
    __table_args__ = (
        Index("idx_decision_asset_time", "asset_id", "created_at"),
    )