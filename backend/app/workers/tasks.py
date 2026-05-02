from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.signal_service import detect_price_spike, create_signal
from app.models.market_price import MarketPrice


def process_price_data(asset_id: int):
    """
    Worker task:
    - Fetch recent prices
    - Detect signals
    - Save if found
    """

    db: Session = SessionLocal()

    try:
        prices = (
            db.query(MarketPrice)
            .filter(MarketPrice.asset_id == asset_id)
            .order_by(MarketPrice.observed_at.asc())
            .limit(50)
            .all()
        )

        signal_data = detect_price_spike(prices)

        if signal_data:
            create_signal(db, asset_id, signal_data)

    finally:
        db.close()