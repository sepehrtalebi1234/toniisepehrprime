import requests
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOG_FILE = "log.txt"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error sending message: {e}")

def log(text):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} - {text}\n")

def fetch_price(symbol):
    url = "https://api.nobitex.ir/market/stats"
    try:
        response = requests.get(url)
        stats = response.json().get("stats", {})
        if symbol in stats:
            return float(stats[symbol]["latest"])
        else:
            log(f"Symbol not found: {symbol}")
            return None
    except Exception as e:
        log(f"Error fetching {symbol}: {e}")
        return None

def analyze_prices():
    ton_usdt = fetch_price("ton-usdt")
    ton_irt_direct = fetch_price("ton-rls")
    usdt_irt = fetch_price("usdt-rls")

    if None in (ton_usdt, ton_irt_direct, usdt_irt):
        log("Error: one or more prices not available.")
        return

    ton_irt_indirect = ton_usdt * usdt_irt
    diff = ton_irt_direct - ton_irt_indirect
    percent_diff = (diff / ton_irt_direct) * 100

    message = (
        f"📊 TON/USDT: {ton_usdt}\n"
        f"💰 TON/IRT (Direct): {ton_irt_direct}\n"
        f"💱 USDT/IRT: {usdt_irt}\n"
        f"🔄 TON/IRT (Indirect): {ton_irt_indirect:.2f}\n"
        f"📉 Difference: {diff:.2f} IRR ({percent_diff:.2f}%)"
    )
    log(message)

    # سیگنال‌دهی ساده
    if percent_diff > 2:
        send_telegram_message("📈 فرصت فروش TON! قیمت مستقیم بالاست.\n\n" + message)
    elif percent_diff < -2:
        send_telegram_message("📉 فرصت خرید TON! قیمت غیرمستقیم ارزونه.\n\n" + message)

    return message

def run_bot():
    count = 0
    while True:
        try:
            analyze_prices()
            count += 1
            if count >= 72:  # تقریباً هر 12 ساعت (72 بار در فواصل 10 دقیقه‌ای)
                send_telegram_message("🕒 گزارش ۱۲ ساعته:\n\n" + analyze_prices())
                count = 0
        except Exception as e:
            log(f"Unexpected error: {e}")
        time.sleep(600)  # هر ۱۰ دقیقه

if __name__ == "__main__":
    send_telegram_message("🚀 ربات TON شروع به کار کرد.")
    run_bot()
