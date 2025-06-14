import os
import sys
import logging
import random
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from functools import wraps


print("--- app.py execution started! (Final Stable Version) ---")

# --- Ensure parent directory is in path to import bot modules ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- Configuration and Data File Paths ---
CONFIG_FILE = os.path.join(current_dir, 'config.json')
USERS_FILE = os.path.join(current_dir, 'users.json')
ORDERS_FILE = os.path.join(current_dir, 'orders.json')
PAYMENTS_FILE = os.path.join(current_dir, 'payments.json')
LOGS_FILE = os.path.join(current_dir, 'backend_logs.json')

# --- Load environment variables initially ---
load_dotenv()

# --- Hardcoded Admin User (For simplicity in this project) ---
ADMIN_USERNAME = "admin" 
# *** YOUR GENERATED SCRIPT HASH IS NOW EMBEDDED BELOW ***
# This hash corresponds to the password you used when generating it.
# Make sure to type that exact password (case-sensitive) on the login screen.
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$xlvsrD5vmfOHKS8N$46ba42001b5a3ee724f21a54257de34cbbf330e750bc31d424f3da5d98cf121f36427dc0f73c818b2b6ca2f15170733a307c54a21af8428daf09f3fac5b4c1b0"

# --- Global state for the backend ---
backend_config = {}
backend_users = []
backend_orders = []
backend_payments = []
backend_logs_list = []

backend_bot_status = "Idle"
backend_last_run_time = None
bot_thread = None
bot_should_stop = threading.Event()

# --- Helper Functions for JSON Persistence ---
def load_json_data(file_path, default_data=None):
    if default_data is None:
        default_data = []
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'lastRunTime' in data and data['lastRunTime'] is not None:
                    try:
                        data['lastRunTime'] = datetime.fromisoformat(data['lastRunTime'])
                    except ValueError:
                        pass
                if 'token_expiry' in data and data['token_expiry'] is not None:
                    try:
                        data['token_expiry'] = datetime.fromisoformat(data['token_expiry'])
                    except ValueError:
                        pass
                if file_path == ORDERS_FILE or file_path == PAYMENTS_FILE:
                    for item in data:
                        if 'timestamp' in item and item['timestamp'] is not None:
                            try:
                                item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                            except ValueError:
                                pass
                return data
        return default_data
    except json.JSONDecodeError as e:
        root_logger.error(f"Error decoding JSON from {file_path}: {e}. Returning default data.")
        return default_data
    except Exception as e:
        root_logger.error(f"Error loading data from {file_path}: {e}. Returning default data.")
        return default_data

def save_json_data(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=lambda o: o.isoformat() if isinstance(o, datetime) else o)
        root_logger.info(f"Data saved to {file_path}")
    except Exception as e:
        root_logger.error(f"Error saving data to {file_path}: {e}")

# --- Initial Load of Data on Backend Startup ---
backend_config = load_json_data(CONFIG_FILE, default_data={
    "bybitApiKey": os.getenv("BYBIT_API_KEY", ""),
    "bybitApiSecret": os.getenv("BYBIT_API_SECRET", ""),
    "paystackSecretKey": os.getenv("PAYSTACK_SECRET_KEY", ""),
    "runIntervalMinutes": 5,
    "lastRunTime": None,
    "email_alerts_enabled": False,
    "email_username": "",
    "email_password": "",
    "alert_recipient_email": "",
    "session_token": None,
    "token_expiry": None
})
backend_users = load_json_data(USERS_FILE, default_data=[
    {"id": "user1", "name": "Kuda Client A", "account": "1234567890", "bank": "50211", "amount": 5000.0},
    {"id": "user2", "name": "Moniepoint Client B", "account": "9876543210", "bank": "YOUR_MONIEPOINT_BANK_CODE", "amount": 10000.0},
])
backend_orders = load_json_data(ORDERS_FILE)
backend_payments = load_json_data(PAYMENTS_FILE)
backend_logs_list = load_json_data(LOGS_FILE, default_data=[])
backend_last_run_time = backend_config.get('lastRunTime')


# --- Configure Logging ---
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

for handler in root_logger.handlers[:]:
    if isinstance(handler, (logging.StreamHandler, logging.FileHandler, logging.handlers.RotatingFileHandler)):
        root_logger.removeHandler(handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
root_logger.addHandler(console_handler)

class ListHandler(logging.Handler):
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list
    def emit(self, record):
        msg = self.format(record)
        self.log_list.append(msg)
        if len(self.log_list) > 500:
            self.log_list.pop(0)

list_handler = ListHandler(backend_logs_list)
list_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
root_logger.addHandler(list_handler)


# --- Import bot functions ---
# These imports must be here after root_logger is defined
import checkorder
import placeorder
import payment
import bybit_merchant_p2p
import email_alerts
from main import users as main_users # Ensure main.py exists and exports 'users'

if not backend_users and main_users:
    backend_users.extend(main_users)
    save_json_data(USERS_FILE, backend_users)

app = Flask(__name__)
CORS(app) 


# --- Bank Name to Bank Code Mapping ---
NIGERIAN_BANK_CODES = {
    "ACCESS BANK": "044", "ZENITH BANK": "057", "GUARANTY TRUST BANK": "058", 
    "KUDA MICROFINANCE BANK": "50211", "FIRST BANK OF NIGERIA": "011",
    "UNION BANK OF NIGERIA": "032", "UNITED BANK FOR AFRICA": "033", 
    "STANBIC IBTC BANK": "221", "FIDELITY BANK": "070", "ECOBANK NIGERIA": "050",
    "KEYSTONE BANK": "082", "PROVIDUS BANK": "101", "WEMA BANK": "023",
    "POLARIS BANK": "076", "UNITY BANK": "215", "STERLING BANK": "232",
    "HERITAGE BANK": "063", "CITIBANK NIGERIA": "023", "JAIZ BANK": "301",
    "SUNTRUST BANK": "100", "FCMB": "214", "CORONATION MERCHANT BANK": "559",
    "FBNQUEST MERCHANT BANK": "560", "RAND MERCHANT BANK": "562",
    "STANDARD CHARTERED BANK": "068", "TITAN TRUST BANK": "102",
    "RUBY MICROFINANCE BANK": "50505",
}

def get_nigerian_bank_code(bybit_bank_name: str) -> str | None:
    if not bybit_bank_name: return None
    normalized_name = bybit_bank_name.upper().strip().replace(" PLC", "").replace(" LIMITED", "").replace(".", "")
    if "GTBANK" in normalized_name or "GUARANTY TRUST" in normalized_name: return "058"
    if "KUDA" in normalized_name: return "50211"
    if "UBA" in normalized_name or "UNITED BANK FOR AFRICA" in normalized_name: return "033"
    if "FCMB" in normalized_name or "FIRST CITY MONUMENT" in normalized_name: return "214"
    return NIGERIAN_BANK_CODES.get(normalized_name)


# --- Helper Function: select_suitable_offer ---
def select_suitable_offer(offers: list, desired_fiat_amount: float) -> dict | None:
    suitable_offers = []
    root_logger.info(f"Searching for an offer suitable for {desired_fiat_amount} NGN...")
    for offer in offers:
        try:
            min_amt = float(offer.get('minTradeAmount', 0))
            max_amt = float(offer.get('maxTradeAmount', float('inf')))
            price = float(offer.get('price', 0))
            crypto_amount_from_offer = desired_fiat_amount / price
            tradable_quantity = float(offer.get('tradableQuantity', 0))
            if min_amt <= desired_fiat_amount and desired_fiat_amount <= max_amt and \
               crypto_amount_from_offer <= tradable_quantity:
                suitable_offers.append(offer)
                root_logger.debug(f"Found suitable offer: Seller '{offer.get('nickName', 'N/A')}', Price: {price}, Limits: {min_amt}-{max_amt}")
            else:
                root_logger.debug(f"Offer from '{offer.get('nickName', 'N/A')}' (Price: {price}) has insufficient quantity or limits.")
        except (ValueError, TypeError) as e:
            root_logger.warning(f"Skipping offer due to invalid amount/price data: {offer}. Error: {e}")
            continue
    if not suitable_offers:
        root_logger.warning(f"No offers found that match the desired amount {desired_fiat_amount} NGN within their limits and tradable quantity.")
        return None
    suitable_offers.sort(key=lambda x: float(x.get('price', float('inf'))))
    best_offer = suitable_offers[0]
    root_logger.info(f"Selected best offer from '{best_offer.get('nickName', 'N/A')}' at price {best_offer.get('price')} for {desired_fiat_amount} NGN.")
    return best_offer

# --- Helper Function: safe_api_call (Modified to return error message) ---
def safe_api_call(api_func, *args, retries=3, delay=5, **kwargs) -> tuple[any, str | None]:
    """
    Attempts to call an API function with retries. Expected API function to return (result, error_message)
    Returns (result, error_message) or (None, error_message).
    """
    for attempt in range(1, retries + 1):
        if bot_should_stop.is_set():
            root_logger.info(f"Bot received stop signal during {api_func.__name__} retry loop. Halting API calls.")
            return (None, "Bot stopped by user during API call.")

        root_logger.info(f"Attempt {attempt}/{retries} to call {api_func.__name__}...")
        
        # API functions will now return (result, error_message)
        result, api_error_msg = api_func(*args, **kwargs) 
        
        if result is not None:
            root_logger.info(f"✅ {api_func.__name__} successful on attempt {attempt}.")
            return (result, None)
        else:
            full_error_msg = f"❌ {api_func.__name__} failed on attempt {attempt}. Reason: {api_error_msg or 'No specific error message provided.'}"
            if attempt < retries:
                root_logger.warning(f"{full_error_msg} Retrying in {delay} seconds...")
                for _ in range(delay):
                    if bot_should_stop.is_set():
                        root_logger.info(f"Bot received stop signal during {api_func.__name__} delay. Halting API calls.")
                        return (None, "Bot stopped by user during API call retry delay.")
                    time.sleep(1)
            else:
                root_logger.error(f"{full_error_msg} after {retries} attempts.")
                return (None, f"API call failed after {retries} attempts. Last reason: {api_error_msg or 'No specific error message.'}")
    return (None, f"API call failed after {retries} attempts.") # Should be caught by the above return, but as fallback

# --- Function to send critical email alerts ---
def send_critical_alert(subject: str, message: str):
    if backend_config.get("email_alerts_enabled"):
        sender_email = backend_config.get("email_username")
        sender_password = backend_config.get("email_password")
        recipient_email = backend_config.get("alert_recipient_email")
        email_alerts.send_alert_email(sender_email, sender_password, recipient_email, subject, message)
    else:
        root_logger.info("Email alerts are disabled in config. Not sending alert.")


# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            root_logger.warning("Attempted unauthorized access: Missing Authorization header.")
            return jsonify({"message": "Authorization token is missing!"}), 401
        
        try:
            token = auth_header.split("Bearer ")[1]
        except IndexError:
            root_logger.warning("Attempted unauthorized access: Invalid Authorization header format.")
            return jsonify({"message": "Invalid token format."}), 401

        stored_token = backend_config.get('session_token')
        token_expiry = backend_config.get('token_expiry')

        if not stored_token or token != stored_token:
            root_logger.warning(f"Attempted unauthorized access: Invalid token provided. Provided: {token[:5]}..., Expected: {stored_token[:5]}...")
            return jsonify({"message": "Invalid token."}), 401
        
        if token_expiry and datetime.now() > token_expiry:
            root_logger.warning("Attempted unauthorized access: Token has expired.")
            backend_config['session_token'] = None
            backend_config['token_expiry'] = None
            save_json_data(CONFIG_FILE, backend_config)
            return jsonify({"message": "Token has expired."}), 401

        return f(*args, **kwargs)
    return decorated_function


# --- Background Bot Execution Logic ---
def run_bot_in_background():
    global backend_bot_status, backend_last_run_time, backend_orders, backend_payments, backend_config

    # Helper function to ensure graceful exit and save state
    def _exit_gracefully(status_override: str = None):
        # CORRECTED: Use 'global' for global variables
        global backend_bot_status, backend_last_run_time
        backend_bot_status = status_override if status_override else "Stopped"
        backend_last_run_time = datetime.now()
        backend_config['lastRunTime'] = backend_last_run_time
        save_json_data(CONFIG_FILE, backend_config)
        save_json_data(LOGS_FILE, backend_logs_list)
        root_logger.info(f"Bot thread exiting with status: {backend_bot_status}")


    root_logger.info("Bot run initiated by Flask endpoint in background thread.")
    backend_bot_status = "Running"
    bot_should_stop.clear()
    backend_last_run_time = None

    bybit_api_key = backend_config.get("bybitApiKey")
    bybit_api_secret = backend_config.get("bybitApiSecret")
    paystack_secret_key = backend_config.get("paystackSecretKey")
    run_interval_minutes = backend_config.get("runIntervalMinutes", 5)
    run_interval_seconds = run_interval_minutes * 60

    # Pre-check for critical API keys
    if not bybit_api_key or not bybit_api_secret:
        error_msg = "Bybit API keys are missing in config. Bot run aborted."
        root_logger.critical(error_msg)
        backend_bot_status = "Error (Missing Bybit Keys)" # Update status for frontend
        send_critical_alert("CRITICAL BOT ERROR: Missing Bybit API Keys", error_msg)
        _exit_gracefully("Error (Missing Bybit Keys)") # Force exit with specific error status
        return

    if not paystack_secret_key:
        error_msg = "Paystack Secret Key is missing in config. Bot run aborted."
        root_logger.critical(error_msg)
        backend_bot_status = "Error (Missing Paystack Key)" # Update status for frontend
        send_critical_alert("CRITICAL BOT ERROR: Missing Paystack Key", error_msg)
        _exit_gracefully("Error (Missing Paystack Key)") # Force exit with specific error status
        return
    
    while True: # Main loop for continuous bot operation
        if bot_should_stop.is_set():
            _exit_gracefully()
            return # Exit the thread function

        try:
            root_logger.info(f"--- Starting new bot cycle (Interval: {run_interval_minutes} minutes) ---")
            backend_bot_status = "Running (Fetching Offers)"
            
            root_logger.info("Attempting to fetch P2P offers from Bybit...")
            # All API calls now return (result, error_message)
            offers, error_msg = safe_api_call(checkorder.get_p2p_offers, crypto="USDT", fiat="NGN", side="Buy", payment_method="Bank Transfer")

            if bot_should_stop.is_set():
                root_logger.info("Bot stopped by user after fetching offers. Halting.")
                _exit_gracefully()
                return

            if not offers:
                if error_msg:
                    root_logger.error(f"No P2P offers found or failed to retrieve offers for this cycle. Reason: {error_msg}. Will retry in next cycle.")
                    backend_bot_status = f"Error (Offers: {error_msg})"
                    send_critical_alert("BOT ALERT: P2P Offer Fetch Failed", error_msg) # Alert for API issues
                else:
                    root_logger.error("No P2P offers found for this cycle. Will retry in next cycle.")
                    backend_bot_status = "Running (No Offers Found)" # No critical error, just no offers

            else: # Offers were successfully retrieved
                root_logger.info(f"Successfully retrieved {len(offers)} P2P offers from Bybit.")
                backend_bot_status = "Running (Processing Offers)"

                # Ensure backend_users is not empty before accessing index 0
                target_fiat_amount = backend_users[0]['amount'] if backend_users else 5000.0 
                if not backend_users:
                    root_logger.warning("No users configured in users.json. Using default target amount 5000.0 NGN.")


                selected_offer = select_suitable_offer(offers, target_fiat_amount)

                if not selected_offer:
                    root_logger.error("No suitable offer found for the target amount. Skipping Bybit purchase this cycle.")
                else:
                    offer_id = selected_offer.get('advNo')
                    trade_amount_ngn = float(selected_offer.get('minTradeAmount'))
                    root_logger.info(f"Chosen offer ID: {offer_id} (Seller: {selected_offer.get('nickName')}, Price: {selected_offer.get('price')}) for {trade_amount_ngn} NGN")

                    root_logger.info(f"Attempting to place P2P order on Bybit for offer ID: {offer_id} with amount: {trade_amount_ngn} NGN.")
                    
                    order_details, error_msg = safe_api_call(
                        placeorder.place_p2p_order,
                        offer_id,
                        trade_amount_ngn,
                        bybit_api_key,
                        bybit_api_secret,
                        retries=3, delay=5
                    )
                    if bot_should_stop.is_set() and order_details is None:
                        root_logger.info("Bot received stop signal during order placement. Halting.")
                        _exit_gracefully()
                        return

                    if order_details:
                        order_no = order_details.get('orderNo', 'N/A')
                        root_logger.info(f"✅ P2P Order '{order_no}' successfully placed for {trade_amount_ngn} NGN on Bybit.")
                        
                        new_order = {
                            "id": order_no,
                            "clientId": "Bybit Seller (Auto-Paid)",
                            "clientName": selected_offer.get('nickName', 'Bybit Seller'),
                            "amountFiat": trade_amount_ngn,
                            "amountCrypto": float(trade_amount_ngn) / float(selected_offer.get('price', 1)),
                            "sellerNickname": selected_offer.get('nickName', 'N/A'),
                            "status": "Order Placed, Getting Seller Details via API",
                            "bybitOrderId": order_no,
                            "paystackTxId": None,
                            "timestamp": datetime.now().isoformat()
                        }
                        backend_orders.append(new_order)
                        save_json_data(ORDERS_FILE, backend_orders)

                        root_logger.info(f"Attempting to get seller bank details for order {order_no} via Bybit Merchant API...")
                        backend_bot_status = "Running (Getting Seller Info via API)"
                        
                        seller_payment_details, error_msg = safe_api_call(
                            bybit_merchant_p2p.get_counterparty_payment_details,
                            order_no,
                            bybit_api_key,
                            bybit_api_secret,
                            retries=3, delay=5
                        )

                        if bot_should_stop.is_set() and seller_payment_details is None:
                            root_logger.info("Bot received stop signal during getting seller details. Halting.")
                            _exit_gracefully()
                            return

                        if seller_payment_details:
                            root_logger.info(f"✅ Successfully retrieved seller bank details via Bybit Merchant API for order {order_no}.")
                            
                            seller_account_number = seller_payment_details.get("accountNumber")
                            seller_bank_name_bybit = seller_payment_details.get("bank")  # Fixed typo: use correct key
                            seller_account_holder_name = seller_payment_details.get("accountHolderName")

                            seller_bank_code_for_paystack = get_nigerian_bank_code(seller_bank_name_bybit)

                            if not all([seller_account_number, seller_bank_name_bybit, seller_account_holder_name, seller_bank_code_for_paystack]):
                                error_reason = f"Incomplete seller payment details or unknown bank for order {order_no}. Bybit Bank Name: {seller_bank_name_bybit}, Paystack Code: {seller_bank_code_for_paystack}. MANUAL PAYMENT REQUIRED!"
                                root_logger.error(f"❌ {error_reason}")
                                send_critical_alert(f"BOT ALERT: Manual Bybit Payment Needed for Order {order_no}", error_reason)
                                for order in backend_orders:
                                    if order["bybitOrderId"] == order_no:
                                        order["status"] = "Incomplete Seller Details/Unknown Bank, Manual Payment Needed"
                                        break
                                save_json_data(ORDERS_FILE, backend_orders)
                            else:
                                root_logger.info(f"Attempting Paystack payment to Bybit seller: {seller_account_holder_name} ({seller_account_number}) at {seller_bank_name_bybit} (Code: {seller_bank_code_for_paystack}).")
                                
                                payment_to_seller_id, error_msg = safe_api_call(
                                    payment.send_payment,
                                    seller_account_number,
                                    seller_bank_code_for_paystack,
                                    trade_amount_ngn,
                                    paystack_secret_key,
                                    retries=3, delay=10
                                )

                                if bot_should_stop.is_set() and payment_to_seller_id is None:
                                    root_logger.info("Bot received stop signal during seller payment. Halting.")
                                    _exit_gracefully()
                                    return

                                if payment_to_seller_id:
                                    root_logger.info(f"✅ Payment sent to Bybit seller for order {order_no}! Paystack Transfer ID: {payment_to_seller_id}")
                                    
                                    root_logger.info(f"Attempting to mark order {order_no} as paid on Bybit via API...")
                                    backend_bot_status = "Running (Confirming Payment on Bybit via API)"

                                    mark_paid_success, error_msg = safe_api_call(
                                        bybit_merchant_p2p.mark_order_as_paid,
                                        order_no,
                                        bybit_api_key,
                                        bybit_api_secret,
                                        retries=3, delay=5
                                    )

                                    if bot_should_stop.is_set() and mark_paid_success is None:
                                        root_logger.info("Bot received stop signal during mark as paid. Halting.")
                                        _exit_gracefully()
                                        return

                                    if mark_paid_success:
                                        root_logger.info(f"✅ Order {order_no} successfully marked as paid on Bybit via API.")
                                        for order in backend_orders:
                                            if order["bybitOrderId"] == order_no:
                                                order["paystackTxId"] = payment_to_seller_id
                                                order["status"] = "Payment Sent & Confirmed on Bybit via API"
                                                break
                                    else:
                                        error_reason = f"Failed to mark order {order_no} as paid on Bybit via API. Reason: {error_msg or 'Unknown API issue'}. MANUAL CONFIRMATION REQUIRED ON BYBIT!"
                                        root_logger.error(f"❌ {error_reason}")
                                        send_critical_alert(f"BOT ALERT: Manual Bybit Confirmation Needed for Order {order_no}", error_reason)
                                        for order in backend_orders:
                                            if order["bybitOrderId"] == order_no:
                                                order["status"] = f"Payment Sent to Seller, MANUAL CONFIRMATION NEEDED on Bybit (Reason: {error_msg[:50]}...)"
                                                break
                                    
                                    new_payment_record = {
                                        "id": payment_to_seller_id,
                                        "clientId": "Bybit Seller",
                                        "clientName": selected_offer.get('nickName', 'Bybit Seller'),
                                        "amount": trade_amount_ngn,
                                        "bank": seller_bank_name_bybit,
                                        "status": "Success",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    backend_payments.append(new_payment_record)
                                    save_json_data(PAYMENTS_FILE, backend_payments)

                                else:
                                    error_reason = f"Paystack payment to Bybit seller for order {order_no} failed. Reason: {error_msg or 'Unknown Paystack issue'}. MANUAL INTERVENTION REQUIRED on Bybit!"
                                    root_logger.error(f"❌ {error_reason}")
                                    send_critical_alert(f"CRITICAL BOT ERROR: Paystack Payment to Seller Failed for Order {order_no}", error_reason)
                                    for order in backend_orders:
                                        if order["bybitOrderId"] == order_no:
                                            order["status"] = f"Payment to Seller Failed, Manual Intervention Needed (Reason: {error_msg[:50]}...)"
                                            break
                                    save_json_data(ORDERS_FILE, backend_orders)

                        else:
                            error_reason = f"Failed to get seller bank details for order {order_no} via Bybit API. Reason: {error_msg or 'Unknown API issue'}. Manual payment to seller will be required."
                            root_logger.error(f"❌ {error_reason}")
                            send_critical_alert(f"CRITICAL BOT ERROR: Failed to Get Seller Info via Bybit API for Order {order_no}", error_reason)
                            for order in backend_orders:
                                if order["bybitOrderId"] == order_no:
                                    order["status"] = f"Failed to Get Seller Info via API, Manual Payment Needed (Reason: {error_msg[:50]}...)"
                                    break
                            save_json_data(ORDERS_FILE, backend_orders)

                    else:
                        error_reason = f"Failed to place P2P order for {selected_offer.get('nickName')}. Reason: {error_msg or 'Unknown issue'}. See placeorder.py logs for details."
                        root_logger.error(f"❌ {error_reason}")
                        root_logger.warning(f"No order placed. Check Bybit API key permissions and your balance.")
                        send_critical_alert(f"CRITICAL BOT ERROR: P2P Order Placement Failed", error_reason)
                        
                root_logger.info("--- Starting client payouts for this cycle ---")
                backend_bot_status = "Running (Processing Client Payouts)"
                for user in backend_users:
                    if bot_should_stop.is_set():
                        root_logger.info(f"Bot stopped by user before processing {user.get('name', 'a user')}. Halting.")
                        _exit_gracefully()
                        return

                    user_amount = user["amount"]
                    user_account = user["account"]
                    user_bank_code = user["bank"]
                    user_name = user.get("name", "Unknown User")

                    root_logger.info(f"\n--- Processing Payout for Client: {user_name} ---")

                    payment_id, error_msg = safe_api_call(
                        payment.send_payment,
                        user_account,
                        user_bank_code,
                        user_amount,
                        paystack_secret_key,
                        retries=3, delay=10
                    )
                    
                    if bot_should_stop.is_set() and payment_id is None:
                        root_logger.info("Bot received stop signal during client payment. Halting.")
                        _exit_gracefully()
                        return

                    if payment_id:
                        root_logger.info(f"✅ Payment sent successfully to client {user_name}! Paystack Transfer ID: {payment_id}")
                            
                        new_payment = {
                            "id": payment_id,
                            "clientId": user.get('id', 'N/A'),
                            "clientName": user_name,
                            "amount": user_amount,
                            "bank": user_bank_code,
                            "status": "Success",
                            "timestamp": datetime.now().isoformat()
                        }
                        backend_payments.append(new_payment)
                        save_json_data(PAYMENTS_FILE, backend_payments)
                    else:
                        error_reason = f"Payout to client {user_name} failed. Reason: {error_msg or 'Unknown Paystack issue'}. Investigate payment.py logs and Paystack dashboard."
                        root_logger.error(f"❌ {error_reason}")
                        send_critical_alert(f"CRITICAL BOT ERROR: Client Payout Failed for {user_name}", error_reason)
                    
                    if bot_should_stop.is_set():
                        root_logger.info(f"Bot stopped by user after processing {user.get('name', 'a user')}. Halting.")
                        _exit_gracefully()
                        return
                    
                    for _ in range(2):
                        if bot_should_stop.is_set():
                            root_logger.info("Bot received stop signal during inter-client delay. Halting.")
                            _exit_gracefully()
                            return
                        time.sleep(1)


                root_logger.info("--- Bot Finished Processing All Users for this cycle ---")
                
            backend_last_run_time = datetime.now()
            backend_config['lastRunTime'] = backend_last_run_time
            save_json_data(CONFIG_FILE, backend_config)
            save_json_data(LOGS_FILE, backend_logs_list)

            root_logger.info(f"Waiting for {run_interval_minutes} minutes before next cycle...")
            backend_bot_status = f"Running (Sleeping for {run_interval_minutes}m)"
            
            total_sleep_seconds = int(run_interval_minutes * 60)
            for _ in range(total_sleep_seconds):
                if bot_should_stop.is_set():
                    root_logger.info("Bot received stop signal during main sleep interval. Halting.")
                    _exit_gracefully()
                    return
                time.sleep(1)

        except Exception as e:
            error_msg = f"Bot run encountered an unhandled critical error during a cycle: {e}"
            root_logger.exception(error_msg)
            backend_bot_status = "Error (Critical Unhandled)" # Update status for frontend
            send_critical_alert("CRITICAL BOT ERROR: Unhandled Exception", error_msg)
            _exit_gracefully("Error (Critical Unhandled)")
            
            root_logger.info("Waiting for 30 seconds before next cycle attempt after critical error...")
            backend_bot_status = "Error (Waiting to Retry After Critical Error)"
            for _ in range(30):
                if bot_should_stop.is_set():
                    root_logger.info("Bot received stop signal during error retry delay. Halting.")
                    _exit_gracefully()
                    return
                time.sleep(1)
    
# --- API Endpoints ---

@app.route('/')
def home():
    return "P2P Bot Backend is running!"

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Backend operational"}), 200

# Authentication Endpoints
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        session_token = str(uuid.uuid4())
        token_expiry = datetime.now() + timedelta(hours=24) 
        
        backend_config['session_token'] = session_token
        backend_config['token_expiry'] = token_expiry
        save_json_data(CONFIG_FILE, backend_config)
        
        root_logger.info(f"Admin user '{username}' logged in successfully.")
        return jsonify({"message": "Login successful", "token": session_token}), 200
    else:
        root_logger.warning(f"Failed login attempt for username: {username}")
        return jsonify({"message": "Invalid username or password"}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    backend_config['session_token'] = None
    backend_config['token_expiry'] = None
    save_json_data(CONFIG_FILE, backend_config)
    root_logger.info("User logged out successfully.")
    return jsonify({"message": "Logged out successfully"}), 200


@app.route('/api/status', methods=['GET'])
@login_required
def get_bot_status_endpoint():
    current_orders = load_json_data(ORDERS_FILE)
    current_payments = load_json_data(PAYMENTS_FILE)
    current_config = load_json_data(CONFIG_FILE, default_data={})

    last_run_iso = current_config.get('lastRunTime').isoformat() if isinstance(current_config.get('lastRunTime'), datetime) else current_config.get('lastRunTime')

    return jsonify({
        "status": backend_bot_status,
        "lastRunTime": last_run_iso,
        "numOrders": len(current_orders),
        "numPayments": len(current_payments)
    })

@app.route('/api/trigger-bot-run', methods=['POST'])
@login_required
def trigger_bot_run_endpoint():
    global backend_bot_status, bot_thread, bot_should_stop

    if backend_bot_status.startswith("Running") or backend_bot_status == "Stopping...":
        root_logger.warning(f"Attempted to start bot, but current status is '{backend_bot_status}'.")
        return jsonify({"message": "Bot is already running or stopping. Please wait."}), 409

    bot_should_stop.clear()
    
    # Ensure only one bot thread is running
    if bot_thread and bot_thread.is_alive():
        root_logger.warning("Bot thread already active. Not starting a new one.")
        return jsonify({"message": "Bot is already running. Not starting a new thread."}), 409

    bot_thread = threading.Thread(target=run_bot_in_background)
    bot_thread.daemon = True
    bot_thread.start()
    
    backend_bot_status = "Running"

    root_logger.info("Flask triggered bot run in background thread.")
    return jsonify({"message": "Bot run initiated successfully in background!"}), 200

@app.route('/api/stop-bot', methods=['POST'])
@login_required
def stop_bot_endpoint():
    global bot_should_stop, backend_bot_status
    if not (backend_bot_status.startswith("Running") or backend_bot_status.startswith("Error")):
        root_logger.warning(f"Attempted to stop bot, but it's not 'Running' or in an error state (current status: '{backend_bot_status}').")
        return jsonify({"message": "Bot is not currently running or is already stopped."}), 400
    
    if backend_bot_status == "Stopping...":
        root_logger.warning("Attempted to stop bot, but it is already in the process of stopping.")
        return jsonify({"message": "Bot is already stopping. Please wait."}), 400

    bot_should_stop.set()
    backend_bot_status = "Stopping..."
    root_logger.info("Stop signal sent to bot. It will halt shortly after current operation.")
    time.sleep(0.5)
    return jsonify({"message": "Stop signal sent to bot. It will halt shortly."}), 200


@app.route('/api/users', methods=['GET'])
@login_required
def get_users_endpoint():
    current_users = load_json_data(USERS_FILE, default_data=[])
    return jsonify(current_users)

@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders_endpoint():
    current_orders = load_json_data(ORDERS_FILE)
    return jsonify([
        {**order, 'timestamp': order['timestamp'].isoformat() if isinstance(order['timestamp'], datetime) else order['timestamp']}
        for order in current_orders
    ])

@app.route('/api/payments', methods=['GET'])
@login_required
def get_payments_endpoint():
    current_payments = load_json_data(PAYMENTS_FILE)
    return jsonify([
        {**payment, 'timestamp': payment['timestamp'].isoformat() if isinstance(payment['timestamp'], datetime) else payment['timestamp']}
        for payment in current_payments
    ])

@app.route('/api/logs', methods=['GET'])
@login_required
def get_logs_endpoint():
    return jsonify(backend_logs_list)

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config_endpoint():
    global backend_config

    if request.method == 'GET':
        display_config = {
            "bybitApiKey": backend_config.get("bybitApiKey", "")[:5] + "..." if backend_config.get("bybitApiKey") else "",
            "bybitApiSecret": backend_config.get("bybitApiSecret", "")[:5] + "..." if backend_config.get("bybitApiSecret") else "",
            "paystackSecretKey": backend_config.get("paystackSecretKey", "")[:5] + "..." if backend_config.get("paystackSecretKey") else "",
            "runIntervalMinutes": backend_config.get("runIntervalMinutes", 5),
            "lastRunTime": backend_config.get('lastRunTime').isoformat() if isinstance(backend_config.get('lastRunTime'), datetime) else backend_config.get('lastRunTime'),
            "email_alerts_enabled": backend_config.get("email_alerts_enabled", False),
            "email_username": backend_config.get("email_username", "")[:5] + "..." if backend_config.get("email_username") else "",
            "email_password": "..." if backend_config.get("email_password") else "",
            "alert_recipient_email": backend_config.get("alert_recipient_email", "")[:5] + "..." if backend_config.get("alert_recipient_email") else ""
        }
        return jsonify(display_config)
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Only update if new value is provided and not empty
        if data.get('bybitApiKey'): backend_config['bybitApiKey'] = data.get('bybitApiKey')
        if data.get('bybitApiSecret'): backend_config['bybitApiSecret'] = data.get('bybitApiSecret')
        if data.get('paystackSecretKey'): backend_config['paystackSecretKey'] = data.get('paystackSecretKey')
        
        if 'email_alerts_enabled' in data:
            backend_config['email_alerts_enabled'] = bool(data.get('email_alerts_enabled'))
        if data.get('email_username'): backend_config['email_username'] = data.get('email_username')
        if data.get('email_password'): backend_config['email_password'] = data.get('email_password')
        if data.get('alert_recipient_email'): backend_config['alert_recipient_email'] = data.get('alert_recipient_email')

        backend_config['runIntervalMinutes'] = int(data.get('runIntervalMinutes', backend_config.get('runIntervalMinutes', 5)))

        save_json_data(CONFIG_FILE, backend_config)
        root_logger.info("Configuration updated and saved.")
        return jsonify({"message": "Configuration updated and saved."}), 200

@app.route('/api/add-client', methods=['POST'])
@login_required
def add_client_endpoint():
    global backend_users
    data = request.get_json()
    if not all(k in data and data[k] is not None for k in ['name', 'account', 'bank', 'amount']):
        return jsonify({"message": "Missing or invalid client data"}), 400
    
    new_id = f"user_{len(backend_users) + 1}_{int(time.time())}"
    new_client = {
        "id": new_id,
        "name": data['name'],
        "account": data['account'],
        "bank": data['bank'],
        "amount": float(data['amount'])
    }
    backend_users.append(new_client)
    save_json_data(USERS_FILE, backend_users)
    root_logger.info(f"Client '{new_client['name']}' added and saved to users.json.")
    return jsonify({"message": "Client added successfully", "client": new_client}), 201

@app.route('/api/remove-client/<string:client_id>', methods=['DELETE'])
@login_required
def remove_client_endpoint(client_id):
    global backend_users
    initial_len = len(backend_users)
    backend_users = [user for user in backend_users if user['id'] != client_id]
    if len(backend_users) < initial_len:
        save_json_data(USERS_FILE, backend_users)
        root_logger.info(f"Client '{client_id}' removed and saved to users.json.")
        return jsonify({"message": "Client removed successfully"}), 200
    else:
        return jsonify({"message": "Client not found"}), 404

# --- Main execution of Flask app ---
if __name__ == '__main__':
    root_logger.info("Starting Flask P2P Bot Backend...")
    app.run(debug=True, port=5000, use_reloader=False)
