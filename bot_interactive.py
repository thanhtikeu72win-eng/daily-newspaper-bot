import os
import telebot
import requests
import schedule
import time
import pytz
import urllib.parse
from bs4 import BeautifulSoup # PDF လင့်ခ်အသစ် ရှာဖွေနိုင်ရန် ထပ်ထည့်ထားသည်
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# 1. Setup
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID') 
bot = telebot.TeleBot(BOT_TOKEN)

# ===========================
# အပိုင်း (က) - User Interactive (Direct Download & Archive)
# ===========================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = message.text.split()
    if len(text) > 1 and text[1] == 'archive':
        bot.reply_to(message, "📅 ဘယ်ရက်စွဲ လိုချင်ပါသလဲ? (ဥပမာ - 23-2-2026)")
    else:
        msg = (
            "🙏 မင်္ဂလာပါ!\n"
            "✅ သတင်းစာများကို Channel တွင် မနက်ခင်းတိုင်း တင်ပေးပါသည်။\n\n"
            "⚠️ Channel တွင် မရောက်လာသေးပါက အောက်ပါခလုတ်များမှ ယနေ့သတင်းစာကို **တိုက်ရိုက် Download** ယူနိုင်ပါသည်။\n\n"
            "🔍 _ယခင်နေ့များအတွက် ရှာလိုပါက ရက်စွဲ (ဥပမာ - 20-2-2026) ကို ရိုက်ထည့်ပါ။_"
        )
        markup = InlineKeyboardMarkup()
        # Direct Download Buttons
        btn_km = InlineKeyboardButton("📥 ယနေ့ ကြေးမုံ", callback_data="get_today_km")
        btn_mal = InlineKeyboardButton("📥 ယနေ့ မြန်မာ့အလင်း", callback_data="get_today_mal")
        
        markup.row(btn_km)
        markup.row(btn_mal)
        bot.reply_to(message, msg, reply_markup=markup, parse_mode="Markdown")

# --- Direct PDF Finder Function ---
def get_direct_pdf_link(base_url):
    try:
        res = requests.get(base_url, timeout=15)
        soup = BeautifulSoup(res.content, 'html.parser')
        article_link = None
        target_path = '/km/' if 'km' in base_url else '/mal/'
        
        for link in soup.find_all('a', href=True):
            if target_path in link['href'] and any(c.isdigit() for c in link['href']):
                article_link = link['href']
                break
                
        if not article_link: return None
        
        full_article = article_link if article_link.startswith('http') else "https://www.moi.gov.mm" + article_link
        res2 = requests.get(full_article, timeout=15)
        soup2 = BeautifulSoup(res2.content, 'html.parser')
        
        for link in soup2.find_all('a', href=True):
            if link['href'].lower().endswith('.pdf'):
                pdf_url = link['href']
                return pdf_url if pdf_url.startswith('http') else "https://www.moi.gov.mm" + pdf_url
        return None
    except:
        return None

# --- Callback Handler for Direct Download Buttons ---
@bot.callback_query_handler(func=lambda call: call.data in ["get_today_km", "get_today_mal"])
def handle_get_today(call):
    paper_name = "ကြေးမုံ" if call.data == "get_today_km" else "မြန်မာ့အလင်း"
    url_to_search = "https://www.moi.gov.mm/km/" if call.data == "get_today_km" else "https://www.moi.gov.mm/mal/"
    
    # နှိပ်တဲ့သူကို Loading လေးပြမယ်
    bot.answer_callback_query(call.id, f"{paper_name} ကို ရှာဖွေနေပါသည်...")
    waiting_msg = bot.send_message(call.message.chat.id, f"🔍 ယနေ့ {paper_name} ကို Web Server မှ ဆွဲထုတ်နေပါသည်... အနည်းငယ် စောင့်ပါဗျ။")
    
    # Link ရှာဖွေမည်
    pdf_link = get_direct_pdf_link(url_to_search)
    
    # ဆွဲထုတ်နေပါသည် စာကို ပြန်ဖျက်မည်
    bot.delete_message(call.message.chat.id, waiting_msg.message_id)
    
    if pdf_link:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"⬇️ {paper_name} Download ယူရန်နှိပ်ပါ", url=pdf_link))
        bot.send_message(call.message.chat.id, f"✅ ရရှိပါပြီ! အောက်ပါခလုတ်ကို နှိပ်၍ တိုက်ရိုက် Download ဆွဲပါ။", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, f"⛔ ယနေ့အတွက် {paper_name} Website တွင် မတင်ရသေးပါ (သို့) ဆာဗာ ကျပ်နေပါသည်။ နောက်မှ ထပ်စမ်းကြည့်ပါ။")

# --- Old Archive Handler ---
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    try:
        text = message.text.strip()
        if "-" in text or "/" in text:
            raw_query = f'site:moi.gov.mm "{text}" Kyaymon'
            encoded_query = urllib.parse.quote(raw_query)
            search_url = f"https://www.google.com/search?q={encoded_query}"

            markup = InlineKeyboardMarkup()
            btn = InlineKeyboardButton("📥 ဖတ်ရှုရန် / Download ယူရန်", url=search_url)
            markup.add(btn)
            
            reply_text = f"🔍 **{text}** အတွက် ရှာဖွေမှုရလဒ်:\n\n👇 အောက်ပါခလုတ်ကို နှိပ်ပါ။"
            bot.reply_to(message, reply_text, reply_markup=markup, parse_mode="Markdown")
        else:
            pass 
    except Exception as e:
        print(f"Error: {e}")
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

def run_scheduler():
    while True:
        try:
            tz = pytz.timezone('Asia/Yangon')
            now = datetime.now(tz)
            
            if now.hour == 6 and now.minute == 0 and now.second < 10:
                send_morning_post()
                time.sleep(60) 
            
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
    return "Bot is running with Direct Download!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t1 = Thread(target=run_http)
    t1.start()
    
    t2 = Thread(target=run_scheduler)
    t2.start()
    
    bot.infinity_polling()
