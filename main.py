from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta

app = Flask(__name__)

# ================== تنظیمات ==================
TELEGRAM_TOKEN = "8849479878:AAGjdVqt5gsKnkNIPDMqPdsMAhhP7d8yuQI"
CHAT_ID = "1964686877"

RSI_PERIOD = 14
RSI_BUY_LEVEL = 35      # زیر این عدد برای خرید
RSI_SELL_LEVEL = 65     # بالای این عدد برای فروش

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram Error:", e)

def get_rsi(symbol, interval="15m"):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        response = requests.get(url, timeout=10)
        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            print("Invalid data from Binance:", data)
            return None

        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])

        df["close"] = pd.to_numeric(df["close"])
        rsi = ta.rsi(df["close"], length=RSI_PERIOD)

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

        if rsi_value is None:
            send_telegram(f"⚠️ خطا در دریافت RSI برای {ticker}")
            return "Error", 200

        # شرط‌های جدید
        if side == "buy" and rsi_value < RSI_BUY_LEVEL:
            message = f"🟢 <b>سیگنال خرید تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI: {rsi_value}"
            send_telegram(message)

        elif side == "sell" and rsi_value > RSI_SELL_LEVEL:
            message = f"🔴 <b>سیگنال فروش تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI: {rsi_value}"
            send_telegram(message)

        else:
            print(f"شرط برقرار نبود → Side: {side} | RSI: {rsi_value}")

        return "OK", 200

    except Exception as e:
        print("Webhook Error:", e)
        return "Error", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
