from typing import List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.ai_service import (
    generate_decision_explanation,
    generate_confidence_adjustment,
)
from app.models.asset import Asset
from app.models.decision import Decision

from app.core.constants import BUY, SELL, HOLD


# =========================================================
# SIMPLE WEIGHTS (EASY TO UNDERSTAND)
# =========================================================
SIGNAL_WEIGHTS = {
    "RSI_OVERBOUGHT": -1,
    "RSI_OVERSOLD": 1,
    "MOMENTUM_UP": 2,
    "MOMENTUM_DOWN": -2,
    "MA_BULLISH_CROSSOVER": 2,
    "MA_BEARISH_CROSSOVER": -2,
}


# =========================================================
# SCORING (SIMPLE)
# =========================================================
def calculate_score(signals: List[Dict[str, Any]]) -> int:
    score = 0

    for signal in signals:
        signal_type = signal.get("signal_type")
        score += SIGNAL_WEIGHTS.get(signal_type, 0)

    return score


# =========================================================
# DECISION LOGIC (LOOSENED)
# =========================================================
def determine_decision(score: int) -> str:
    if score >= 2:
        return BUY

    if score <= -2:
        return SELL

    return HOLD


# =========================================================
# CONFIDENCE (CLEAN + CONSISTENT)
# =========================================================
def calculate_confidence(score: int) -> int:
    base = abs(score) * 25

    if base == 0:
        return 20  # no more 0% confidence

    return min(base, 100)


# =========================================================
# MAIN GENERATOR
# =========================================================
def generate_decision(signals: List[Dict[str, Any]]) -> Dict[str, Any]:

    if not signals:
        return {
            "decision": HOLD,
            "confidence": 20,
            "score": 0,
            "signals": [],
        }

    score = calculate_score(signals)
    decision = determine_decision(score)
    confidence = calculate_confidence(score)

    return {
        "decision": decision,
        "confidence": confidence,
        "score": score,
        "signals": signals,
    }


# =========================================================
# PERSISTENCE (KEEP AI — THIS IS YOUR EDGE)
# =========================================================
def create_decision(
    db: Session,
    asset_id: int,
    decision_data: Dict[str, Any],
) -> Decision:

    signals = decision_data.get("signals", []) or []

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    symbol = asset.symbol if asset else "UNKNOWN"

    signal_types = [s.get("signal_type") for s in signals]

    base_confidence = decision_data["confidence"]

    # -----------------------------------
    # AI CONFIDENCE (LIGHT TOUCH)
    # -----------------------------------
    adjusted_confidence = base_confidence

    if signals:
        try:
            ai_conf = generate_confidence_adjustment(
                asset_symbol=symbol,
                decision=decision_data["decision"],
                base_confidence=base_confidence,
                signals=signal_types,
                signal_data=signals,
            )

            # Clamp slightly (don’t let AI go crazy)
            adjusted_confidence = max(
                base_confidence - 15,
                min(ai_conf, base_confidence + 15)
            )

        except Exception as e:
            print(f"[AI ERROR] Confidence adjustment failed: {e}")

    # -----------------------------------
    # AI EXPLANATION (KEEP THIS)
    # -----------------------------------
    if signals:
        try:
            explanation = generate_decision_explanation(
                asset_symbol=symbol,
                decision=decision_data["decision"],
                confidence=adjusted_confidence,
                signals=signal_types,
                signal_data=signals,
            )
        except Exception as e:
            print(f"[AI ERROR] Failed explanation: {e}")
            explanation = "AI explanation unavailable."
    else:
        explanation = "No signals detected. HOLD."

    # -----------------------------------
    # SAVE
    # -----------------------------------
    decision = Decision(
        asset_id=asset_id,
        decision=decision_data["decision"],
        confidence=adjusted_confidence,
        score=decision_data["score"],
        decision_metadata={
            "signals": signal_types,
            "signal_count": len(signal_types),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "explanation": explanation,
        },
    )

    db.add(decision)
    db.commit()
    db.refresh(decision)

    return decision