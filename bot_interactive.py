import os
import telebot
import requests
import schedule
import time
import pytz
from datetime import datetime
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 1. Setup
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID') # Render မှာ Env Variable အနေနဲ့ ထည့်ထားဖို့ လိုပါတယ် (ဥပမာ @kyaymoneNews)
bot = telebot.TeleBot(BOT_TOKEN)

# ===========================
# အပိုင်း (က) - User Interactive (Archive Search)
# ===========================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = message.text.split()
    if len(text) > 1 and text[1] == 'archive':
        bot.reply_to(message, "📅 ဘယ်ရက်စွဲ လိုချင်ပါသလဲ? (ဥပမာ - 21-2-2026 ဟု ရိုက်ပေးပါ)")
    else:
        bot.reply_to(message, "မင်္ဂလာပါ! Archive ရှာလိုပါက Channel Menu မှတဆင့် ဝင်ရောက်ပါ။")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    text = message.text.strip()
    
    # ရက်စွဲပုံစံ စစ်ဆေးခြင်း (ရိုးရှင်းသောနည်းလမ်း)
    if "-" in text or "/" in text:
        # Google Search URL
        search_url = f"https://www.google.com/search?q=site:moi.gov.mm+\"{text}\"+Kyaymon"
        
        # Download Button
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("📥 ဖတ်ရှုရန် / Download ယူရန်", url=search_url)
        markup.add(btn)
        
        reply_text = f"🔍 **{text}** အတွက် ရှာဖွေမှုရလဒ် အသင့်ဖြစ်ပါပြီ။\n\n👇 အောက်ပါခလုတ်ကို နှိပ်ပါ။"
        bot.reply_to(message, reply_text, reply_markup=markup, parse_mode="Markdown")
    else:
        pass # ရက်စွဲမဟုတ်ရင် ဘာမှမလုပ်ပါ

# ===========================
# အပိုင်း (ခ) - Morning Auto Post (Exchange Rates)
# ===========================

def get_exchange_rates():
    try:
        # ဗဟိုဘဏ် API မှ ယူခြင်း
        url = "https://forex.cbm.gov.mm/api/latest"
        response = requests.get(url).json()
        rates = response['rates']
        date_str = response['info']
        
        # အဓိက ငွေကြေးများ
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
        return "🌤 မင်္ဂလာမနက်ခင်းပါ! ဒီနေ့အတွက် သတင်းစာ မကြာမီ လာပါမည်။"

def send_morning_post():
    if CHANNEL_ID:
        msg = get_exchange_rates()
        try:
            bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
            print("Morning post sent!")
        except Exception as e:
            print(f"Failed to send morning post: {e}")

# Scheduler Function (အချိန်ကိုက် စနစ်)
def run_scheduler():
    # မြန်မာစံတော်ချိန် မနက် ၆:၀၀ (MMT)
    # Render Server က UTC ဖြစ်လို့ UTC 23:30 (Previous Day) ကို ချိန်ရပါတယ်
    # ဒါမှမဟုတ် Library 'pytz' သုံးပြီး တိုက်ရိုက်ချိန်ပါမယ်
    
    while True:
        try:
            # လက်ရှိ မြန်မာအချိန်ကို ယူမည်
            tz = pytz.timezone('Asia/Yangon')
            now = datetime.now(tz)
            
            # မနက် ၆ နာရီ ၀ မိနစ်၊ စက္ကန့် ၀ ဖြစ်ရင် Post တင်မယ်
            if now.hour == 6 and now.minute == 0 and now.second < 10: # 10 seconds buffer
                send_morning_post()
                time.sleep(60) # တင်ပြီးရင် ၁ မိနစ် အိပ်မယ် (ထပ်မတင်အောင်)
            
            time.sleep(1) # ၁ စက္ကန့်တိုင်း စစ်မယ်
        except Exception as e:
            print(f"Scheduler Error: {e}")
            time.sleep(5)

# ===========================
# အပိုင်း (ဂ) - Web Server (Render Keep-Alive)
# ===========================

app = Flask('')

@app.route('/')
def home():
    return "Bot is running with Scheduler!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

# Threading (လုပ်ငန်း ၃ ခု ပြိုင်တူ run ခြင်း)
if __name__ == "__main__":
    # 1. Start Web Server
    t1 = Thread(target=run_http)
    t1.start()
    
    # 2. Start Scheduler
    t2 = Thread(target=run_scheduler)
    t2.start()
    
    # 3. Start Bot Polling
    bot.infinity_polling()
