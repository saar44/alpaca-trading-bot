import os
import time
import requests
import alpaca_trade_api as tradeapi

# הגדרת מפתחות הגישה מתוך משתני הסביבה ב-Render
API_KEY = os.getenv('APOLLO_API_KEY') or os.getenv('APCA_API_KEY_ID')
API_SECRET = os.getenv('APOLLO_API_SECRET') or os.getenv('APCA_API_SECRET_KEY')
BASE_URL = 'https://paper-api.alpaca.markets'

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# אתחול חיבור ל-Alpaca (דמו)
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram keys missing")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def scan_and_trade():
    send_telegram_message("🔍 *Alpaca Bot* סורק מניות בטווח 2$-120$...")
    try:
        assets = api.list_assets(status='active', asset_class='us_equity')
        traded_count = 0
        
        for asset in assets:
            if asset.tradable and asset.exchange in ['NASDAQ', 'NYSE']:
                symbol = asset.symbol
                try:
                    bar = api.get_latest_bar(symbol)
                    price = bar.c
                    
                    # סינון לפי טווח המחירים המבוקש (2$ עד 120$)
                    if 2.0 <= price <= 120.0:
                        # בדיקה אם יש מספיק כוח קנייה בחשבון הדמו
                        account = api.get_account()
                        cash = float(account.cash)
                        
                        # הגדרת סכום קנייה לדוגמה לעסקה (למשל 100 דולר או לפי תקציב שתבחר)
                        trade_amount = 100.0
                        if cash >= trade_amount and traded_count < 1:  # מגביל לעסקה אחת לדוגמה בסבב
                            qty = int(trade_amount / price)
                            if qty > 0:
                                # חישוב יעד רווח (12%+) ועצירת הפסד (4%-)
                                take_profit_price = round(price * 1.12, 2)
                                stop_loss_price = round(price * 0.96, 2)
                                
                                # ביצוע פקודת קנייה בדמו
                                api.submit_order(
                                    symbol=symbol,
                                    qty=qty,
                                    side='buy',
                                    type='market',
                                    time_in_force='gtc'
                                )
                                
                                msg = (
                                    f"🚨 *בוצעה פקודת קנייה חדשה (דמו)!*\n"
                                    f"📌 מניה: `{symbol}`\n"
                                    f"💵 מחיר כניסה: `{price}$`\n"
                                    f"📦 כמות: `{qty}`\n"
                                    f"🎯 יעד רווח (+12%): `{take_profit_price}$`\n"
                                    f"🛑 סטופ-לוס (-4%): `{stop_loss_price}$`"
                                )
                                send_telegram_message(msg)
                                traded_count += 1
                except Exception:
                    continue
                    
    except Exception as e:
        send_telegram_message(f"❌ שגיאה בסריקה ובמסחר: {str(e)}")

def main_loop():
    send_telegram_message("🤖 *Alpaca Trading Bot* הופעל ומוכן למסחר דמו!")
    while True:
        scan_and_trade()
        # המתנה של שעה בין סריקה לסריקה
        time.sleep(3600)

if __name__ == "__main__":
    main_loop()
