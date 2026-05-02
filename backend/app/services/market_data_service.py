from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal

from app.models.asset import Asset
from app.models.market_price import MarketPrice
from app.integrations.coingecko import fetch_market_prices


def ingest_market_data(db: Session, assets: list[str]):
    """
    Fetch market data → store in DB
    (NO QUEUE LOGIC HERE)
    """

    data = fetch_market_prices(assets)

    created = []

    for item in data:
        symbol = item["symbol"]
        price = Decimal(str(item["price_usd"]))

        asset = db.query(Asset).filter(Asset.symbol == symbol).first()

        if not asset:
            continue

        market_price = MarketPrice(
            asset_id=asset.id,
            price_usd=price,
            observed_at=datetime.now(timezone.utc)  # modern + correct
        )

        db.add(market_price)
        db.commit()
        db.refresh(market_price)

        created.append(market_price)

    return created