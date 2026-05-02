from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal

from app.services.signal_service import (
    detect_signals,
    create_signal,
)


def process_price_data(asset_id: int):
    """
    Worker task:
    - Load recent price history
    - Detect signals (multi-signal)
    - Prevent duplicate consecutive signals
    - Persist signals

    IMPORTANT:
    This worker MUST NOT call ingest_market_data().
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
            .limit(20)
            .all()
        )

        # Convert to chronological order: oldest -> newest
        recent_prices = list(reversed(recent_prices))

        if len(recent_prices) < 2:
            print("[WARN] Not enough data to detect signals")
            return

        # -----------------------------------
        # 3. Detect signals
        # -----------------------------------
        signals = detect_signals(recent_prices)

        if not signals:
            print("[INFO] No signals detected")
            return

        # -----------------------------------
        # 4. Get latest existing signal
        # -----------------------------------
        latest_signal = (
            db.query(MarketSignal)
            .filter(MarketSignal.asset_id == asset_id)
            .order_by(MarketSignal.detected_at.desc())
            .first()
        )

        # -----------------------------------
        # 5. Persist signals with deduplication
        # -----------------------------------
        for signal_data in signals:
            signal_type = signal_data["signal_type"]

            if latest_signal and latest_signal.signal_type == signal_type:
                print(f"[SKIP] Duplicate consecutive signal: {signal_type}")
                continue

            create_signal(db, asset_id, signal_data)
            print(f"[SUCCESS] Signal created: {signal_type}")

    except SQLAlchemyError as e:
        db.rollback()
        print(f"[DB ERROR] Asset {asset_id}: {e}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Asset {asset_id}: {e}")

    finally:
        db.close()