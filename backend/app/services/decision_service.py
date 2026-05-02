from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.core.constants import (
    SIGNAL_WEIGHTS,
    BUY,
    SELL,
    HOLD,
)

from app.models.decision import Decision


# ---------------------------------------------------------
# SCORING
# ---------------------------------------------------------
def calculate_score(signals: List[Dict[str, Any]]) -> int:
    score = 0

    for signal in signals:
        signal_type = signal["signal_type"]
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
        "signals": [s["signal_type"] for s in signals],
    }


# ---------------------------------------------------------
# PERSISTENCE (🔥 NEW)
# ---------------------------------------------------------
def create_decision(
    db: Session,
    asset_id: int,
    decision_data: Dict[str, Any],
) -> Decision:

    decision = Decision(
        asset_id=asset_id,
        decision=decision_data["decision"],
        confidence=decision_data["confidence"],
        score=decision_data["score"],
        decision_metadata={
            "signals": decision_data.get("signals", [])
        },
    )

    db.add(decision)
    db.commit()
    db.refresh(decision)

    return decision