import requests
from sqlalchemy.orm import Session

from app.models.asset import Asset

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"


def seed_assets_from_coingecko(db: Session, limit: int = 10):
    """
    Populate assets table from CoinGecko (top coins by market cap)
    """

    try:
        response = requests.get(
            COINGECKO_URL,
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
            },
            timeout=10,
        )

        response.raise_for_status()
        coins = response.json()

        # -----------------------------------
        # Preload existing assets
        # -----------------------------------
        existing_assets = db.query(Asset).all()
        existing_symbols = {a.symbol for a in existing_assets}

        created = []

        # -----------------------------------
        # Insert new assets
        # -----------------------------------
        for coin in coins:
            coin_id = coin["id"]

            if coin_id in existing_symbols:
                continue

            asset = Asset(
                symbol=coin["id"],
                name=coin["name"],  # 🔥 REQUIRED (fixes your error)
                is_active=True
            )

            db.add(asset)
            created.append(asset)

            print(f"[ADDED] {coin['id']} ({coin['name']})")

        db.commit()

        print(f"[SUCCESS] Seeded {len(created)} assets")

        return created

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed assets: {e}")
        return []