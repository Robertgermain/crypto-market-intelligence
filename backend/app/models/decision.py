from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)

    decision = Column(String(20), nullable=False)  # BUY / SELL / HOLD
    confidence = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)

    decision_metadata = Column(JSON, nullable=True)  # store signals used

    created_at = Column(DateTime(timezone=True), server_default=func.now())