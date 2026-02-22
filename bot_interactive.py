import os
import requests
from bs4 import BeautifulSoup
import datetime
from urllib.parse import unquote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ChatMemberHandler
from telegram.constants import ChatMemberStatus
from flask import Flask
from threading import Thread

# --- Flask Server (Render အတွက် မရှိမဖြစ်) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Render က ပေးမယ့် Port ကို သုံးပါမယ်
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Secrets ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# URLs
KM_URL = "https://www.moi.gov.mm/km/"
MAL_URL = "https://www.moi.gov.mm/mal/"

# ===================== HELPER FUNCTIONS =====================

def get_main_menu():
    """Main Menu Buttons"""
    keyboard = [
        [InlineKeyboardButton("📰 ဒီနေ့သတင်းစာ", callback_data='today')],
        [InlineKeyboardButton("📚 အရင်ရက်များ", callback_data='archive')],
        [InlineKeyboardButton("🔔 Notification ဖွင့်နည်း", callback_data='subscribe')],
        [InlineKeyboardButton("❓ အကူအညီ", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def fetch_newspaper():
    """Fetch today's newspaper"""
    urls = [
        (KM_URL, "ကြေးမုံ"),
        (MAL_URL, "မြန်မာ့အလင်း")
    ]
    
    for url, name in urls:
        try:
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            target_path = '/km/' if 'km' in url else '/mal/'
            article_link = None
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if target_path in href and any(char.isdigit() for char in href):
                    article_link = href
                    break
            
            if not article_link:
                continue
                
            if not article_link.startswith('http'):
                full_url = "https://www.moi.gov.mm" + article_link
            else:
                full_url = article_link
            
            article_response = requests.get(full_url, timeout=30)
            article_soup = BeautifulSoup(article_response.content, 'html.parser')
            
            for link in article_soup.find_all('a', href=True):
                if link['href'].endswith('.pdf'):
                    pdf_url = link['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = "https://www.moi.gov.mm" + pdf_url
                    
                    pdf_response = requests.get(pdf_url, timeout=60)
                    filename = unquote(pdf_url.split('/')[-1])
                    
                    with open(filename, 'wb') as f:
                        f.write(pdf_response.content)
                    
                    return filename, name
                    
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            continue
    
    return None, None

# ===================== COMMAND HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome Message + Menu"""
    welcome_text = """
🇲🇲 *မြန်မာ့နေ့စဉ်သတင်းစာ Bot မှ ကြိုဆိုပါတယ်!*

ဒီ Bot က နေ့စဉ်ထုတ် သတင်းစာများဖြစ်တဲ့ ကြေးမုံနဲ့ မြန်မာ့အလင်း သတင်းစာတို့ကို အလိုအလျောက် ပို့ပေးပါတယ်။

📌 *လုပ်ဆောင်ချက်များ:*
• ဒီနေ့သတင်းစာ ရယူခြင်း
• အရင်ရက်များ ပြန်ကြည့်ခြင်း
• နေ့စဉ် Notification ရယူခြင်း

အောက်က ခလုတ်များကို နှိပ်၍ စတင်အသုံးပြုနိုင်ပါပြီ။
    """
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help Command"""
    help_text = """
📖 *အသုံးပြုနည်း လမ်းညွှန်*

*Commands များ:*
/start - ပင်မစာမျက်နှာ
/today - ဒီနေ့သတင်းစာ ရယူမယ်
/archive - အရင်ရက်များ
/subscribe - Notification ဖွင့်နည်း
/help - ဒီစာမျက်နှာ

*Channel:* @YourChannelUsername
*နေ့စဉ် မနက် ၇:၀၀ နာရီ* တွင် အလိုအလျောက် ပို့ပေးပါသည်။
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get Today's Newspaper"""
    await update.message.reply_text("⏳ သတင်းစာ ရှာဖွေနေပါသည်... ခဏစောင့်ပါ။")
    
    filename, newspaper_name = fetch_newspaper()
    
    if filename:
        today_str = datetime.datetime.now().strftime("%d-%m-%Y")
        caption = f"📰 {newspaper_name}သတင်းစာ ({today_str})"
        
        with open(filename, 'rb') as f:
            await update.message.reply_document(document=f, caption=caption)
        
        os.remove(filename)
    else:
        await update.message.reply_text("⛔ ဒီနေ့ သတင်းစာ မတွေ့ပါ။ သတင်းစာတိုက် ပိတ်ရက် ဖြစ်နိုင်ပါသည်။")

async def archive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Archive - Past Newspapers"""
    keyboard = [
        [InlineKeyboardButton("📰 ကြေးမုံ Archive", url="https://www.moi.gov.mm/km/")],
        [InlineKeyboardButton("📰 မြန်မာ့အလင်း Archive", url="https://www.moi.gov.mm/mal/")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data='back_to_menu')]
    ]
    
    await update.message.reply_text(
        "📚 *အရင်ရက်များက သတင်းစာများ*\n\nအောက်ပါ Link များတွင် ကြည့်ရှုနိုင်ပါသည်။",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Subscribe Instructions"""
    subscribe_text = """
🔔 *နေ့စဉ် Notification ရယူနည်း*

*အဆင့် ၁:* Channel ကို Join လုပ်ပါ
👉 @YourChannelUsername

*အဆင့် ၂:* Notification ဖွင့်ပါ
• Channel ထဲဝင်ပါ
• Channel နာမည်ကို နှိပ်ပါ
• 🔔 Notifications ကို Enable လုပ်ပါ

✅ ပြီးပါပြီ! နေ့စဉ် မနက် ၇:၀၀ နာရီတွင် သတင်းစာ ရောက်လာပါလိမ့်မယ်။
    """
    await update.message.reply_text(subscribe_text, parse_mode='Markdown')

# ===================== CALLBACK HANDLERS (Button Clicks) =====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Inline Button Clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'today':
        await query.message.reply_text("⏳ သတင်းစာ ရှာဖွေနေပါသည်...")
        filename, newspaper_name = fetch_newspaper()
        
        if filename:
            today_str = datetime.datetime.now().strftime("%d-%m-%Y")
            caption = f"📰 {newspaper_name}သတင်းစာ ({today_str})"
            with open(filename, 'rb') as f:
                await query.message.reply_document(document=f, caption=caption)
            os.remove(filename)
        else:
            await query.message.reply_text("⛔ ဒီနေ့ သတင်းစာ မတွေ့ပါ။")
    
    elif query.data == 'archive':
        keyboard = [
            [InlineKeyboardButton("📰 ကြေးမုံ", url="https://www.moi.gov.mm/km/")],
            [InlineKeyboardButton("📰 မြန်မာ့အလင်း", url="https://www.moi.gov.mm/mal/")],
            [InlineKeyboardButton("🔙 နောက်သို့", callback_data='back_to_menu')]
        ]
        await query.message.edit_text(
            "📚 *အရင်ရက်များက သတင်းစာများ*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'subscribe':
        await query.message.edit_text(
            "🔔 *Notification ဖွင့်နည်း*\n\n1️⃣ @YourChannelUsername ကို Join လုပ်ပါ\n2️⃣ Channel Settings မှာ Notifications ဖွင့်ပါ",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 နောက်သို့", callback_data='back_to_menu')]])
        )
    
    elif query.data == 'help':
        help_text = "📖 *Commands:*\n/today - ဒီနေ့သတင်းစာ\n/archive - အရင်ရက်များ\n/help - အကူအညီ"
        await query.message.edit_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 နောက်သို့", callback_data='back_to_menu')]])
        )
    
    elif query.data == 'back_to_menu':
        welcome_text = "🇲🇲 *မြန်မာ့နေ့စဉ်သတင်းစာ Bot*\n\nအောက်က Menu မှ ရွေးချယ်ပါ။"
        await query.message.edit_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )

# ===================== WELCOME NEW MEMBERS =====================

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new channel/group members"""
    for member in update.message.new_chat_members:
        if not member.is_bot:
            welcome_msg = f"""
👋 *ကြိုဆိုပါတယ် {member.first_name}!*

မြန်မာ့နေ့စဉ်သတင်းစာ Channel မှ ကြိုဆိုပါတယ်။

📰 နေ့စဉ် မနက် ၇:၀၀ နာရီတွင် သတင်းစာ အလိုအလျောက် ရောက်လာပါလိမ့်မယ်။

🔔 Notification ဖွင့်ထားဖို့ မမေ့ပါနဲ့!
            """
            await update.message.reply_text(welcome_msg, parse_mode='Markdown')

# ===================== MAIN =====================

def main():
    """Start the bot"""
    keep_alive()  # Render Web Server ကို စတင်ပါ
    print("Bot is starting...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("archive", archive_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    
    # Callback Handler (for inline buttons)
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Welcome new members
    # (Note: Use ChatMemberHandler in newer versions, but MessageHandler works for basic entry)
    # app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    
    # Start polling
    print("Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    from telegram.ext import MessageHandler, filters
    main()
