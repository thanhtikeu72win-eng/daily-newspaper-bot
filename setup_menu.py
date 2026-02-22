import os
import requests
import json

# GitHub Secrets မှ Token ယူမည်
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
# Admin Username ကိုတော့ ဒီမှာ ပြင်ထည့်ပါ
ADMIN_USERNAME = "Than Htike Win" 

def send_pinned_menu():
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Error: BOT_TOKEN or CHANNEL_ID not found in secrets!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Bot Username ကို အရင်လှမ်းယူမယ် (Link ချိတ်ဖို့)
    bot_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()
    bot_username = bot_info['result']['username']

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📚 ယခင်သတင်းစာများ (Archive)", "url": f"https://t.me/{bot_username}?start=archive"}
            ],
            [
                {"text": "📞 Admin သို့ ဆက်သွယ်ရန်", "url": f"https://t.me/{ADMIN_USERNAME}"}
            ],
            [
                {"text": "🌐 MOI Website", "url": "https://www.moi.gov.mm"}
            ]
        ]
    }

    data = {
        "chat_id": CHANNEL_ID,
        "text": (
            "📰 **Daily Newspaper Control Panel**\n\n"
            "✅ နေ့စဉ် သတင်းစာများကို မနက် ၆:၃၀ တွင် အလိုအလျောက် ပို့ပေးပါမည်။\n"
            "✅ ယခင်ရက်စွဲဟောင်းများ (Archive) ကို ရှာဖွေလိုပါက အောက်ပါခလုတ်ကို နှိပ်ပါ။"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }

    print(f"Sending Menu to {CHANNEL_ID}...")
    response = requests.post(url, data=data)
    print("Response:", response.text)

if __name__ == "__main__":
    send_pinned_menu()
