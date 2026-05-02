from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal
from app.services.indicator_service import calculate_rsi

from app.core.constants import (
    PRICE_SPIKE,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    MA_BULLISH_CROSSOVER,
    MA_BEARISH_CROSSOVER,
)


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
# MOVING AVERAGE
# ---------------------------------------------------------
def calculate_moving_average(prices: List[MarketPrice], window: int):
    if len(prices) < window:
        return None

    subset = prices[-window:]
    total = sum(p.price_usd for p in subset)
    return total / window


# ---------------------------------------------------------
# PRICE SPIKE
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
            "signal_type": PRICE_SPIKE,
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
# RSI
# ---------------------------------------------------------
def detect_rsi_signal(
    prices: List[MarketPrice],
) -> Optional[Dict[str, Any]]:

    rsi = calculate_rsi(prices)

    if rsi is None:
        return None

    if rsi >= Decimal("70"):
        return {
            "signal_type": RSI_OVERBOUGHT,
            "strength": rsi,
            "metadata": {"rsi": float(rsi)},
            "detected_at": datetime.now(timezone.utc),
        }

    if rsi <= Decimal("30"):
        return {
            "signal_type": RSI_OVERSOLD,
            "strength": rsi,
            "metadata": {"rsi": float(rsi)},
            "detected_at": datetime.now(timezone.utc),
        }

    return None


# ---------------------------------------------------------
# FIXED MA CROSSOVER
# ---------------------------------------------------------
def detect_ma_crossover(
    prices: List[MarketPrice]
) -> Optional[Dict[str, Any]]:

    SHORT_WINDOW = 5
    LONG_WINDOW = 10

    # 🔥 FIX: need LONG + 1 for previous comparison
    if len(prices) < LONG_WINDOW + 1:
        return None

    short_prev = calculate_moving_average(prices[:-1], SHORT_WINDOW)
    long_prev = calculate_moving_average(prices[:-1], LONG_WINDOW)

    short_curr = calculate_moving_average(prices, SHORT_WINDOW)
    long_curr = calculate_moving_average(prices, LONG_WINDOW)

    if not all([short_prev, long_prev, short_curr, long_curr]):
        return None

    # Bullish crossover
    if short_prev <= long_prev and short_curr > long_curr:
        return {
            "signal_type": MA_BULLISH_CROSSOVER,
            "strength": short_curr - long_curr,
            "metadata": {
                "short_ma": str(short_curr),
                "long_ma": str(long_curr),
                "prev_short_ma": str(short_prev),
                "prev_long_ma": str(long_prev),
            },
            "detected_at": datetime.now(timezone.utc),
        }

    # Bearish crossover
    if short_prev >= long_prev and short_curr < long_curr:
        return {
            "signal_type": MA_BEARISH_CROSSOVER,
            "strength": long_curr - short_curr,
            "metadata": {
                "short_ma": str(short_curr),
                "long_ma": str(long_curr),
                "prev_short_ma": str(short_prev),
                "prev_long_ma": str(long_prev),
            },
            "detected_at": datetime.now(timezone.utc),
        }

    return None


# ---------------------------------------------------------
# MULTI SIGNAL (PRIORITIZED)
# ---------------------------------------------------------
def detect_signals(
    prices: List[MarketPrice]
) -> List[Dict[str, Any]]:

    signals = []

    # 1. MA crossover FIRST (most important)
    ma_signal = detect_ma_crossover(prices)
    if ma_signal:
        signals.append(ma_signal)

    # 2. RSI
    rsi_signal = detect_rsi_signal(prices)
    if rsi_signal:
        signals.append(rsi_signal)

    # 3. Spike LAST (least important)
    price_spike = detect_price_spike(prices)
    if price_spike:
        signals.append(price_spike)

    return signals


# ---------------------------------------------------------
# PERSISTENCE
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