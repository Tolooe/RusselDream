from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta
import json

app = Flask(__name__)

# ================== تنظیمات ==================
TELEGRAM_TOKEN = "8977850121:AAFyIf67j078f3lZYtZEELSzLQ-kdZRI3zw"
CHAT_ID = "1964686877"

RSI_PERIOD = 14
RSI_BUY_LEVEL = 35
RSI_SELL_LEVEL = 65

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram Error:", e)

def get_rsi(symbol):
    try:
        # استفاده از API عمومی‌تر
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=15&limit=100"
        
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print("Bybit Status Code:", response.status_code)
        print("Bybit Response:", response.text[:300])  # برای دیدن پاسخ
        
        data = response.json()
        
        if data.get("retCode") != 0:
            print("Bybit Error:", data.get("retMsg"))
            return None
            
        klines = data["result"]["list"]
        
        if not klines or len(klines) < 20:
            print("Not enough kline data")
            return None
            
        # داده‌ها از جدید به قدیم هستند
        closes = [float(k[4]) for k in reversed(klines)]
        
        series = pd.Series(closes)
        rsi = ta.rsi(series, length=RSI_PERIOD)
        
        return round(float(rsi.iloc[-1]), 2)
        
    except Exception as e:
        print("Error getting RSI:", str(e))
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("Received:", data)

        side = str(data.get("side", "")).lower()
        ticker = str(data.get("ticker", "")).replace(".P", "").replace("/", "").upper()
        price = data.get("price", "N/A")

        rsi_value = get_rsi(ticker)
        print(f"RSI Result: {rsi_value}")

        if rsi_value is None:
            send_telegram(f"⚠️ خطا در دریافت RSI برای {ticker}")
            return "Error", 200

        if side == "buy" and rsi_value < RSI_BUY_LEVEL:
            msg = f"🟢 <b>سیگنال خرید تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI: {rsi_value}"
            send_telegram(msg)
            
        elif side == "sell" and rsi_value > RSI_SELL_LEVEL:
            msg = f"🔴 <b>سیگنال فروش تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI: {rsi_value}"
            send_telegram(msg)
            
        else:
            print(f"Condition not met | Side: {side} | RSI: {rsi_value}")

        return "OK", 200

    except Exception as e:
        print("Webhook Error:", e)
        return "Error", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
