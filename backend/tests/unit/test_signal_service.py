from decimal import Decimal
from datetime import datetime, timezone

from app.models.market_price import MarketPrice
from app.services.signal_service import detect_price_spike


def create_price(price: str):
    return MarketPrice(
        price_usd=Decimal(price),
        observed_at=datetime.now(timezone.utc)
    )


def test_price_spike_detected():
    prices = [
        create_price("100"),
        create_price("108")
    ]

    result = detect_price_spike(prices, threshold=Decimal("5.0"))

    assert result is not None
    assert result["signal_type"] == "price_spike"


def test_no_spike_detected():
    prices = [
        create_price("100"),
        create_price("102")
    ]

    result = detect_price_spike(prices, threshold=Decimal("5.0"))

    assert result is None