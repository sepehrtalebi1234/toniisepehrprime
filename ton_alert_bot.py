import os
import time
import requests
import pandas as pd
import numpy as np
import logging
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from scipy.signal import argrelextrema
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# تنظیمات عمومی
SYMBOL = "TONUSDT"
INTERVALS = ["15m", "1h", "4h"]  # تایم‌فریم‌های تحلیل
API_URL = "https://api.binance.com/api/v3/klines"


def fetch_ohlcv(symbol: str, interval: str, limit: int = 100):
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }
    res = requests.get(API_URL, params=params)
    data = res.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        '_', '_', '_', '_', '_'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df


def analyze(df: pd.DataFrame):
    signals = []

    # اندیکاتورهای تکنیکال
    rsi = RSIIndicator(close=df['close']).rsi()
    ema_fast = EMAIndicator(close=df['close'], window=9).ema_indicator()
    ema_slow = EMAIndicator(close=df['close'], window=21).ema_indicator()
    macd = MACD(close=df['close']).macd_diff()
    bb = BollingerBands(close=df['close'])

    close = df['close']
    volume = df['volume']

    # قوانین نوسان‌گیری ساده
    if (
        rsi.iloc[-1] < 30 and
        macd.iloc[-1] > 0 and
        close.iloc[-1] < bb.bollinger_lband().iloc[-1]
    ):
        signals.append("🔵 سیگنال خرید کوتاه‌مدت")

    elif (
        rsi.iloc[-1] > 70 and
        macd.iloc[-1] < 0 and
        close.iloc[-1] > bb.bollinger_hband().iloc[-1]
    ):
        signals.append("🔴 سیگنال فروش کوتاه‌مدت")

    return signals


def run_analysis():
    try:
        all_signals = []
        for interval in INTERVALS:
            df = fetch_ohlcv(SYMBOL, interval)
            signals = analyze(df)
            if signals:
                all_signals.extend([f"[{interval}] {s}" for s in signals])

        if all_signals:
            message = f"📊 هشدار تحلیلگر TON/USDT:\n\n" + "\n".join(all_signals)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        else:
            print("هیچ سیگنالی یافت نشد.")

    except Exception as e:
        logging.exception("خطا در اجرای تحلیل:")


if __name__ == '__main__':
    while True:
        run_analysis()
        time.sleep(900)  # تحلیل هر ۱۵ دقیقه
