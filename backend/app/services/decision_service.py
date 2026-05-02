from typing import List, Dict, Any

from app.core.constants import (
    SIGNAL_WEIGHTS,
    BUY,
    SELL,
    HOLD,
)


def calculate_score(signals: List[Dict[str, Any]]) -> int:
    """
    Sum weighted signals into a total score.
    """
    score = 0

    for signal in signals:
        signal_type = signal["signal_type"]
        weight = SIGNAL_WEIGHTS.get(signal_type, 0)
        score += weight

    return score


def determine_decision(score: int) -> str:
    """
    Convert score into BUY / SELL / HOLD.
    """
    if score >= 2:
        return BUY
    elif score <= -2:
        return SELL
    return HOLD


def calculate_confidence(score: int) -> int:
    """
    Convert score into confidence percentage (0–100).
    """
    # Simple normalization
    confidence = min(abs(score) * 25, 100)
    return confidence


def generate_decision(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point for decision engine.
    """
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