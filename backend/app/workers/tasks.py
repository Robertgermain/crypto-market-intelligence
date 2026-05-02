from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.market_price import MarketPrice
from app.services.signal_service import detect_price_spike, create_signal


def process_price_data(asset_id: int):
    """
    Worker task:
    - Load recent price history
    - Detect signals
    - Persist signals

    IMPORTANT:
    This worker MUST NOT call ingest_market_data().
    That causes recursive jobs + API rate limiting.
    """

    db: Session = SessionLocal()

    try:
        # -----------------------------------
        # 1. Validate asset
        # -----------------------------------
        asset = db.query(Asset).filter(Asset.id == asset_id).first()

        if not asset:
            print(f"[ERROR] Asset {asset_id} not found")
            return

        print(f"[INFO] Processing signals for asset: {asset.symbol}")

        # -----------------------------------
        # 2. Get recent price history
        # -----------------------------------
        recent_prices = (
            db.query(MarketPrice)
            .filter(MarketPrice.asset_id == asset_id)
            .order_by(MarketPrice.observed_at.desc())
            .limit(10)
            .all()
        )

        # Convert to chronological order
        recent_prices = list(reversed(recent_prices))

        if len(recent_prices) < 2:
            print("[WARN] Not enough data to detect signals")
            return

        # -----------------------------------
        # 3. Detect signal
        # -----------------------------------
        signal_data = detect_price_spike(
            recent_prices,
            threshold=Decimal("5.0")
        )

        if not signal_data:
            print("[INFO] No signal detected")
            return

        # -----------------------------------
        # 4. Persist signal
        # -----------------------------------
        create_signal(db, asset_id, signal_data)

        print(f"[SUCCESS] Signal created: {signal_data['signal_type']}")

    # -----------------------------------
    # DB Error Handling
    # -----------------------------------
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[DB ERROR] Asset {asset_id}: {e}")

    # -----------------------------------
    # Catch-All Error Handling
    # -----------------------------------
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Asset {asset_id}: {e}")

    finally:
        db.close()