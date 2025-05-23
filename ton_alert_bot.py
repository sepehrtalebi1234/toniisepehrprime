import requests
import time
import traceback

# اطلاعات تلگرام
TELEGRAM_TOKEN = "توکن رباتت اینجا"
TELEGRAM_CHAT_ID = "آیدی عددی تلگرامت اینجا"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except:
        pass  # در صورت قطع اینترنت یا خطای ارسال، نادیده بگیر

def fetch_price(symbol="ton/usdt"):
    response = requests.get("https://api.nobitex.ir/market/stats")
    stats = response.json()["stats"]
    return float(stats[symbol.replace("/", "")]["latest"])

def run_bot():
    prices = []
    last_signal = None
    last_alive = time.time()
    send_telegram("✅ ربات با موفقیت روی Render اجرا شد و فعال است.")

    while True:
        try:
            price = fetch_price()
            prices.append(price)
            if len(prices) > 20:
                prices.pop(0)
            if len(prices) >= 20:
                ma5 = sum(prices[-5:]) / 5
                ma20 = sum(prices) / 20

                if ma5 > ma20 and last_signal != "buy":
                    send_telegram("📈 سیگنال خرید (تقاطع صعودی MA5/MA20)")
                    last_signal = "buy"
                elif ma5 < ma20 and last_signal != "sell":
                    send_telegram("📉 سیگنال فروش (تقاطع نزولی MA5/MA20)")
                    last_signal = "sell"

            # هر 12 ساعت پیام وضعیت بده
            if time.time() - last_alive > 43200:
                send_telegram("🔄 ربات همچنان فعال است و بازار را رصد می‌کند.")
                last_alive = time.time()

        except Exception as e:
            traceback.print_exc()
            send_telegram(f"❗ خطا: {e}")

        time.sleep(300)  # هر ۵ دقیقه یک بار داده جدید

if __name__ == "__main__":
    run_bot()
