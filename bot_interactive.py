import os
import telebot
from flask import Flask
from threading import Thread

# 1. Telegram Bot Setup
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# 2. Bot Logic (Start & Archive)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Check if user clicked the deep link
    text = message.text.split()
    if len(text) > 1 and text[1] == 'archive':
        bot.reply_to(message, "📅 ဘယ်ရက်စွဲ လိုချင်ပါသလဲ? (ဥပမာ - 21-2-2026 ဟု ရိုက်ပေးပါ)")
        # Next step handler is not persistent in server restarts, so stateless is better here.
        # But for simplicity, we use simple reply logic below.
    else:
        bot.reply_to(message, "မင်္ဂလာပါ! Archive ရှာလိုပါက Channel Menu မှတဆင့် ဝင်ရောက်ပါ။")

# 3. Message Listener (Date Handler)
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    # ရိုးရှင်းအောင် ရက်စွဲပုံစံ ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    text = message.text.strip()
    
    # ရက်စွဲဖြစ်နိုင်ချေရှိသော စာများ (ရိုးရှင်းသော စစ်ဆေးမှု)
    if "-" in text or "/" in text:
        bot.reply_to(message, f"🔍 **{text}** အတွက် Google တွင် ရှာဖွေရန် Link:\n\nhttps://www.google.com/search?q=site:moi.gov.mm+\"{text}\"+Kyaymon")
    else:
        # ရက်စွဲမဟုတ်ရင် ဘာမှမလုပ် (သို့) ကူညီစာပို့
        pass

# 4. Dummy Web Server for Render (Keep Alive)
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

if __name__ == "__main__":
    keep_alive() # Web Server စဖွင့်မယ်
    bot.infinity_polling() # Bot စနားထောင်မယ်
