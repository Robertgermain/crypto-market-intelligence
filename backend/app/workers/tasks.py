from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal
from app.models.decision import Decision

from app.services.signal_service import (
    detect_signals,
    create_signal,
)

from app.services.decision_service import generate_decision, create_decision

MIN_REQUIRED_PRICES = 11


def process_price_data(asset_id: int):
    """
    Worker task:
    - Load recent price history
    - Detect signals
    - Generate decision
    - Idempotent decision creation
    - Deduplicated signal persistence (linked to decision)
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
        # 2. Load prices
        # -----------------------------------
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

        # -----------------------------------
        # 3. Detect signals
        # -----------------------------------
        signals = detect_signals(recent_prices) or []

        # -----------------------------------
        # 4. Generate decision
        # -----------------------------------
        decision_data = generate_decision(signals)

        print(
            f"[DECISION] {decision_data['decision']} "
            f"(confidence={decision_data['confidence']}%, score={decision_data['score']})"
        )

        # -----------------------------------
        # 5. IDEMPOTENCY CHECK
        # -----------------------------------
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

        # -----------------------------------
        # 6. Store decision
        # -----------------------------------
        decision_record = create_decision(db, asset_id, decision_data)

        print(f"[SUCCESS] Decision stored (id={decision_record.id})")

        # -----------------------------------
        # 7. If no signals → done
        # -----------------------------------
        if not signals:
            print("[INFO] No signals detected")
            return

        print(f"[DEBUG] Detected signals: {[s['signal_type'] for s in signals]}")

        # -----------------------------------
        # 8. Load recent signals (for dedup)
        # -----------------------------------
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

        # -----------------------------------
        # 9. Persist signals (SMART DEDUP)
        # -----------------------------------
        created_any = False

        for signal_data in signals:
            signal_type = signal_data["signal_type"]
            strength = signal_data.get("strength")

            prev = last_signal_by_type.get(signal_type)

            # ---- Dedup logic ----
            if prev:
                try:
                    prev_strength = float(prev.strength)
                    curr_strength = float(strength)

                    delta = abs(curr_strength - prev_strength)

                    if delta < 0.5:
                        print(f"[SKIP] Duplicate signal: {signal_type}")
                        continue

                except Exception:
                    print(f"[SKIP] Duplicate consecutive signal: {signal_type}")
                    continue

            # ---- Ensure timestamp ----
            if "detected_at" not in signal_data or not signal_data["detected_at"]:
                signal_data["detected_at"] = datetime.now(timezone.utc)

            # ---- Link to decision ----
            signal_data["decision_id"] = decision_record.id

            create_signal(db, asset_id, signal_data)

            print(
                f"[SUCCESS] Signal created: {signal_type} "
                f"(decision_id={decision_record.id})"
            )

            created_any = True

        if not created_any:
            print("[INFO] All detected signals were duplicates")

    except SQLAlchemyError as e:
        db.rollback()
        print(f"[DB ERROR] Asset {asset_id}: {e}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Asset {asset_id}: {e}")

    finally:
        db.close()