import os
import requests
import json

# GitHub Secrets မှ ယူမည်
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
# Admin Username (Space မပါ)
ADMIN_USERNAME = "Balagyi"

def send_pinned_menu():
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Error: Token or Channel ID missing!")
        return

    # Bot Username ကို အလိုအလျောက် ယူမည်
    try:
        me = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()
        bot_username = me['result']['username']
    except:
        print("Error: Invalid Token")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # ခလုတ် (၂) ခု
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📚 ယခင်သတင်းစာများ (Archive)", "url": f"https://t.me/{bot_username}?start=archive"}
            ],
            [
                {"text": "📞 Admin သို့ ဆက်သွယ်ရန်", "url": f"https://t.me/{ADMIN_USERNAME}"}
            ]
        ]
    }

    data = {
        "chat_id": CHANNEL_ID,
        "text": (
            "📰 **Welcome to MyanmarNewsWatch**\n\n"
            "✅ နေ့စဉ် ကြေးမုံသတင်းစာများကို ဤနေရာတွင် ဖတ်ရှုနိုင်ပါသည်။\n"
            "✅ ယခင်ရက်စွဲဟောင်းများ ရှာလိုပါက Archive ခလုတ်ကို နှိပ်ပါ။"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }

    print(f"Sending Menu to {CHANNEL_ID}...")
    response = requests.post(url, data=data)
    print("Response:", response.text)

if __name__ == "__main__":
    send_pinned_menu()
