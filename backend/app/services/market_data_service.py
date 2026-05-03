from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal
import json

from app.models.asset import Asset
from app.models.market_price import MarketPrice
from app.integrations.coingecko import fetch_top_market_coins
from app.core.redis import redis_conn


def ingest_market_data(db: Session, limit: int = 20):
    """
    Fetch top market coins → cache in Redis → store in DB

    Flow:
    Redis → CoinGecko → PostgreSQL
    """

    # -----------------------------------
    # 1. Redis Cache Lookup
    # -----------------------------------
    cache_key = f"top_market_coins:{limit}"

    cached = redis_conn.get(cache_key)

    if cached:
        print("[REDIS] Using cached market data")

        try:
            data = json.loads(cached.decode("utf-8"))
        except Exception:
            print("[WARN] Failed to decode Redis cache — refetching")
            data = []
    else:
        data = []

    # -----------------------------------
    # 2. Fetch from API if needed
    # -----------------------------------
    if not data:
        print("[API] Fetching from CoinGecko")

        data = fetch_top_market_coins(limit=limit)

        if not data:
            print("[WARN] No market data returned")
            return []

        # Store in Redis (TTL shorter than scheduler interval)
        redis_conn.setex(
            cache_key,
            30,  # 🔥 30s TTL (important)
            json.dumps(data)
        )

    created = []

    # -----------------------------------
    # 3. Build Asset Map (OPTIMIZATION)
    # -----------------------------------
    existing_assets = db.query(Asset).all()
    asset_map = {a.symbol: a for a in existing_assets}

    # -----------------------------------
    # 4. Process Each Coin
    # -----------------------------------
    for item in data:
        symbol = item["symbol"]
        name = item["name"]
        price = Decimal(str(item["price_usd"]))

        # -----------------------------------
        # 4A. UPSERT ASSET
        # -----------------------------------
        asset = asset_map.get(symbol)

        if not asset:
            asset = Asset(
                symbol=symbol,
                name=name,
                is_active=True,
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)

            asset_map[symbol] = asset

            print(f"[ASSET CREATED] {symbol} ({name})")

        # -----------------------------------
        # 4B. INSERT PRICE SNAPSHOT
        # -----------------------------------
        market_price = MarketPrice(
            asset_id=asset.id,
            price_usd=price,
            observed_at=datetime.now(timezone.utc),
        )

        db.add(market_price)
        created.append(market_price)

        print(f"[INGEST] {symbol} → {price}")

    # -----------------------------------
    # 5. COMMIT ALL PRICES
    # -----------------------------------
    db.commit()

    print(f"[SUCCESS] Ingested {len(created)} price records")

    return created