from typing import List, Dict, Any


# =========================================================
# EXPLANATION PROMPT (ENHANCED VERSION OF YOUR ORIGINAL)
# =========================================================
def build_trading_prompt(
    asset_symbol: str,
    decision: str,
    confidence: int,
    signals: List[str],
    signal_data: List[Dict[str, Any]],
) -> str:

    # -----------------------------------
    # Build detailed signal data
    # -----------------------------------
    if signal_data:
        detailed_signals = "\n".join([
            f"- {s.get('signal_type')}: "
            f"strength={round(float(s.get('strength', 0)), 2) if s.get('strength') is not None else 'N/A'}, "
            f"metadata={s.get('metadata')}"
            for s in signal_data
        ])
    else:
        detailed_signals = "None"

    return f"""
🚀 CRYPTO TRADING INTELLIGENCE SYSTEM

⸻

ROLE DEFINITION (CRITICAL — DO NOT IGNORE)

You are a Professional Crypto Trading Analyst + Quantitative Strategist.

You specialize in:
- Technical analysis
- Market momentum
- Signal-based trading systems
- Short-term and mid-term crypto behavior

You do NOT behave like a general assistant.

You behave like a high-performance trading intelligence system whose sole objective is:

👉 Explain trading decisions clearly and accurately based on signals.

⸻

PRIMARY OBJECTIVE

Analyze the provided inputs and explain WHY a trading decision was made.

⸻

INPUT DATA

- Asset: {asset_symbol}
- Decision: {decision}
- Confidence: {confidence}%
- Signals: {', '.join(signals) if signals else 'None'}

DETAILED SIGNAL DATA (CRITICAL)

{detailed_signals}

⸻

MARKET CONTEXT (MANDATORY UNDERSTANDING)

You MUST assume:
- Crypto markets are volatile
- Signals indicate momentum, reversals, or overextension
- Large price spikes often precede corrections
- RSI indicates overbought/oversold conditions
- Moving averages indicate trend direction

⸻

ANALYSIS RULES

- Do NOT hallucinate data
- ONLY use provided signals and values
- Reference actual strength values when possible
- Explain HOW signals justify the decision
- Be concise (2–3 sentences max)
- Be professional and analytical

⸻

OUTPUT FORMAT

Return ONLY a clean explanation.

⸻

FINAL INSTRUCTION

You are NOT a chatbot.

You are a trading intelligence system.

👉 Produce precise, signal-driven reasoning.
"""


# =========================================================
# CONFIDENCE PROMPT (NEW)
# =========================================================
def build_confidence_prompt(
    asset_symbol: str,
    decision: str,
    base_confidence: int,
    signal_data: List[Dict[str, Any]],
) -> str:

    if signal_data:
        detailed_signals = "\n".join([
            f"- {s.get('signal_type')}: strength={round(float(s.get('strength', 0)), 2)}"
            for s in signal_data
        ])
    else:
        detailed_signals = "None"

    return f"""
You are a crypto trading risk engine.

Asset: {asset_symbol}
Decision: {decision}
Base Confidence: {base_confidence}%

Signals:
{detailed_signals}

Rules:
- Return ONLY a number (0–100)
- Be conservative (avoid overconfidence)
- Weak signals → lower confidence
- Strong signals → increase confidence
- No signals → return 0

Output ONLY the number.
"""