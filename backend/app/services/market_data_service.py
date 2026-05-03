from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal

from app.models.asset import Asset
from app.models.market_price import MarketPrice
from app.integrations.coingecko import fetch_market_prices


def ingest_market_data(db: Session):
    """
    Fetch market data from CoinGecko and store in DB
    """

    # -----------------------------------
    # Load assets from DB
    # -----------------------------------
    assets = db.query(Asset).all()

    if not assets:
        print("[WARN] No assets found")
        return []

    asset_symbols = [a.symbol for a in assets]

    # -----------------------------------
    # Fetch market prices
    # -----------------------------------
    data = fetch_market_prices(asset_symbols)

    if not data:
        print("[WARN] No market data returned")
        return []

    # -----------------------------------
    # Build lookup map
    # -----------------------------------
    asset_map = {a.symbol: a for a in assets}

    created = []

    # -----------------------------------
    # Insert price records
    # -----------------------------------
    for item in data:
        symbol = item["symbol"]
        price = Decimal(str(item["price_usd"]))

        asset = asset_map.get(symbol)

        if not asset:
            print(f"[SKIP] Unknown asset: {symbol}")
            continue

        market_price = MarketPrice(
            asset_id=asset.id,
            price_usd=price,
            observed_at=datetime.now(timezone.utc),
        )

        db.add(market_price)
        created.append(market_price)

        print(f"[INGEST] {symbol} → {price}")

    # -----------------------------------
    # Single commit (IMPORTANT)
    # -----------------------------------
    db.commit()

    return created