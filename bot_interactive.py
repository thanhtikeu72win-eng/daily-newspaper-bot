import os
import telebot
from datetime import datetime

# Render မှာ Environment Variable အနေနဲ့ ထည့်ရပါမယ်
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# 1. Start & Archive Command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = message.text.split()
    if len(text) > 1 and text[1] == 'archive':
        msg = bot.reply_to(message, "📅 ဘယ်ရက်စွဲ လိုချင်ပါသလဲ? (ဥပမာ - 21-2-2026 လို့ ရိုက်ပေးပါ)")
        bot.register_next_step_handler(msg, process_date_step)
    else:
        bot.reply_to(message, "မင်္ဂလာပါ! Archive ရှာလိုပါက Channel Menu မှတဆင့် ဝင်ရောက်ပါ။")

# 2. Date Processing
def process_date_step(message):
    try:
        date_input = message.text.strip()
        # ရက်စွဲ Format စစ်ဆေး
        date_obj = datetime.strptime(date_input, '%d-%m-%Y')
        formatted_date = date_obj.strftime("%d %B %Y") # 21 February 2026 format
        
        # Google Search Query (site:moi.gov.mm "21 February 2026" Kyaymon)
        query = f"site:moi.gov.mm \"{formatted_date}\" Kyaymon"
        search_url = f"https://www.google.com/search?q={query}"
        
        # Result ပို့ပေးခြင်း
        reply_text = (
            f"🔍 **{formatted_date}** အတွက် ရှာဖွေမှုရလဒ်:\n\n"
            f"👇 အောက်ပါ Link ကို နှိပ်ပြီး Download ရယူပါ:\n{search_url}"
        )
        
        bot.reply_to(message, reply_text, parse_mode="Markdown")
            
    except ValueError:
        msg = bot.reply_to(message, "⚠️ ရက်စွဲမှားနေပါသည်။ (Day-Month-Year) ပုံစံဖြင့် ပြန်ရိုက်ပါ (ဥပမာ 21-2-2026)")
        bot.register_next_step_handler(msg, process_date_step)

if __name__ == "__main__":
    bot.infinity_polling()
