from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal
from app.services.indicator_service import calculate_rsi


# ---------------------------------------------------------
# CORE CALCULATION
# ---------------------------------------------------------
def calculate_price_change_percent(
    old_price: Decimal,
    new_price: Decimal
) -> Decimal:
    if old_price == 0:
        return Decimal("0")

    return ((new_price - old_price) / old_price) * 100


# ---------------------------------------------------------
# PRICE SPIKE SIGNAL
# ---------------------------------------------------------
def detect_price_spike(
    prices: List[MarketPrice],
    threshold: Decimal = Decimal("5.0")
) -> Optional[Dict[str, Any]]:

    if len(prices) < 2:
        return None

    old_price = prices[0].price_usd
    new_price = prices[-1].price_usd

    percent_change = calculate_price_change_percent(old_price, new_price)

    if percent_change >= threshold:
        return {
            "signal_type": "PRICE_SPIKE",
            "strength": percent_change,
            "metadata": {
                "old_price": str(old_price),
                "new_price": str(new_price),
                "percent_change": str(percent_change),
            },
            "detected_at": datetime.now(timezone.utc),
        }

    return None


# ---------------------------------------------------------
# RSI SIGNAL
# ---------------------------------------------------------
def detect_rsi_signal(
    prices: List[MarketPrice],
) -> Optional[Dict[str, Any]]:

    rsi = calculate_rsi(prices)

    if rsi is None:
        return None

    if rsi >= Decimal("70"):
        return {
            "signal_type": "RSI_OVERBOUGHT",
            "strength": rsi,
            "metadata": {
                "rsi": float(rsi)
            },
            "detected_at": datetime.now(timezone.utc),
        }

    if rsi <= Decimal("30"):
        return {
            "signal_type": "RSI_OVERSOLD",
            "strength": rsi,
            "metadata": {
                "rsi": float(rsi)
            },
            "detected_at": datetime.now(timezone.utc),
        }

    return None


# ---------------------------------------------------------
# MULTI-SIGNAL DETECTION (NEW)
# ---------------------------------------------------------
def detect_signals(
    prices: List[MarketPrice]
) -> List[Dict[str, Any]]:
    """
    Run ALL signal detectors and return list of signals
    """

    signals = []

    price_spike = detect_price_spike(prices)
    if price_spike:
        signals.append(price_spike)

    rsi_signal = detect_rsi_signal(prices)
    if rsi_signal:
        signals.append(rsi_signal)

    return signals


# ---------------------------------------------------------
# PERSISTENCE LAYER (DB WRITE)
# ---------------------------------------------------------
def create_signal(
    db: Session,
    asset_id: int,
    signal_data: Dict[str, Any],
) -> MarketSignal:

    signal = MarketSignal(
        asset_id=asset_id,
        signal_type=signal_data["signal_type"],
        strength=signal_data["strength"],
        signal_metadata=signal_data.get("metadata"),
        detected_at=signal_data.get("detected_at"),
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    return signal