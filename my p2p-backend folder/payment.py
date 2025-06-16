import requests
import json
import logging
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PAYSTACK_BASE_URL = "https://api.paystack.co"

def send_payment(account_number: str, bank_code: str, amount: float, paystack_secret_key: str, timeout: int = 20) -> tuple[str | None, str | None]:
    """
    Initiates a bank transfer via Paystack's Transfers API.
    Returns (Paystack_transfer_code, None) on success, or (None, error_message) on failure.
    Includes explicit timeout for all API calls.
    """
    headers = {
        "Authorization": f"Bearer {paystack_secret_key}",
        "Content-Type": "application/json"
    }

    # --- Step 1: Verify Bank Account (Recommended) ---
    logging.info(f"Verifying account {account_number} for bank code {bank_code} with Paystack...")
    resolve_account_url = f"{PAYSTACK_BASE_URL}/bank/resolve?account_number={account_number}&bank_code={bank_code}"
    try:
        response = requests.get(resolve_account_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        resolve_data = response.json()

        if resolve_data.get("status") and resolve_data["data"]["account_name"]:
            resolved_account_name = resolve_data["data"]["account_name"]
            logging.info(f"Account resolved: {resolved_account_name}")
        else:
            error_msg = f"Paystack account resolution failed for {account_number} (Bank: {bank_code}). Message: {resolve_data.get('message', 'Unknown error')}, Status: {resolve_data.get('status')}"
            logging.error(f"❌ {error_msg}")
            # Specific check for API key issues
            if "authorization" in str(resolve_data.get("message", "")).lower() or response.status_code == 401:
                error_msg += ". Possible Paystack Secret Key issue or invalid permissions."
            return (None, error_msg)
    except requests.exceptions.Timeout:
        error_msg = f"Paystack account resolution timed out after {timeout} seconds."
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Paystack account resolution connection error: {e}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Paystack account resolution HTTP error: {e}. Response: {e.response.text}"
        logging.error(f"❌ {error_msg}")
        # Specific check for API key issues from HTTP status
        if e.response.status_code == 401:
            error_msg += ". Possible Paystack Secret Key issue or invalid permissions."
        return (None, error_msg)
    except json.JSONDecodeError:
        error_msg = f"Failed to decode JSON from Paystack account resolution response. Raw: {response.text}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred during Paystack account resolution: {e}"
        logging.error(f"❌ {error_msg}", exc_info=True)
        return (None, error_msg)


    # --- Step 2: Create Transfer Recipient ---
    recipient_url = f"{PAYSTACK_BASE_URL}/transferrecipient"
    recipient_payload = {
        "type": "nuban",
        "name": resolved_account_name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": "NGN"
    }

    logging.info(f"Creating Paystack transfer recipient for {account_number}...")
    try:
        response = requests.post(recipient_url, json=recipient_payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        recipient_data = response.json()

        if recipient_data.get("status") and recipient_data.get("data", {}).get("recipient_code"):
            recipient_code = recipient_data["data"]["recipient_code"]
            logging.info(f"Paystack recipient created. Recipient Code: {recipient_code}.")
        else:
            error_msg = f"Failed to create Paystack transfer recipient for {account_number}. Message: {recipient_data.get('message', 'Unknown error')}, Details: {recipient_data}"
            logging.error(f"❌ {error_msg}")
            # Specific check for API key issues
            if "authorization" in str(recipient_data.get("message", "")).lower() or response.status_code == 401:
                error_msg += ". Possible Paystack Secret Key issue or invalid permissions."
            return (None, error_msg)
    except requests.exceptions.Timeout:
        error_msg = f"Paystack recipient creation timed out after {timeout} seconds."
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Paystack recipient creation connection error: {e}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Paystack recipient creation HTTP error: {e}. Response: {e.response.text}"
        logging.error(f"❌ {error_msg}")
        # Specific check for API key issues from HTTP status
        if e.response.status_code == 401:
            error_msg += ". Possible Paystack Secret Key issue or invalid permissions."
        return (None, error_msg)
    except json.JSONDecodeError:
        error_msg = f"Failed to decode JSON from Paystack recipient creation response. Raw: {response.text}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred during Paystack recipient creation: {e}"
        logging.error(f"❌ {error_msg}", exc_info=True)
        return (None, error_msg)

    # --- Step 3: Initiate Transfer ---
    transfer_url = f"{PAYSTACK_BASE_URL}/transfer"
    transfer_reference = str(uuid.uuid4()) 

    transfer_payload = {
        "source": "balance",
        "amount": int(amount * 100), # Amount in kobo
        "recipient": recipient_code,
        "reason": "P2P Bot Payout",
        "reference": transfer_reference,
    }

    logging.info(f"Initiating Paystack transfer of {amount} NGN to recipient code {recipient_code} with reference {transfer_reference}...")
    try:
        response = requests.post(transfer_url, json=transfer_payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        transfer_data = response.json()

        if transfer_data.get("status"):
            transfer_status = transfer_data.get("data", {}).get("status")
            transfer_code = transfer_data.get("data", {}).get("transfer_code")
            logging.info(f"Paystack transfer initiated. Status: {transfer_status}, Transfer Code: {transfer_code}, Message: {transfer_data.get('message')}")
            return (transfer_code, None)
        else:
            error_msg = f"Paystack transfer failed. Message: {transfer_data.get('message', 'Unknown error')}, Details: {transfer_data}"
            logging.error(f"❌ {error_msg}")
            # Specific check for API key issues
            if "authorization" in str(transfer_data.get("message", "")).lower() or response.status_code == 401:
                error_msg += ". Possible Paystack Secret Key issue or invalid permissions."
            return (None, error_msg)

    except requests.exceptions.Timeout:
        error_msg = f"Paystack transfer timed out after {timeout} seconds."
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Paystack transfer connection error: {e}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Paystack transfer HTTP error: {e}. Response: {e.text}"
        logging.error(f"❌ {error_msg}")
        # Specific check for API key issues from HTTP status
        if e.response.status_code == 401:
            error_msg += ". Possible Paystack Secret Key issue or invalid permissions."
        return (None, error_msg)
    except json.JSONDecodeError:
        error_msg = f"Failed to decode JSON response from Paystack. Raw: {response.text}"
        logging.error(f"❌ {error_msg}")
        return (None, error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred in send_payment (Paystack): {e}"
        logging.error(f"❌ {error_msg}", exc_info=True)
        return (None, error_msg)

