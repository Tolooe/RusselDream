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

def get_rsi(symbol, interval="15"):
    """
    دریافت RSI از Bybit
    interval: 1, 3, 5, 15, 30, 60, 120, 240, D و ...
    """
    try:
        # تبدیل نماد به فرمت Bybit (مثلاً BTCUSDT)
        url = "https://api.bybit.com/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": 100
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("retCode") != 0:
            print("Bybit Error:", data)
            return None

        klines = data["result"]["list"]
        
        if not klines:
            print("No kline
