import os
import asyncio
from datetime import datetime
from flask import Flask, jsonify
from deriv_api import DerivAPI

app = Flask(__name__)

# Configuration loaded securely from Render Environment Variables
BOT_SECRET = os.getenv("BOT_SECRET", "311223")
DERIV_APP_ID = int(os.getenv("DERIV_APP_ID", "1089"))
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN", "YOUR_DERIV_API_TOKEN")
SYMBOL = "frxXAUUSD"  # Gold symbol on Deriv Web API

async def run_trading_bot():
    """Autonomous background trading loop using Deriv Web API"""
    print("Starting autonomous Gold Breakout bot (Deriv Web API)...")
    
    # Instantiate the Deriv WebSocket API connection
    api = DerivAPI(app_id=DERIV_APP_ID)
    
    # 1. Authorize using your Web API token
    auth = await api.authorize(DERIV_API_TOKEN)
    if not auth or "error" in auth:
        print(f"Deriv Authorization failed: {auth}")
        return

    # 2. Extract and log account details
    user_info = auth.get("authorize", {})
    user_id = user_info.get("loginid", "Unknown")
    email = user_info.get("email", "Unknown")
    currency = user_info.get("currency", "USD")
    is_virtual = user_info.get("is_virtual", 0)
    balance = user_info.get("balance", 0.0)
    
    account_type = "DEMO (Virtual)" if is_virtual == 1 else "REAL"
    
    print(f"=== Deriv Account Connected Successfully ===")
    print(f"Login ID: {user_id}")
    print(f"Account Type: {account_type}")
    print(f"Balance: {balance} {currency}")
    print(f"Email: {email}")
    print(f"==========================================")

    current_day = None
    range_high = None
    range_low = None
    traded_today = False

    while True:
        try:
            now = datetime.utcnow()
            day = now.date()
            hour = now.hour

            # Reset daily variables on a new day
            if day != current_day:
                current_day = day
                range_high = None
                range_low = None
                traded_today = False
                print(f"--- New Trading Day: {day} ---")

            # Range building window: 04:00 to 06:00 UTC
            if 4 <= hour < 6 and not traded_today:
                candles = await api.ticks_history({
                    "ticks_history": SYMBOL,
                    "end": "latest",
                    "count": 10,
                    "granularity": 900  # 15-minute candles
                })
                
                if "history" in candles:
                    prices = candles["history"]["prices"]
                    range_high = max(prices)
                    range_low = min(prices)
                    print(f"Range built — High: {range_high} | Low: {range_low}")

            # Trading window: 06:00 UTC onwards
            elif hour >= 6 and range_high and range_low and not traded_today:
                print(f"Monitoring breakout levels: Buy > {range_high} or Sell < {range_low}")
                
                # Example Deriv API order proposal & buy execution framework:
                # proposal = await api.proposal({
                #     "proposal": 1,
                #     "amount": 10,
                #     "basis": "stake",
                #     "contract_type": "CALL",
                #     "currency": currency,
                #     "symbol": SYMBOL,
                #     "duration": 1,
                #     "duration_unit": "d"
                # })
                # if "proposal" in proposal:
                #     buy_res = await api.buy({"buy": proposal["proposal"]["id"], "price": 10})
                #     print(f"Order executed: {buy_res}")

                traded_today = True

            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"Bot loop error: {e}")
            await asyncio.sleep(30)

@app.route('/')
def home():
    return jsonify({"status": "Autonomous Gold Bot is running live", "symbol": SYMBOL}), 200

def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_trading_bot())

if __name__ == '__main__':
    import threading
    t = threading.Thread(target=start_background_loop, daemon=True)
    t.start()
    
    app.run(host='0.0.0.0', port=8080)
