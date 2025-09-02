import os
import ccxt
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- Main Logic ---

def send_telegram_notification(message):
    """Sends a message to your Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials are not set.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Successfully sent notification: {message}")
        else:
            print(f"Error sending notification: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred while sending Telegram message: {e}")


def check_for_macd_cross():
    """Checks for the LATEST MACD zero line cross in the last 100 minutes and sends a notification."""
    symbol = 'BTC/USDT'
    timeframe = '1m'
    
    try:
        # 1. Fetch Data
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        
        # 2. Process Data with Pandas
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')

        # 3. Calculate MACD
        df.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)
        
        # --- LOGIC CHANGE IS HERE ---
        # 4. Check for a cross by searching backwards (from newest to oldest)
        # We start from the last candle (index 99) and go down to the second candle (index 1).
        for i in reversed(range(1, len(df))):
            previous_macd = df['MACD_12_26_9'].iloc[i-1]
            current_macd = df['MACD_12_26_9'].iloc[i]
            
            # Check for Crossover (Negative to Positive)
            if previous_macd <= 0 and current_macd > 0:
                cross_time = df['timestamp'].iloc[i].strftime('%Y-%m-%d %H:%M:%S')
                message = f"{cross_time} crossover (IST)"
                send_telegram_notification(message)
                return # Exit after finding the LATEST cross

            # Check for Crossunder (Positive to Negative)
            if previous_macd >= 0 and current_macd < 0:
                cross_time = df['timestamp'].iloc[i].strftime('%Y-%m-%d %H:%M:%S')
                message = f"{cross_time} crossunder (IST)"
                send_telegram_notification(message)
                return # Exit after finding the LATEST cross
        
        # This message is now more accurate.
        print("No MACD zero cross found in the last 100 minutes.")

    except Exception as e:
        print(f"An error occurred during the check: {e}")

# --- Run the Script ---
if __name__ == "__main__":
    print(f"Running MACD Alert Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    check_for_macd_cross()
