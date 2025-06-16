import hashlib
import hmac
import time
import requests
import logging
import json # Ensure json is imported

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BYBIT_MERCHANT_BASE_URL = "https://api.bybit.com" # Or https://api-testnet.bybit.com if on testnet

def _generate_signature(api_key: str, api_secret: str, params: dict) -> str:
    """
    Generates the HMAC SHA256 signature for Bybit Merchant API requests.
    Parameters should be sorted alphabetically and then URL-encoded.
    """
    # Sort parameters alphabetically
    sorted_params = sorted(params.items())
    
    # Concatenate key=value pairs
    query_string = "&".join([f"{key}={value}" for key, value in sorted_params])
    
    # Generate signature
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def _make_request(method: str, endpoint: str, api_key: str, api_secret: str, params: dict = None, timeout: int = 15) -> tuple[dict, str | None]:
    """
    Helper function to make signed requests to Bybit Merchant API.
    Returns (result_dict, None) on success, or (None, error_message) on failure.
    Includes explicit timeout.
    """
    if params is None:
        params = {}

    # Add common parameters
    params['api_key'] = api_key
    params['timestamp'] = int(time.time() * 1000) # Milliseconds
    params['recvWindow'] = 5000 # Max 60000 (ms)

    # Generate signature
    params['sign'] = _generate_signature(api_key, api_secret, params)

    url = f"{BYBIT_MERCHANT_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params, timeout=timeout) # Explicit timeout
        elif method.upper() == 'POST':
            response = requests.post(url, data=params, timeout=timeout) # Explicit timeout
        else:
            error_msg = f"Unsupported HTTP method: {method}"
            logging.error(error_msg)
            return (None, error_msg)

        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if data.get("retCode") == 0:
            logging.info(f"Bybit Merchant API response for {endpoint}: {data.get('retMsg', 'Success')}")
            return (data.get("result"), None)
        else:
            error_msg = f"Bybit Merchant API error for {endpoint}. Code: {data.get('retCode')}, Message: {data.get('retMsg')}, Raw: {data}"
            logging.error(f"❌ {error_msg}")
            # Specific check for API key issues
            if "key" in str(data.get("retMsg", "")).lower() or data.get("retCode") in [10001, 30001]: # Example common error codes
                error_msg += ". Possible API Key/Secret issue or permission error."
            return (None, error_msg)

    except requests.exceptions.Timeout:
        error_msg = f"Bybit Merchant API request to {endpoint} timed out after {timeout} seconds."
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Bybit Merchant API connection error to {endpoint}: {e}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Bybit Merchant API HTTP error for {endpoint}: {e}. Response: {e.response.text}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except json.JSONDecodeError:
        error_msg = f"Failed to decode JSON from Bybit Merchant API response for {endpoint}. Raw: {response.text}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred during Bybit Merchant API request to {endpoint}: {e}"
        logging.error(f"❌ {error_msg}", exc_info=True)
        return (None, error_msg)

def get_counterparty_payment_details(order_no: str, api_key: str, api_secret: str, timeout: int = 15) -> tuple[dict, str | None]:
    """
    Fetches counterparty (seller) payment details for a specific P2P order.
    Returns (details_dict, None) on success, or (None, error_message) on failure.
    """
    endpoint = "/fiat/v1/private/trade/order-detail"
    params = {
        "orderNo": order_no
    }
    logging.info(f"Fetching counterparty payment details for order {order_no}...")
    result, error_msg = _make_request('GET', endpoint, api_key, api_secret, params, timeout=timeout)
    if result:
        trade_details = result.get("tradeDetails")
        if trade_details:
            return ({
                "accountNumber": trade_details.get("accountNo"),
                "bankName": trade_details.get("bankName"),
                "accountHolderName": trade_details.get("accountHolderName")
            }, None)
    
    final_error = error_msg if error_msg else f"Could not retrieve complete counterparty payment details for order {order_no}."
    logging.error(f"Could not retrieve counterparty payment details for order {order_no}. Reason: {final_error}")
    return (None, final_error)


def mark_order_as_paid(order_no: str, api_key: str, api_secret: str, timeout: int = 15) -> tuple[bool, str | None]:
    """
    Marks a P2P order as paid.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    endpoint = "/fiat/v1/private/trade/paid"
    params = {
        "orderNo": order_no
    }
    logging.info(f"Marking order {order_no} as paid...")
    result, error_msg = _make_request('POST', endpoint, api_key, api_secret, params, timeout=timeout)
    if result is not None: 
        return (True, None)
    
    final_error = error_msg if error_msg else f"Failed to mark order {order_no} as paid."
    logging.error(final_error)
    return (False, final_error)

