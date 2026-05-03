from typing import List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.ai_service import generate_decision_explanation
from app.models.asset import Asset
from app.models.decision import Decision

from app.core.constants import (
    SIGNAL_WEIGHTS,
    BUY,
    SELL,
    HOLD,
)


# ---------------------------------------------------------
# SCORING
# ---------------------------------------------------------
def calculate_score(signals: List[Dict[str, Any]]) -> int:
    score = 0

    for signal in signals:
        signal_type = signal.get("signal_type")
        weight = SIGNAL_WEIGHTS.get(signal_type, 0)
        score += weight

    return score


# ---------------------------------------------------------
# DECISION LOGIC
# ---------------------------------------------------------
def determine_decision(score: int) -> str:
    if score >= 2:
        return BUY
    elif score <= -2:
        return SELL
    return HOLD


# ---------------------------------------------------------
# CONFIDENCE
# ---------------------------------------------------------
def calculate_confidence(score: int) -> int:
    return min(abs(score) * 25, 100)


# ---------------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------------
def generate_decision(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not signals:
        return {
            "decision": HOLD,
            "confidence": 0,
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
        "signals": signals,  # ✅ FULL SIGNAL DATA (not just types)
    }


# ---------------------------------------------------------
# PERSISTENCE (WITH DATA-AWARE AI)
# ---------------------------------------------------------
def create_decision(
    db: Session,
    asset_id: int,
    decision_data: Dict[str, Any],
) -> Decision:

    signals = decision_data.get("signals", []) or []

    # -----------------------------------
    # Get asset symbol
    # -----------------------------------
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    symbol = asset.symbol if asset else "UNKNOWN"

    # -----------------------------------
    # Extract signal types for metadata
    # -----------------------------------
    signal_types = [s.get("signal_type") for s in signals]

    # -----------------------------------
    # Generate AI explanation (DATA-AWARE)
    # -----------------------------------
    if signals:
        try:
            explanation = generate_decision_explanation(
                asset_symbol=symbol,
                decision=decision_data["decision"],
                confidence=decision_data["confidence"],
                signals=signal_types,        # simple list
                signal_data=signals,         # FULL DATA
            )
        except Exception as e:
            print(f"[AI ERROR] Failed to generate explanation: {e}")
            explanation = "AI explanation unavailable."
    else:
        explanation = (
            "No significant signals detected. "
            "HOLD decision based on neutral market conditions."
        )

    # -----------------------------------
    # Create decision (CLEAN METADATA)
    # -----------------------------------
    decision = Decision(
        asset_id=asset_id,
        decision=decision_data["decision"],
        confidence=decision_data["confidence"],
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