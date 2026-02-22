import os
import time
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
import schedule
from datetime import datetime
import pytz

# Render မှ Environment Variables များ
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID') # Render မှာ ထပ်ထည့်ပေးရပါမယ်
bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# ၁။ Bot အောက်ခြေ Menu နှင့် စာပြန်ခြင်း စနစ်
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # အောက်ခြေမှာ အမြဲပေါ်နေမယ့် ခလုတ် (၃) ခု ဖန်တီးခြင်း
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("🔍 သတင်းစာရှာရန်")
    btn2 = KeyboardButton("📊 ယနေ့ပေါက်ဈေး")
    btn3 = KeyboardButton("📞 Admin သို့ ဆက်သွယ်ရန်")
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(message.chat.id, "မင်္ဂလာပါ! အောက်ပါ Menu များမှ ရွေးချယ်နိုင်ပါသည် 👇", reply_markup=markup)

@bot.message_handler(func=lambda msg: True)
def handle_messages(message):
    text = message.text.strip()
    
    if text == "🔍 သတင်းစာရှာရန်" or text.lower() == "/archive":
        bot.reply_to(message, "📅 ဘယ်ရက်စွဲ လိုချင်ပါသလဲ? (ဥပမာ - 21-2-2026 ဟု ရိုက်ပေးပါ)")
        
    elif text == "📊 ယနေ့ပေါက်ဈေး":
        rates = get_daily_rates()
        bot.reply_to(message, rates, parse_mode="Markdown")
        
    elif text == "📞 Admin သို့ ဆက်သွယ်ရန်":
        bot.reply_to(message, "Admin နှင့် တိုက်ရိုက်ပြောဆိုရန် 👉 @thanhtikeu72win ကို နှိပ်ပါ။")
        
    elif "-" in text or "/" in text:
        # Download Button နှင့် Google Link ပို့ပေးခြင်း
        search_url = f"https://www.google.com/search?q=site:moi.gov.mm+\"{text}\"+Kyaymon"
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("📥 ဖတ်ရှုရန် / Download ယူရန်", url=search_url)
        markup.add(btn)
        bot.reply_to(message, f"🔍 **{text}** အတွက် ရှာဖွေမှုရလဒ်:\n\n👇 အောက်ပါခလုတ်ကို နှိပ်ပါ။", reply_markup=markup, parse_mode="Markdown")
        
    else:
        bot.reply_to(message, "⚠️ ကျေးဇူးပြု၍ အောက်ခြေ Menu မှ ရွေးချယ်ပါ သို့မဟုတ် ရက်စွဲကို (21-2-2026) ပုံစံဖြင့် ရိုက်ထည့်ပါ။")

# ==========================================
# ၂။ ရွှေဈေး / ငွေဈေး Auto Post စနစ်
# ==========================================

def get_daily_rates():
    # မှတ်ချက်: တကယ့် Live ဈေးနှုန်းတွေကို Website တွေကနေ Auto ဆွဲယူဖို့က အနည်းငယ် ရှုပ်ထွေးပါတယ်။
    # လောလောဆယ် ပုံစံပြ (Sample) အနေဖြင့်သာ ထည့်ထားပါသည်။ (နောင်တွင် API ဖြင့် ချိတ်ဆက်နိုင်သည်)
    tz = pytz.timezone('Asia/Yangon')
    today = datetime.now(tz).strftime("%d-%m-%Y")
    
    text = (
        f"📊 **ယနေ့ပေါက်ဈေး ({today})**\n\n"
        f"💵 ကန်ဒေါ်လာ (USD): ~ xxxx ကျပ်\n"
        f"🥇 အကယ်ဒမီ မီးလင်းရွှေ: ~ xxxxx ကျပ်\n"
        f"⛽ စက်သုံးဆီ (92): ~ xxxx ကျပ်\n\n"
        f"*(မှတ်ချက်: ဤသည်မှာ ဥပမာပြသထားခြင်းသာ ဖြစ်ပါသည်။)*"
    )
    return text

def job_post_rates_to_channel():
    if CHANNEL_ID:
        try:
            rates_text = get_daily_rates()
            bot.send_message(CHANNEL_ID, rates_text, parse_mode="Markdown")
            print("Successfully posted daily rates to channel.")
        except Exception as e:
            print(f"Error posting rates: {e}")

# ==========================================
# ၃။ အချိန်ကိုက် လုပ်ဆောင်မည့် Scheduler
# ==========================================

def run_scheduler():
    # နေ့စဉ် မြန်မာစံတော်ချိန် မနက် ၆ နာရီခွဲတွင် တင်ရန် (Render သည် UTC အချိန်ကို သုံးသဖြင့် UTC 00:00 ဟု ထားပါသည်)
    schedule.every().day.at("00:00").do(job_post_rates_to_channel)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# ==========================================
# ၄။ Flask Server (Render အတွက် Keep-Alive)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running with Scheduler!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_http).start()      # Server စတင်ခြင်း
    Thread(target=run_scheduler).start() # Auto-Post အချိန်ကိုက်စနစ် စတင်ခြင်း
    bot.infinity_polling()               # Bot စတင်ခြင်း
