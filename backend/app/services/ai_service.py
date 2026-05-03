import os
from typing import List, Dict, Any

# -----------------------------------
# Safe OpenAI import (prevents pytest crash)
# -----------------------------------
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# -----------------------------------
# Initialize client safely
# -----------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OpenAI and OPENAI_API_KEY else None


# =========================================================
# DECISION EXPLANATION (EXISTING - IMPROVED SAFETY)
# =========================================================
def generate_decision_explanation(
    asset_symbol: str,
    decision: str,
    confidence: int,
    signals: List[str],
    signal_data: List[Dict[str, Any]],
) -> str:
    """
    Generate AI explanation using REAL signal data.
    """

    if client is None:
        return "AI disabled (no OpenAI client or API key)."

    try:
        # -----------------------------------
        # Build signal detail block
        # -----------------------------------
        if signal_data:
            signal_details = "\n".join([
                f"- {s.get('signal_type')}: "
                f"strength={round(float(s.get('strength', 0)), 2) if s.get('strength') is not None else 'N/A'}, "
                f"metadata={s.get('metadata')}"
                for s in signal_data
            ])
        else:
            signal_details = "None"

        # -----------------------------------
        # Prompt
        # -----------------------------------
        prompt = f"""
You are a professional crypto trading analyst.

Analyze the trading decision using the ACTUAL signal data provided.

Asset: {asset_symbol}
Decision: {decision}
Confidence: {confidence}%

Signals:
{signal_details}

Instructions:
- Be data-driven (reference actual values like % change, RSI, etc.)
- Do NOT make generic statements like "crypto is volatile"
- Be decisive and professional
- Explain WHY the decision makes sense
- STRICTLY limit to 2 sentences

Return only the explanation.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a highly precise crypto trading analyst."},
                {"role": "user", "content": prompt},
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
# 🔥 NEW: AI CONFIDENCE ADJUSTMENT
# =========================================================
def generate_confidence_adjustment(
    asset_symbol: str,
    decision: str,
    base_confidence: int,
    signals: List[str],
    signal_data: List[Dict[str, Any]],
) -> int:
    """
    AI refines confidence score (0–100).

    Rules:
    - Never breaks system (fallback to base_confidence)
    - Always returns valid int
    """

    if client is None:
        return base_confidence

    try:
        # -----------------------------------
        # Build signal detail block
        # -----------------------------------
        if signal_data:
            signal_details = "\n".join([
                f"- {s.get('signal_type')}: strength={round(float(s.get('strength', 0)), 2)}"
                for s in signal_data
            ])
        else:
            signal_details = "None"

        # -----------------------------------
        # Prompt
        # -----------------------------------
        prompt = f"""
You are a crypto trading risk model.

Adjust the confidence score based on signal strength and realism.

Asset: {asset_symbol}
Decision: {decision}
Base Confidence: {base_confidence}%

Signals:
{signal_details}

Rules:
- Return ONLY a number between 0 and 100
- Be CONSERVATIVE (avoid overconfidence)
- Weak signals → reduce confidence
- Strong signals → increase confidence
- No signals → return 0

Output ONLY the number.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise trading risk evaluator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # 🔥 VERY LOW = deterministic
        )

        raw = response.choices[0].message.content.strip()

        # -----------------------------------
        # Safe parsing (VERY IMPORTANT)
        # -----------------------------------
        try:
            value = int(float(raw))
        except Exception:
            print(f"[AI WARNING] Invalid confidence output: {raw}")
            return base_confidence

        # Clamp range
        return max(0, min(100, value))

    except Exception as e:
        print(f"[AI ERROR] Confidence adjustment failed: {e}")
        return base_confidence