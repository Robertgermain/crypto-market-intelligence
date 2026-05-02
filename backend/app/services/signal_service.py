from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.market_price import MarketPrice
from app.models.market_signal import MarketSignal


# ---------------------------------------------------------
# CORE CALCULATION
# ---------------------------------------------------------
def calculate_price_change_percent(
    old_price: Decimal,
    new_price: Decimal
) -> Decimal:
    """
    Calculate percentage change between two prices.
    """

    if old_price == 0:
        return Decimal("0")

    return ((new_price - old_price) / old_price) * 100


# ---------------------------------------------------------
# SIGNAL DETECTION (PURE LOGIC)
# ---------------------------------------------------------
def detect_price_spike(
    prices: List[MarketPrice],
    threshold: Decimal = Decimal("5.0")
) -> Optional[Dict[str, Any]]:
    """
    Detects a price spike based on percentage change.

    Assumes:
    - prices are ordered oldest → newest
    """

    if len(prices) < 2:
        return None

    old_price = prices[0].price_usd
    new_price = prices[-1].price_usd

    percent_change = calculate_price_change_percent(old_price, new_price)

    if percent_change >= threshold:
        return {
            "signal_type": "price_spike",
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
# PERSISTENCE LAYER (DB WRITE)
# ---------------------------------------------------------
def create_signal(
    db: Session,
    asset_id: int,
    signal_data: Dict[str, Any],
) -> MarketSignal:
    """
    Persist a detected signal into the database.
    """

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