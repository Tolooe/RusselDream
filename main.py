
from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta

app = Flask(__name__)

# ================== تنظیمات ==================
TELEGRAM_TOKEN = "توکن_ربات_تلگرام_اینجا"
CHAT_ID = "چت_آیدی_خودت_اینجا"

RSI_PERIOD = 14
RSI_BUY_LEVEL = 30
RSI_SELL_LEVEL = 70

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def get_rsi(symbol, interval="15m"):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        data = requests.get(url).json()
        df = pd.DataFrame(data)
        df[4] = pd.to_numeric(df[4])
        rsi = ta.rsi(df[4], length=RSI_PERIOD)
        return round(rsi.iloc[-1], 2)
    except Exception as e:
        print("Error getting RSI:", e)
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received:", data)

    side = data.get("side", "").lower()
    ticker = data.get("ticker", "").replace(".P", "").replace("/", "").upper()
    price = data.get("price", "N/A")

    rsi_value = get_rsi(ticker)

    if rsi_value is None:
        send_telegram(f"⚠️ خطا در دریافت RSI برای {ticker}")
        return "Error", 200

    if side == "buy" and rsi_value <= RSI_BUY_LEVEL:
        message = f"🟢 <b>سیگنال خرید تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI: {rsi_value}"
        send_telegram(message)
    elif side == "sell" and rsi_value >= RSI_SELL_LEVEL:
        message = f"🔴 <b>سیگنال فروش تأیید شد</b>\n\nجفت‌ارز: {ticker}\nقیمت: {price}\nRSI: {rsi_value}"
        send_telegram(message)
    else:
        # اگر خواستی وقتی شرط برقرار نیست هم خبرت کنه، خط پایین را از حالت نظر خارج کن
        # send_telegram(f"⚪ سیگنال دریافت شد اما شرط RSI برقرار نبود\n{ticker} | {side} | RSI: {rsi_value}")
        pass

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
