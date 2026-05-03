from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from statistics import stdev

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

    old_price = prices[-2].price_usd
    new_price = prices[-1].price_usd

    percent_change = calculate_price_change_percent(old_price, new_price)
    abs_change = abs(percent_change)

    if abs_change >= threshold:
        return {
            "signal_type": PRICE_SPIKE,
            "strength": abs_change,
            "metadata": {
                "direction": "UP" if percent_change > 0 else "DOWN",
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
# MA CROSSOVER
# ---------------------------------------------------------
def detect_ma_crossover(
    prices: List[MarketPrice]
) -> Optional[Dict[str, Any]]:

    SHORT_WINDOW = 5
    LONG_WINDOW = 10

    if len(prices) < LONG_WINDOW + 1:
        return None

    short_prev = calculate_moving_average(prices[:-1], SHORT_WINDOW)
    long_prev = calculate_moving_average(prices[:-1], LONG_WINDOW)

    short_curr = calculate_moving_average(prices, SHORT_WINDOW)
    long_curr = calculate_moving_average(prices, LONG_WINDOW)

    if not all([short_prev, long_prev, short_curr, long_curr]):
        return None

    if short_prev <= long_prev and short_curr > long_curr:
        return {
            "signal_type": MA_BULLISH_CROSSOVER,
            "strength": short_curr - long_curr,
            "metadata": {
                "short_ma": str(short_curr),
                "long_ma": str(long_curr),
            },
            "detected_at": datetime.now(timezone.utc),
        }

    if short_prev >= long_prev and short_curr < long_curr:
        return {
            "signal_type": MA_BEARISH_CROSSOVER,
            "strength": long_curr - short_curr,
            "metadata": {
                "short_ma": str(short_curr),
                "long_ma": str(long_curr),
            },
            "detected_at": datetime.now(timezone.utc),
        }

    return None


# ---------------------------------------------------------
# 🔥 MOMENTUM SIGNAL (NEW)
# ---------------------------------------------------------
def detect_momentum(
    prices: List[MarketPrice],
    threshold: Decimal = Decimal("1.0")
) -> Optional[Dict[str, Any]]:

    if len(prices) < 2:
        return None

    old_price = prices[-2].price_usd
    new_price = prices[-1].price_usd

    percent_change = calculate_price_change_percent(old_price, new_price)

    if percent_change >= threshold:
        return {
            "signal_type": "MOMENTUM_UP",
            "strength": percent_change,
            "metadata": {"change_percent": str(percent_change)},
            "detected_at": datetime.now(timezone.utc),
        }

    if percent_change <= -threshold:
        return {
            "signal_type": "MOMENTUM_DOWN",
            "strength": abs(percent_change),
            "metadata": {"change_percent": str(percent_change)},
            "detected_at": datetime.now(timezone.utc),
        }

    return None


# ---------------------------------------------------------
# 🔥 VOLATILITY SIGNAL (NEW)
# ---------------------------------------------------------
def detect_volatility(
    prices: List[MarketPrice],
) -> Optional[Dict[str, Any]]:

    if len(prices) < 10:
        return None

    values = [float(p.price_usd) for p in prices[-10:]]
    volatility = stdev(values)

    last_price = float(prices[-1].price_usd)

    if volatility > last_price * 0.01:  # 1% volatility
        return {
            "signal_type": "VOLATILITY_SPIKE",
            "strength": Decimal(str(volatility)),
            "metadata": {"volatility": volatility},
            "detected_at": datetime.now(timezone.utc),
        }

    return None


# ---------------------------------------------------------
# 🔥 MULTI SIGNAL ENGINE (UPDATED)
# ---------------------------------------------------------
def detect_signals(
    prices: List[MarketPrice]
) -> List[Dict[str, Any]]:

    signals = []

    if len(prices) < 5:
        return signals

    # Priority order matters
    detectors = [
        detect_ma_crossover,
        detect_rsi_signal,
        detect_price_spike,
        detect_momentum,
        detect_volatility,
    ]

    for detector in detectors:
        try:
            result = detector(prices)
            if result:
                signals.append(result)
        except Exception as e:
            print(f"[SIGNAL ERROR] {detector.__name__}: {e}")

    return signals


# ---------------------------------------------------------
# PERSISTENCE
# ---------------------------------------------------------
def create_signal(
    db: Session,
    asset_id: int,
    signal_data: Dict[str, Any],
) -> MarketSignal:

    detected_at = signal_data.get("detected_at") or datetime.now(timezone.utc)

    signal = MarketSignal(
        asset_id=asset_id,
        decision_id=signal_data.get("decision_id"),
        signal_type=signal_data["signal_type"],
        strength=signal_data["strength"],
        signal_metadata=signal_data.get("metadata"),
        detected_at=detected_at,
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    return signal