import time
import requests
from typing import List, Dict


COINGECKO_API_URL = "https://api.coingecko.com/api/v3"


# =========================================================
# EXISTING: SIMPLE PRICE (KEEP FOR FLEXIBILITY)
# =========================================================
def fetch_market_prices(
    assets: List[str],
    retries: int = 3,
    backoff_factor: int = 2
) -> List[Dict]:
    """
    Fetch specific asset prices (simple/price endpoint)

    NOTE:
    - Only returns valid CoinGecko IDs
    - Silently ignores invalid ones
    """

    ids = ",".join(assets)

    for attempt in range(retries):
        try:
            response = requests.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={
                    "ids": ids,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true"
                },
                timeout=10
            )

            # -----------------------------
            # Rate limit handling
            # -----------------------------
            if response.status_code == 429:
                wait_time = backoff_factor ** attempt
                print(f"[RATE LIMIT] Attempt {attempt+1}: retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            results = []

            for asset_id, values in data.items():
                results.append({
                    "symbol": asset_id,
                    "price_usd": values["usd"],
                    "change_24h": values.get("usd_24h_change", 0)
                })

            print(f"[COINGECKO] simple/price returned {len(results)} assets")

            return results

        except requests.RequestException as e:
            wait_time = backoff_factor ** attempt
            print(f"[API ERROR] Attempt {attempt+1}: {e} | retrying in {wait_time}s...")
            time.sleep(wait_time)

    print("[FAILURE] simple/price failed after retries")
    return []


# =========================================================
# NEW: TOP MARKET COINS (THIS IS WHAT YOU NEED)
# =========================================================
def fetch_top_market_coins(
    limit: int = 20,
    retries: int = 3,
    backoff_factor: int = 2
) -> List[Dict]:
    """
    Fetch TOP coins by market cap (coins/markets endpoint)

    THIS SHOULD BE YOUR PRIMARY DATA SOURCE
    """

    for attempt in range(retries):
        try:
            response = requests.get(
                f"{COINGECKO_API_URL}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": limit,
                    "page": 1,
                },
                timeout=10
            )

            # -----------------------------
            # Rate limit handling
            # -----------------------------
            if response.status_code == 429:
                wait_time = backoff_factor ** attempt
                print(f"[RATE LIMIT] Attempt {attempt+1}: retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            results = []

            for coin in data:
                results.append({
                    "symbol": coin["id"],
                    "name": coin["name"],
                    "price_usd": coin["current_price"],
                    "market_cap": coin.get("market_cap"),
                    "volume_24h": coin.get("total_volume"),
                    "change_24h": coin.get("price_change_percentage_24h"),
                })

            print(f"[COINGECKO] coins/markets returned {len(results)} assets")

            return results

        except requests.RequestException as e:
            wait_time = backoff_factor ** attempt
            print(f"[API ERROR] Attempt {attempt+1}: {e} | retrying in {wait_time}s...")
            time.sleep(wait_time)

    print("[FAILURE] coins/markets failed after retries")
    return []