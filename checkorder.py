import requests
import logging
import json # Ensure json is imported here too for potential future uses

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BYBIT_P2P_BASE_URL = "https://api.bybit.com" # Use "https://api-testnet.bybit.com" for testnet

def get_p2p_offers(crypto: str = "USDT", fiat: str = "NGN", side: str = "Buy", payment_method: str = "Bank Transfer") -> tuple[list, str | None]:
    """
    Fetches P2P offers from Bybit.
    Returns (list_of_offers, None) on success, or (None, error_message) on failure.
    Includes explicit timeout.
    """
    endpoint = "/fiat/v1/public/ads"
    params = {
        "page": 1,
        "limit": 50, # Get up to 50 offers
        "tokenId": crypto,
        "currencyId": fiat,
        "side": side,
        "payment": payment_method # Filters by payment method
    }
    url = f"{BYBIT_P2P_BASE_URL}{endpoint}"

    logging.info(f"Fetching {side} {crypto}/{fiat} P2P offers with {payment_method}...")
    try:
        response = requests.get(url, params=params, timeout=10) # Explicit timeout: 10 seconds
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data.get("code") == 0:
            offers = data.get("result", {}).get("items", [])
            logging.info(f"Successfully retrieved {len(offers)} P2P offers.")
            return (offers, None)
        else:
            error_msg = f"Bybit P2P API error. Code: {data.get('code')}, Message: {data.get('message', 'Unknown error')}, Raw: {data}"
            logging.error(f"❌ {error_msg}")
            return (None, error_msg)

    except requests.exceptions.Timeout:
        error_msg = f"Bybit P2P API request to {url} timed out after 10 seconds."
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Bybit P2P API connection error to {url}: {e}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Bybit P2P API HTTP error for {url}: {e}. Response: {e.response.text}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred while fetching P2P offers: {e}"
        logging.error(f"❌ {error_msg}", exc_info=True)
        return (None, error_msg)

