import requests
from typing import List, Dict


COINGECKO_API_URL = "https://api.coingecko.com/api/v3"


def fetch_market_prices(assets: List[str]) -> List[Dict]:
    """
    Fetch current market prices from CoinGecko
    """

    ids = ",".join(assets)

    response = requests.get(
        f"{COINGECKO_API_URL}/simple/price",
        params={
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for asset_id, values in data.items():
        results.append({
            "symbol": asset_id,
            "price_usd": values["usd"],
            "change_24h": values.get("usd_24h_change", 0)
        })

    return results