from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta

app = Flask(__name__)

# ================== تنظیمات ==================
TELEGRAM_TOKEN = "8977850121:AAFyIf67j078f3lZYtZEELSzLQ-kdZRI3zw"
CHAT_ID = "1964686877"

RSI_PERIOD = 14
RSI_BUY_LEVEL = 35      # زیر این عدد برای خرید
RSI_SELL_LEVEL = 65     # بالای این عدد برای فروش
RSI_TIMEFRAME = "15"    # تایم‌فریم ۱۵ دقیقه

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
        url = "https://api.bybit.com/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": RSI_TIMEFRAME,   # <-- تایم‌فریم ۱۵ دقیقه
            "limit": 100
        }

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        print("Status Code:", response.status_code)
        
        data = response.json()

        if data.get("retCode") != 0:
            print("Bybit Error:", data.get("retMsg"))
            return None

        klines = data["result"]["list"]
        
        if not klines or len(klines) < RSI_PERIOD + 5:
            print("Not enough data")
            return None

        # داده‌ها از جدید به قدیم هستند → برعکس می‌کنیم
        closes = [float(item[4]) for item in reversed(klines)]
        
        rsi = ta.rsi(pd.Series(closes), length=RSI_PERIOD)
        
        return round(float(rsi.iloc[-1]), 2)

    except Exception as e:
        print("Error getting RSI:", e)
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
        print(f"RSI (15m) for {ticker}: {rsi_value}")

        if rsi_value is None:
            send_telegram(f"⚠️ خطا در دریافت RSI ۱۵ دقیقه برای {ticker}")
            return "Error", 200

        if side == "buy" and rsi_value < RSI_BUY_LEVEL:
            msg = f"🟢 <b>سیگنال خرید تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI (15m): {rsi_value}"
            send_telegram(msg)

        elif side == "sell" and rsi_value > RSI_SELL_LEVEL:
            msg = f"🔴 <b>سیگنال فروش تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI (15m): {rsi_value}"
            send_telegram(msg)

        else:
            print(f"شرط برقرار نبود | Side: {side} | RSI 15m: {rsi_value}")

        return "OK", 200

    except Exception as e:
        print("Webhook Error:", e)
        return "Error", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
