import requests
import logging
import hashlib
import hmac
import time
import json # CRITICAL: Ensure json is imported!

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BYBIT_TRADE_BASE_URL = "https://api.bybit.com" # Use "https://api-testnet.bybit.com" for testnet

def _generate_signature_for_unified_api(api_key: str, api_secret: str, params: dict) -> str:
    """
    Generates the HMAC SHA256 signature for Bybit Unified API (which P2P trade APIs fall under).
    For Fiat API, the signature is based on sorted key=value pairs of the *request body*.
    """
    # Sort body params alphabetically for signature generation
    sorted_body_params = sorted(params.items())
    query_string_for_signing = "&".join([f"{key}={value}" for key, value in sorted_body_params])
    
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string_for_signing.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def place_p2p_order(offer_id: str, amount_fiat: float, api_key: str, api_secret: str) -> tuple[dict, str | None]:
    """
    Places a P2P order on Bybit.
    Returns (order_details_dict, None) on success, or (None, error_message) on failure.
    Includes explicit timeout.
    """
    endpoint = "/fiat/v1/private/trade/order" # This is the specific P2P order endpoint
    url = f"{BYBIT_TRADE_BASE_URL}{endpoint}"

    # Parameters to be sent in the request body, including auth params for signing
    body_params = {
        "advNo": offer_id,
        "amount": str(amount_fiat), # Amount should be a string for Bybit API
        "api_key": api_key,
        "timestamp": int(time.time() * 1000), # Milliseconds
        "recvWindow": 5000 # Max 60000 (ms)
    }
    
    # Generate signature from the body_params
    body_params['sign'] = _generate_signature_for_unified_api(api_key, api_secret, body_params)

    headers = {
        "Content-Type": "application/json"
    }

    logging.info(f"Placing P2P order with offer {offer_id} for {amount_fiat} NGN...")
    try:
        # Send all body_params as JSON in the request body
        response = requests.post(url, json=body_params, headers=headers, timeout=15) # Explicit timeout: 15 seconds
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0:
            order_info = data.get("result", {})
            logging.info(f"Successfully placed P2P order: {order_info.get('orderNo')}")
            return (order_info, None)
        else:
            error_msg = f"Bybit P2P Order API error. Code: {data.get('code')}, Message: {data.get('message', 'Unknown error')}, Raw: {data}"
            logging.error(f"❌ {error_msg}")
            return (None, error_msg)

    except requests.exceptions.Timeout:
        error_msg = f"Bybit P2P Order API request to {url} timed out after 15 seconds."
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Bybit P2P Order API connection error to {url}: {e}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Bybit P2P Order API HTTP error for {url}: {e}. Response: {e.response.text}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred while placing P2P order: {e}"
        logging.error(f"❌ {error_msg}", exc_info=True)
        return (None, error_msg)

