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


def generate_decision_explanation(
    asset_symbol: str,
    decision: str,
    confidence: int,
    signals: List[str],
    signal_data: List[Dict[str, Any]],  # ✅ NEW (critical)
) -> str:
    """
    Generate AI explanation using REAL signal data.

    Safe for:
    - missing OpenAI package
    - missing API key
    - test environments
    """

    # -----------------------------------
    # Disable AI if not available
    # -----------------------------------
    if client is None:
        return "AI disabled (no OpenAI client or API key)."

    try:
        # -----------------------------------
        # Build signal detail block (DATA-AWARE)
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
        # Strong, data-driven prompt
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
            temperature=0.3,  # lower = more consistent + less fluff
        )

        # -----------------------------------
        # Extract response safely
        # -----------------------------------
        content = response.choices[0].message.content

        if not content:
            return "AI returned empty response."

        return content.strip()

    except Exception as e:
        # -----------------------------------
        # Fail-safe (CRITICAL for production)
        # -----------------------------------
        print(f"[AI ERROR] Failed to generate explanation: {e}")
        return "AI explanation unavailable."