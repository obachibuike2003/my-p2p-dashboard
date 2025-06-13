import logging
import os
import time
from dotenv import load_dotenv

# Import functions from your custom modules
# Ensure these files (checkorder.py, placeorder.py, payment.py) are in the same directory
from checkorder import get_p2p_offers
from placeorder import place_p2p_order
from payment import send_payment

# --- Configuration and Setup ---

# Load environment variables from the .env file.
# This should be called at the very beginning of your application's entry point.
load_dotenv()

# Configure logging for the entire application.
# Messages will be saved to 'bot_log.txt' and will appear in the console.
# Note: When imported by app.py, app.py's logging config might take precedence
# or integrate this.
logging.basicConfig(
    filename="bot_log.txt",
    level=logging.INFO, # Set to logging.DEBUG for more verbose output during testing
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_log.txt"), # Log to file
        logging.StreamHandler()             # Log to console
    ]
)

# --- Define users list as a GLOBAL variable ---
# This list holds details for different recipients (your clients)
# you might want to send payments to after a crypto purchase.
# This must be at the top level so app.py can import it.
users = [
    # Example for Kuda Bank (Bank Code: 50211)
    {"id": "user1", "amount": 5000.0, "account": "1234567890", "bank": "50211", "name": "Kuda Client A"},
    # Placeholder for Moniepoint (Bank Code needs verification)
    # IMPORTANT: You MUST verify the correct Flutterwave bank code for Moniepoint.
    # If a direct transfer code isn't available, you might need an alternative method.
    {"id": "user2", "amount": 10000.0, "account": "9876543210", "bank": "YOUR_MONIEPOINT_BANK_CODE", "name": "Moniepoint Client B"}
]

# --- Helper Functions for Bot Logic ---
# These functions are now defined globally in main.py.
# While app.py might have its own copies for immediate integration,
# this makes them available for other parts of your bot if needed.

def select_suitable_offer(offers: list, desired_fiat_amount: float) -> dict | None:
    """
    Selects the most suitable P2P offer based on amount limits and price.
    Prioritizes offers that can fulfill the desired amount and then by best price.

    Args:
        offers (list): A list of P2P offers fetched from Bybit.
        desired_fiat_amount (float): The specific fiat amount (NGN) the user wants to spend.

    Returns:
        dict | None: The selected offer dictionary if found, otherwise None.
    """
    suitable_offers = []
    logging.info(f"Searching for an offer suitable for {desired_fiat_amount} NGN...")

    for offer in offers:
        try:
            min_amt = float(offer.get('minTradeAmount', 0))
            max_amt = float(offer.get('maxTradeAmount', float('inf'))) # Use infinity if max is missing
            price = float(offer.get('price', 0)) # Price of 1 USDT in fiat
            tradable_quantity = float(offer.get('tradableQuantity', 0)) # Ensure this is also floated

            # Check if the desired amount falls within the offer's limits
            if min_amt <= desired_fiat_amount <= max_amt:
                # Also, check if the offer has enough crypto for the desired fiat amount
                # This calculation assumes you are buying USDT (side="Buy")
                crypto_amount_from_offer = desired_fiat_amount / price

                if crypto_amount_from_offer <= tradable_quantity:
                    suitable_offers.append(offer)
                    logging.debug(f"Found suitable offer: Seller '{offer.get('nickName', 'N/A')}', Price: {price}, Limits: {min_amt}-{max_amt}")
                else:
                    logging.debug(f"Offer from '{offer.get('nickName', 'N/A')}' (Price: {price}) has insufficient crypto quantity for {desired_fiat_amount} NGN.")

        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping offer due to invalid amount/price data: {offer}. Error: {e}")
            continue

    if not suitable_offers:
        logging.warning(f"No offers found that match the desired amount {desired_fiat_amount} NGN within their limits and tradable quantity.")
        return None

    suitable_offers.sort(key=lambda x: float(x.get('price', float('inf'))))

    best_offer = suitable_offers[0]
    logging.info(f"Selected best offer from '{best_offer.get('nickName', 'N/A')}' at price {best_offer.get('price')} for {desired_fiat_amount} NGN.")
    return best_offer


def safe_api_call(api_func, *args, retries=3, delay=5, **kwargs):
    """
    Attempts to call an API function with retries on failure.

    Args:
        api_func (callable): The function to call (e.g., place_p2p_order, send_payment).
        *args: Positional arguments to pass to api_func.
        retries (int): Number of times to retry the call.
        delay (int): Delay in seconds between retries.
        **kwargs: Keyword arguments to pass to api_func.

    Returns:
        Any: The result of api_func if successful, otherwise None after all retries fail.
    """
    for attempt in range(1, retries + 1):
        logging.info(f"Attempt {attempt}/{retries} to call {api_func.__name__}...")
        result = api_func(*args, **kwargs)
        if result is not None:
            logging.info(f"✅ {api_func.__name__} successful on attempt {attempt}.")
            return result
        else:
            if attempt < retries:
                logging.warning(f"❌ {api_func.__name__} failed on attempt {attempt}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"❌ {api_func.__name__} failed after {retries} attempts.")
    return None

# --- Main Application Logic Function (renamed for clarity when imported) ---
# This function encapsulates the bot's core trading loop.
# It is designed to be called by app.py, not to run automatically on import.
def run_p2p_bot_core_logic():
    logging.info("--- P2P Bot Core Logic Started ---")

    # This function is now callable by app.py
    # You would typically pass parameters needed for a specific run
    # For now, it will use global 'users' and fetch its own offers.
    # In a more advanced Flask setup, you might pass users/config from Flask.

    # This implementation mirrors the main logic from the original main.py
    logging.info("Attempting to fetch P2P offers from Bybit...")
    offers = get_p2p_offers(crypto="USDT", fiat="NGN", side="Buy", payment_method="Bank Transfer")

    if not offers:
        logging.error("No P2P offers found or failed to retrieve offers. Core logic stopping.")
        return # Stop execution if no offers are available

    logging.info(f"Successfully retrieved {len(offers)} P2P offers from Bybit.")

    for user in users:
        user_amount = user["amount"]
        user_account = user["account"]
        user_bank_code = user["bank"]
        user_name = user.get("name", "Unknown User")

        logging.info(f"\n--- Processing for User: {user_name} (Account: {user_account}, Bank: {user_bank_code}) ---")

        selected_offer = select_suitable_offer(offers, user_amount)

        if not selected_offer:
            logging.error(f"No suitable offer found for {user_name} with desired amount {user_amount} NGN. Skipping this user.")
            continue

        offer_id = selected_offer.get('advNo')

        if not offer_id:
            logging.error(f"❌ Could not extract offer ID from the selected offer for {user_name}. Skipping order placement.")
            continue

        logging.info(f"Chosen offer ID: {offer_id} (Seller: {selected_offer.get('nickName')}, Price: {selected_offer.get('price')})")

        logging.info(f"Attempting to place P2P order on Bybit for offer ID: {offer_id} with amount: {user_amount} NGN.")
        order_details = safe_api_call(place_p2p_order, offer_id, user_amount, retries=3, delay=5)

        if order_details:
            order_no = order_details.get('orderNo', 'N/A')
            logging.info(f"✅ P2P Order '{order_no}' successfully placed for {user_name} on Bybit.")
            logging.warning(f"ACTION REQUIRED: Please go to Bybit to confirm payment for order '{order_no}' within the given time frame ({selected_offer.get('timeLimit') or 'N/A'} minutes).")
            logging.warning("This bot does NOT automatically confirm payment on Bybit or wait for crypto release.")

            logging.info(f"Attempting to send payment of {user_amount} NGN to {user_name} ({user_account}, Bank: {user_bank_code})...")

            if user_bank_code == "YOUR_MONIEPOINT_BANK_CODE":
                logging.warning(f"⚠️ Moniepoint bank code is a placeholder. Payment for {user_name} may fail unless a valid code is provided from Flutterwave docs.")
            
            payment_id = safe_api_call(send_payment, user_account, user_bank_code, user_amount, retries=3, delay=10)

            if payment_id:
                logging.info(f"✅ Payment sent successfully for {user_name}! Flutterwave Transfer ID: {payment_id}")
                logging.warning(f"REMINDER: After payment is sent, wait for the seller to release crypto on Bybit. Monitor Bybit order '{order_no}' status.")
            else:
                logging.error(f"❌ Payment failed for {user_name} ({user_account}). Investigate payment.py logs and Flutterwave dashboard.")
                logging.warning(f"CRITICAL: P2P Order '{order_no}' placed but payment failed for {user_name}. MANUAL INTERVENTION REQUIRED on Bybit!")
        else:
            logging.error(f"❌ Failed to place P2P order for {user_name}. See placeorder.py logs for details.")
            logging.warning(f"No order placed for {user_name}. Check Bybit API key permissions and your balance.")

    logging.info("--- P2P Bot Core Logic Finished ---")


# --- Entry Point (commented out for Flask integration) ---
# This block will NOT run when main.py is imported by app.py.
# app.py will explicitly call the functions it needs.
# if __name__ == "__main__":
#     logging.info("--- Application Started (Standalone) ---")
#     # Ensure all necessary API keys are loaded from .env
#     bybit_api_key = os.getenv("BYBIT_API_KEY")
#     bybit_api_secret = os.getenv("BYBIT_API_SECRET")
#     flutterwave_secret_key = os.getenv("FLUTTERWAVE_SECRET_KEY")

#     if not bybit_api_key or not bybit_api_secret:
#         logging.critical("Bybit API keys (BYBIT_API_KEY, BYBIT_API_SECRET) are not set. Please check your .env file.")
#     if not flutterwave_secret_key:
#         logging.critical("Flutterwave Secret Key (FLUTTERWAVE_SECRET_KEY) is not set. Please check your .env file.")
    
#     run_p2p_bot_core_logic()
