import os
import telebot
import requests
import schedule
import time
import pytz
import urllib.parse  # URL ပြဿနာဖြေရှင်းရန် ထပ်ထည့်ထားသည်
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# 1. Setup
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID') 
bot = telebot.TeleBot(BOT_TOKEN)

# ===========================
# အပိုင်း (က) - User Interactive (Archive Search)
# ===========================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = message.text.split()
    if len(text) > 1 and text[1] == 'archive':
        bot.reply_to(message, "📅 ဘယ်ရက်စွဲ လိုချင်ပါသလဲ? (ဥပမာ - 21-2-2026)")
    else:
        bot.reply_to(message, "မင်္ဂလာပါ! Archive ရှာလိုပါက Channel Menu မှတဆင့် ဝင်ရောက်ပါ။")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    try:
        text = message.text.strip()
        
        # ရက်စွဲဖြစ်နိုင်ချေရှိသော စာများ (- သို့မဟုတ် / ပါဝင်သည်)
        if "-" in text or "/" in text:
            
            # --- ပြင်ဆင်ထားသော အပိုင်း (URL Fixing) ---
            # မူရင်းစာသား: site:moi.gov.mm "21-2-2026" Kyaymon
            raw_query = f'site:moi.gov.mm "{text}" Kyaymon'
            
            # Telegram လက်ခံအောင် Encode လုပ်ခြင်း (Space -> %20, " -> %22)
            encoded_query = urllib.parse.quote(raw_query)
            
            # နောက်ဆုံး Link
            search_url = f"https://www.google.com/search?q={encoded_query}"
            # ----------------------------------------

            # Button တည်ဆောက်ခြင်း
            markup = InlineKeyboardMarkup()
            btn = InlineKeyboardButton("📥 ဖတ်ရှုရန် / Download ယူရန်", url=search_url)
            markup.add(btn)
            
            # စာပြန်ခြင်း
            reply_text = f"🔍 **{text}** အတွက် ရှာဖွေမှုရလဒ်:\n\n👇 အောက်ပါခလုတ်ကို နှိပ်ပါ။"
            bot.reply_to(message, reply_text, reply_markup=markup, parse_mode="Markdown")
            
        else:
            # ရက်စွဲမဟုတ်ရင် ဘာမှမလုပ်ပါ (User စိတ်မရှုပ်အောင်)
            pass 

    except Exception as e:
        print(f"Error: {e}")
        # Error တက်ရင် User ကို အသိပေးမည်
        bot.reply_to(message, "စနစ်ပိုင်းဆိုင်ရာ Error ဖြစ်နေပါသည်။ Admin ကို အကြောင်းကြားပါ။")

# ===========================
# အပိုင်း (ခ) - Morning Auto Post (Exchange Rates)
# ===========================

def get_exchange_rates():
    try:
        url = "https://forex.cbm.gov.mm/api/latest"
        response = requests.get(url).json()
        rates = response['rates']
        date_str = response['info']
        
        usd = rates.get('USD', 'N/A')
        eur = rates.get('EUR', 'N/A')
        sgd = rates.get('SGD', 'N/A')
        thb = rates.get('THB', 'N/A')
        
        msg = (
            f"🌤 **မင်္ဂလာမနက်ခင်းပါ** ({date_str})\n\n"
            f"🏦 **ဗဟိုဘဏ် ငွေလဲလှယ်နှုန်းများ**\n"
            f"🇺🇸 USD: {usd} MMK\n"
            f"🇪🇺 EUR: {eur} MMK\n"
            f"🇸🇬 SGD: {sgd} MMK\n"
            f"🇹🇭 THB: {thb} MMK\n\n"
            f"🗞 _ဒီနေ့ သတင်းစာ ခဏအကြာတွင် ရောက်ရှိပါမည်..._"
        )
        return msg
    except Exception as e:
        print(f"Error fetching rates: {e}")
        return "🌤 မင်္ဂလာမနက်ခင်းပါ! သတင်းစာ မကြာမီ လာပါမည်။"

def send_morning_post():
    if CHANNEL_ID:
        msg = get_exchange_rates()
        try:
            bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
            print("Morning post sent!")
        except Exception as e:
            print(f"Failed to send morning post: {e}")

# Scheduler Function
def run_scheduler():
    while True:
        try:
            tz = pytz.timezone('Asia/Yangon')
            now = datetime.now(tz)
            
            # မနက် ၆:၀၀ အတိတွင် တင်မည်
            if now.hour == 6 and now.minute == 0 and now.second < 10:
                send_morning_post()
                time.sleep(60) # ၁ မိနစ် အနားယူ (ထပ်မတင်မိအောင်)
            
            time.sleep(1)
        except Exception as e:
            print(f"Scheduler Error: {e}")
            time.sleep(5)

# ===========================
# အပိုင်း (ဂ) - Web Server (Render Keep-Alive)
# ===========================

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # 1. Start Web Server
    t1 = Thread(target=run_http)
    t1.start()
    
    # 2. Start Scheduler
    t2 = Thread(target=run_scheduler)
    t2.start()
    
    # 3. Start Bot Polling
    bot.infinity_polling()
