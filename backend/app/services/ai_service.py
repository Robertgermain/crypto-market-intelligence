import os
from typing import List, Dict, Any

# -----------------------------------
# Safe OpenAI import
# -----------------------------------
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app.prompts.trading_prompt import (
    build_trading_prompt,
    build_confidence_prompt,
)

# -----------------------------------
# Initialize client safely
# -----------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OpenAI and OPENAI_API_KEY else None


# =========================================================
# DECISION EXPLANATION
# =========================================================
def generate_decision_explanation(
    asset_symbol: str,
    decision: str,
    confidence: int,
    signals: List[str],
    signal_data: List[Dict[str, Any]],
) -> str:
    """
    Generate AI explanation using structured prompt.
    """

    if client is None:
        return "AI disabled (no OpenAI client or API key)."

    try:
        # -----------------------------------
        # Build prompt via prompt layer
        # -----------------------------------
        prompt = build_trading_prompt(
            asset_symbol=asset_symbol,
            decision=decision,
            confidence=confidence,
            signals=signals,
            signal_data=signal_data,
        )

        # -----------------------------------
        # Call OpenAI
        # -----------------------------------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly precise crypto trading analyst.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content

        if not content:
            return "AI returned empty response."

        return content.strip()

    except Exception as e:
        print(f"[AI ERROR] Failed to generate explanation: {e}")
        return "AI explanation unavailable."


# =========================================================
# AI CONFIDENCE ADJUSTMENT
# =========================================================
def generate_confidence_adjustment(
    asset_symbol: str,
    decision: str,
    base_confidence: int,
    signals: List[str],
    signal_data: List[Dict[str, Any]],
) -> int:
    """
    AI refines confidence score (0–100)
    """

    # No signals = no confidence
    if not signals:
        return 0

    if client is None:
        return base_confidence

    try:
        # -----------------------------------
        # Build prompt via prompt layer
        # -----------------------------------
        prompt = build_confidence_prompt(
            asset_symbol=asset_symbol,
            decision=decision,
            base_confidence=base_confidence,
            signal_data=signal_data,
        )

        # -----------------------------------
        # Call OpenAI
        # -----------------------------------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise trading risk evaluator.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,  # low = consistent
        )

        raw = response.choices[0].message.content.strip()

        # -----------------------------------
        # Safe parsing
        # -----------------------------------
        try:
            value = int(float(raw))
        except Exception:
            print(f"[AI WARNING] Invalid confidence output: {raw}")
            return base_confidence

        return max(0, min(100, value))

    except Exception as e:
        print(f"[AI ERROR] Confidence adjustment failed: {e}")
        return base_confidence


# =========================================================
# RISK (NON-AI → FAST + RELIABLE)
# =========================================================
def calculate_risk_level(confidence: int, signal_count: int) -> str:
    """
    Lightweight deterministic risk model
    """

    if confidence >= 70:
        return "LOW"
    elif confidence >= 30:
        return "MEDIUM"
    return "HIGH"