import time
import requests
from typing import List, Dict


COINGECKO_API_URL = "https://api.coingecko.com/api/v3"


def fetch_market_prices(
    assets: List[str],
    retries: int = 3,
    backoff_factor: int = 2
) -> List[Dict]:
    """
    Fetch current market prices from CoinGecko
    with retry + exponential backoff
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
            # Handle Rate Limiting (429)
            # -----------------------------
            if response.status_code == 429:
                wait_time = backoff_factor ** attempt
                print(f"[RATE LIMIT] Attempt {attempt+1}: retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            # Raise other HTTP errors
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

        # -----------------------------
        # Network / Request Errors
        # -----------------------------
        except requests.RequestException as e:
            wait_time = backoff_factor ** attempt
            print(f"[API ERROR] Attempt {attempt+1}: {e} | retrying in {wait_time}s...")
            time.sleep(wait_time)

    # -----------------------------
    # Final failure
    # -----------------------------
    print("[FAILURE] Max retries reached. Returning empty result.")
    return []