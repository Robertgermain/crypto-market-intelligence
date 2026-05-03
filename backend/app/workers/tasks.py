from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal
from app.models.decision import Decision

from app.services.signal_service import detect_signals, create_signal
from app.services.decision_service import generate_decision, create_decision
from app.services.market_data_service import ingest_market_data

MIN_REQUIRED_PRICES = 11


# =========================================================
# PROCESS SINGLE ASSET
# =========================================================
def process_price_data(asset_id: int):

    db: Session = SessionLocal()

    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()

        if not asset:
            print(f"[ERROR] Asset {asset_id} not found")
            return

        print(f"[INFO] Processing signals for asset: {asset.symbol}")

        recent_prices = (
            db.query(MarketPrice)
            .filter(MarketPrice.asset_id == asset_id)
            .order_by(MarketPrice.observed_at.desc())
            .limit(50)
            .all()
        )

        recent_prices = list(reversed(recent_prices))

        print(f"[DEBUG] Loaded {len(recent_prices)} prices")

        if len(recent_prices) < MIN_REQUIRED_PRICES:
            print(f"[WARN] Not enough data ({len(recent_prices)})")
            return

        signals = detect_signals(recent_prices) or []

        decision_data = generate_decision(signals)

        print(
            f"[DECISION] {decision_data['decision']} "
            f"(confidence={decision_data['confidence']}%, score={decision_data['score']})"
        )

        last_decision = (
            db.query(Decision)
            .filter(Decision.asset_id == asset_id)
            .order_by(Decision.created_at.desc())
            .first()
        )

        if last_decision:
            if (
                last_decision.decision == decision_data["decision"]
                and last_decision.score == decision_data["score"]
            ):
                print("[SKIP] Duplicate decision — no change")
                return

        decision_record = create_decision(db, asset_id, decision_data)

        print(f"[SUCCESS] Decision stored (id={decision_record.id})")

        if not signals:
            print("[INFO] No signals detected")
            return

        recent_signals = (
            db.query(MarketSignal)
            .filter(MarketSignal.asset_id == asset_id)
            .order_by(MarketSignal.detected_at.desc())
            .limit(10)
            .all()
        )

        last_signal_by_type = {}
        for s in recent_signals:
            if s.signal_type not in last_signal_by_type:
                last_signal_by_type[s.signal_type] = s

        created_any = False

        for signal_data in signals:
            signal_type = signal_data["signal_type"]
            strength = signal_data.get("strength")

            prev = last_signal_by_type.get(signal_type)

            if prev:
                try:
                    delta = abs(float(strength) - float(prev.strength))
                    if delta < 0.5:
                        print(f"[SKIP] Duplicate signal: {signal_type}")
                        continue
                except Exception:
                    continue

            if "detected_at" not in signal_data:
                signal_data["detected_at"] = datetime.now(timezone.utc)

            signal_data["decision_id"] = decision_record.id

            create_signal(db, asset_id, signal_data)

            print(f"[SUCCESS] Signal created: {signal_type}")
            created_any = True

        if not created_any:
            print("[INFO] All signals were duplicates")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Asset {asset_id}: {e}")

    finally:
        db.close()


# =========================================================
# 🔥 FULL PIPELINE (KEY ADDITION)
# =========================================================
def run_full_pipeline():

    db: Session = SessionLocal()

    try:
        print("\n[PIPELINE] Starting full pipeline...\n")

        # 1. INGEST
        ingest_market_data(db, limit=20)

        # 2. GET ALL ASSETS
        assets = db.query(Asset).all()
        print(f"[PIPELINE] Processing {len(assets)} assets")

        # 3. PROCESS ALL
        for asset in assets:
            process_price_data(asset.id)

        print("\n[PIPELINE] COMPLETE\n")

    except Exception as e:
        print(f"[PIPELINE ERROR] {e}")

    finally:
        db.close()