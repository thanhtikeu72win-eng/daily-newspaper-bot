import requests
import json

# --- ပြင်ဆင်ရန် ---
BOT_TOKEN = "7793780937:AAGGzXmJl3mN7n6YYxYlB0JPnZAtvAZzWeQ"  # BotFather ဆီက Token
CHANNEL_ID = "@kyaymoneNews"       # မိတ်ဆွေ Channel ID
ADMIN_USERNAME = "Than Htike Win" # Admin ရဲ့ Username (ဥပမာ: mgmg123) - @ မပါရ
# ------------------

def send_pinned_menu():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # ခလုတ်များ ဖန်တီးခြင်း
    keyboard = {
        "inline_keyboard": [
            [
                # ၁. Archive (Bot ဆီမှာ သွားရှာခိုင်းမယ်)
                {"text": "📚 ယခင်သတင်းစာများ (Archive)", "url": f"https://t.me/{get_bot_username()}?start=archive"}
            ],
            [
                # ၂. Admin ဆီ ဆက်သွယ်ရန်
                {"text": "📞 Admin သို့ ဆက်သွယ်ရန်", "url": f"https://t.me/{ADMIN_USERNAME}"}
            ],
            [
                # ၃. Website Link
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

    response = requests.post(url, data=data)
    print(response.json())

def get_bot_username():
    # Bot username ကို အလိုအလျောက် ဆွဲယူခြင်း
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
    return r.json()['result']['username']

if __name__ == "__main__":
    send_pinned_menu()
