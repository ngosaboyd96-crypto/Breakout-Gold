import os
import asyncio
from flask import Flask, request, jsonify
from deriv_api import DerivAPI

app = Flask(__name__)

BOT_SECRET = os.getenv("BOT_SECRET", "super-secret-key-123")
DERIV_APP_ID = int(os.getenv("DERIV_APP_ID", "1089"))
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN", "YOUR_DERIV_API_TOKEN")

async def execute_deriv_trade(action, symbol, qty, sl_price):
    try:
        api = DerivAPI(app_id=DERIV_APP_ID)
        auth = await api.authorize({"authorize": DERIV_API_TOKEN})
        if not auth or "error" in auth:
            print(f"Deriv Authorization failed: {auth}")
            return False

        print(f"Successfully connected! Executing {action} on {symbol} | Qty: {qty} | SL: {sl_price}")
        # Insert specific Deriv order call here (e.g., api.buy({...}))
        return True
    except Exception as e:
        print(f"Deriv Execution Error: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON payload"}), 400
    
    if data.get("secret") != BOT_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    action = data.get("action")   
    event = data.get("event")     
    ticker = data.get("ticker")   
    qty = data.get("qty")
    sl = data.get("sl")
    reason = data.get("reason")

    if event == "entry":
        asyncio.run(execute_deriv_trade(action, ticker, qty, sl))
    elif event == "exit":
        print(f"Closing positions for {ticker}. Reason: {reason}")

    return jsonify({"status": "success", "event": event}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
