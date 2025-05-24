from flask import Flask
import ccxt
import threading
import time
from config import BOT_TOKEN, CHAT_ID, PAIR_LIST
import requests

app = Flask(__name__)

# آدرس API نوبیتکس
NOBITEX_API = "https://api.nobitex.ir/market/stats"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# گرفتن قیمت‌های لحظه‌ای
def fetch_price(symbol):
    try:
        if symbol == "TON/USDT":
            binance = ccxt.binance()
            ticker = binance.fetch_ticker("TON/USDT")
            return float(ticker['last'])
        elif symbol in ["TON/IRT", "USDT/IRT"]:
            res = requests.get(NOBITEX_API)
            data = res.json()
            key = symbol.lower().replace("/", "")
            return float(data["stats"][key]["latest"])
        else:
            return None
    except Exception as e:
        print(f"خطا در دریافت قیمت {symbol}: {e}")
        return None

# محاسبه سیگنال‌ها با استفاده از یک استراتژی ساده
def calculate_signal(prices):
    signal = ""
    try:
        ton_usdt = prices["TON/USDT"]
        ton_irt = prices["TON/IRT"]
        usdt_irt = prices["USDT/IRT"]

        implied_usdt_irt = ton_irt / ton_usdt
        diff_percent = ((implied_usdt_irt - usdt_irt) / usdt_irt) * 100

        signal += f"📊 TON/USDT: {ton_usdt:.3f} $\n"
        signal += f"📊 TON/IRT: {ton_irt:,.0f} تومان\n"
        signal += f"📊 USDT/IRT: {usdt_irt:,.0f} تومان\n"
        signal += f"💡 Implied USDT/IRT via TON: {implied_usdt_irt:,.0f} تومان\n"
        signal += f"📈 اختلاف: {diff_percent:.2f}%\n"

        if diff_percent > 1.5:
            signal += "\n✅ فرصت فروش TON به ریال (قیمت بیش‌برآورد شده)"
        elif diff_percent < -1.5:
            signal += "\n✅ فرصت خرید TON به ریال (قیمت کم‌برآورد شده)"
        else:
            signal += "\nℹ️ وضعیت متعادل"

        return signal

    except Exception as e:
        return f"❗ خطا در تحلیل: {e}"

# ارسال پیام به تلگرام
def send_to_telegram(message):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(TELEGRAM_API, data=payload)
    except Exception as e:
        print(f"❗ خطا در ارسال تلگرام: {e}")

# تسک تکرارشونده
def run_bot():
    while True:
        try:
            prices = {pair: fetch_price(pair) for pair in PAIR_LIST}
            if all(prices.values()):
                signal = calculate_signal(prices)
                send_to_telegram(signal)
        except Exception as e:
            print(f"❗ خطای کلی: {e}")
        time.sleep(900)  # هر ۱۵ دقیقه

# اجرای ربات در ترد جدا
@app.before_first_request
def activate_job():
    thread = threading.Thread(target=run_bot)
    thread.start()

# پاسخ به درخواست وب‌سرویس (برای اطمینان از فعال بودن)
@app.route('/')
def index():
    return "✅ ربات تحلیلگر TON فعال است."

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
