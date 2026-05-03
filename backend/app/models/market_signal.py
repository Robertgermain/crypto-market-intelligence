from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class MarketSignal(Base):
    __tablename__ = "market_signals"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(
        Integer,
        ForeignKey("assets.id"),
        nullable=False,
        index=True
    )

    decision_id = Column(
        Integer,
        ForeignKey("decisions.id"),
        nullable=True,
        index=True
    )

    signal_type = Column(
        String(50),
        nullable=False,
        index=True
    )

    strength = Column(
        Numeric(10, 4),
        nullable=False
    )

    signal_metadata = Column(
        JSONB,
        nullable=True
    )

    detected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # -----------------------------
    # Relationships
    # -----------------------------
    asset = relationship("Asset")

    decision = relationship(
        "Decision",
        back_populates="signals",
        foreign_keys=[decision_id],
    )

    # -----------------------------
    # Indexes
    # -----------------------------
    __table_args__ = (
        Index("idx_signal_asset_time", "asset_id", "detected_at"),
        Index("idx_signal_decision", "decision_id"),
    )