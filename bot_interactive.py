import os
import telebot
import requests
import time
import pytz
import urllib.parse
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from bs4 import BeautifulSoup  # Web Scraping အတွက်

# 1. Setup
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID') 
bot = telebot.TeleBot(BOT_TOKEN)

# MOI URLs
KM_URL = "https://www.moi.gov.mm/km/"
MAL_URL = "https://www.moi.gov.mm/mal/"

# ===========================
# အပိုင်း (က) - Helper Functions (Scraping)
# ===========================

def get_direct_pdf_link(base_url):
    """MOI Website မှ နောက်ဆုံးရ PDF Link ကို ရှာပေးသော Function"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 1. Category Page ကို ဆွဲမည်
        res = requests.get(base_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        article_link = None
        target_path = '/km/' if 'km' in base_url else '/mal/'
        
        # Link ရှာခြင်း
        for link in soup.find_all('a', href=True):
            if target_path in link['href'] and any(c.isdigit() for c in link['href']):
                article_link = link['href']
                break # အပေါ်ဆုံး Link (Latest) ကို ယူမည်
        
        if not article_link: return None
        
        # 2. Article Page ထဲ ဝင်မည်
        full_article_url = article_link if article_link.startswith('http') else "https://www.moi.gov.mm" + article_link
        res2 = requests.get(full_article_url, headers=headers, timeout=15)
        soup2 = BeautifulSoup(res2.content, 'html.parser')
        
        # 3. PDF ရှာမည်
        for link in soup2.find_all('a', href=True):
            if link['href'].lower().endswith('.pdf'):
                pdf_url = link['href']
                # Full URL ပြန်ပေးမည်
                return pdf_url if pdf_url.startswith('http') else "https://www.moi.gov.mm" + pdf_url
        return None
    except Exception as e:
        print(f"Scraping Error: {e}")
        return None

# ===========================
# အပိုင်း (ခ) - User Handlers
# ===========================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    msg = (
        f"🙏 မင်္ဂလာပါ {user_name}!\n\n"
        "📰 **ယနေ့ သတင်းစာများ ရယူရန်**\n"
        "အောက်ပါ ခလုတ်များကို နှိပ်၍ တိုက်ရိုက် Download ရယူနိုင်ပါသည်။\n\n"
        "📅 **ရက်ဟောင်းများ ရှာလိုလျှင်**\n"
        "ရက်စွဲကို ရိုက်ထည့်ပါ (ဥပမာ - 21-2-2026)"
    )
    
    markup = InlineKeyboardMarkup()
    # Direct Download Buttons
    btn_km = InlineKeyboardButton("📥 ကြေးမုံ (Today)", callback_data="dl_km")
    btn_mal = InlineKeyboardButton("📥 မြန်မာ့အလင်း (Today)", callback_data="dl_mal")
    markup.row(btn_km, btn_mal)
    
    bot.reply_to(message, msg, reply_markup=markup, parse_mode="Markdown")

# Callback Handler for Buttons
@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def handle_download_buttons(call):
    paper_type = call.data.split('_')[1] # 'km' or 'mal'
    name = "ကြေးမုံ" if paper_type == 'km' else "မြန်မာ့အလင်း"
    url = KM_URL if paper_type == 'km' else MAL_URL
    
    # Loading Message
    bot.answer_callback_query(call.id, f"{name} ကို ရှာဖွေနေပါသည်...")
    loading_msg = bot.send_message(call.message.chat.id, f"🔍 **{name}** ယနေ့ထုတ် PDF ကို ရှာဖွေနေပါသည်... ခေတ္တစောင့်ပါ...", parse_mode="Markdown")
    
    # Scraping
    pdf_link = get_direct_pdf_link(url)
    
    # Delete Loading Message
    try:
        bot.delete_message(call.message.chat.id, loading_msg.message_id)
    except:
        pass

    if pdf_link:
        markup = InlineKeyboardMarkup()
        btn_dl = InlineKeyboardButton(f"⬇️ {name} Download ယူရန် နှိပ်ပါ", url=pdf_link)
        markup.add(btn_dl)
        bot.send_message(call.message.chat.id, f"✅ **{name}** အတွက် Link ရပါပြီ!", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, f"⚠️ **{name}** ယနေ့စာစောင် Web Page တွင် မတွေ့ရှိရသေးပါ။ (ခေတ္တအကြာမှ ပြန်စမ်းပါ)", parse_mode="Markdown")

# Date Search Handler
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    try:
        text = message.text.strip()
        # ရက်စွဲပုံစံ စစ်ဆေးခြင်း (- သို့မဟုတ် / ပါဝင်လျှင်)
        if "-" in text or "/" in text:
            raw_query = f'site:moi.gov.mm "{text}" Kyaymon'
            encoded_query = urllib.parse.quote(raw_query)
            search_url = f"https://www.google.com/search?q={encoded_query}"

            markup = InlineKeyboardMarkup()
            btn = InlineKeyboardButton("🔍 Google တွင် ရှာဖွေရန်", url=search_url)
            markup.add(btn)
            
            bot.reply_to(message, f"📆 **{text}** အတွက် Archive ရှာဖွေမှု:", reply_markup=markup, parse_mode="Markdown")
        else:
            # ရက်စွဲမဟုတ်လျှင် ဘာမှမလုပ် (သို့မဟုတ်) Help ပြနိုင်သည်
            pass 

    except Exception as e:
        print(f"Error: {e}")

# ===========================
# အပိုင်း (ဂ) - Morning Auto Post
# ===========================

def get_exchange_rates():
    try:
        url = "https://forex.cbm.gov.mm/api/latest"
        response = requests.get(url, timeout=10).json()
        rates = response['rates']
        date_str = response['info']
        
        msg = (
            f"🌤 **မင်္ဂလာမနက်ခင်းပါ** ({date_str})\n\n"
            f"🏦 **ဗဟိုဘဏ် ငွေလဲလှယ်နှုန်းများ**\n"
            f"🇺🇸 USD: {rates.get('USD','-')} MMK\n"
            f"🇪🇺 EUR: {rates.get('EUR','-')} MMK\n"
            f"🇸🇬 SGD: {rates.get('SGD','-')} MMK\n"
            f"🇹🇭 THB: {rates.get('THB','-')} MMK\n\n"
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

# ===========================
# အပိုင်း (ဃ) - Server & Scheduler Loop
# ===========================

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

def run_scheduler():
    while True:
        try:
            tz = pytz.timezone('Asia/Yangon')
            now = datetime.now(tz)
            
            # မနက် ၆:၀၀ အတိ (စက္ကန့် ၅၀ အတွင်း)
            if now.hour == 6 and now.minute == 0 and now.second < 50:
                send_morning_post()
                time.sleep(60) # ၁ မိနစ် ပြည့်အောင်စောင့် (Double post မဖြစ်အောင်)
            
            time.sleep(10) # ၁၀ စက္ကန့်တစ်ခါ အချိန်စစ်မယ်
        except Exception as e:
            print(f"Scheduler Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Web Server
    t1 = Thread(target=run_http)
    t1.start()
    
    # Scheduler
    t2 = Thread(target=run_scheduler)
    t2.start()
    
    # Bot Polling
    print("Bot started...")
    bot.infinity_polling()
