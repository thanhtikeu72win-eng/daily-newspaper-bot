import os
import telebot
from datetime import datetime

# Render မှာ Environment Variable အနေနဲ့ ထည့်ပါ
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ၁. Start Command (Menu ကနေ လာရင် start=archive ဆိုပြီး ပါလာမယ်)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # အကယ်၍ Link ကနေ archive ပါလာရင်
    if len(message.text.split()) > 1 and message.text.split()[1] == 'archive':
        msg = bot.reply_to(message, "📅 ဘယ်ရက်စွဲ လိုချင်ပါသလဲ? (ဥပမာ - 21-02-2026 ဟု ရိုက်ထည့်ပါ)")
        bot.register_next_step_handler(msg, process_date_step)
    else:
        bot.reply_to(message, "မင်္ဂလာပါ! သတင်းစာ Archive ရှာလိုပါက Channel မှတဆင့် ဝင်ရောက်ပါ။")

# ၂. ရက်စွဲရိုက်ထည့်လိုက်သောအခါ လုပ်ဆောင်မည့်အလုပ်
def process_date_step(message):
    try:
        date_str = message.text.strip()
        # ရက်စွဲ Format စစ်ဆေးခြင်း
        datetime.strptime(date_str, '%d-%m-%Y')
        
        bot.reply_to(message, f"🔍 {date_str} အတွက် သတင်းစာ ရှာဖွေနေပါသည်...\n(ဒီနေရာမှာ Download Logic ဆက်ရေးရပါမယ်)")
        
        # ဒီနေရာမှာ bot_auto.py ထဲက check_and_download function ကို 
        # ပြန်ခေါ်သုံးပြီး ပို့ပေးလို့ရပါတယ်
        
    except ValueError:
        msg = bot.reply_to(message, "⚠️ ရက်စွဲမှားယွင်းနေပါသည်။ ကျေးဇူးပြု၍ DD-MM-YYYY ပုံစံဖြင့် ပြန်ရိုက်ပါ။ (ဥပမာ 21-02-2026)")
        bot.register_next_step_handler(msg, process_date_step)

if __name__ == "__main__":
    bot.infinity_polling()
