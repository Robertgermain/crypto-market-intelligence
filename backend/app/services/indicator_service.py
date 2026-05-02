from decimal import Decimal
from typing import List

from app.models.market_price import MarketPrice


def calculate_rsi(prices: List[MarketPrice], period: int = 14) -> Decimal | None:
    """
    Calculate RSI using closing prices
    """

    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    # -----------------------------------
    # Calculate price changes
    # -----------------------------------
    for i in range(1, len(prices)):
        change = prices[i].price_usd - prices[i - 1].price_usd

        if change > 0:
            gains.append(change)
            losses.append(Decimal("0"))
        else:
            gains.append(Decimal("0"))
            losses.append(abs(change))

    # -----------------------------------
    # Initial averages
    # -----------------------------------
    avg_gain = sum(gains[:period]) / Decimal(period)
    avg_loss = sum(losses[:period]) / Decimal(period)

    if avg_loss == 0:
        return Decimal("100")

    rs = avg_gain / avg_loss
    rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))

    return rsi