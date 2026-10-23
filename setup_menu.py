"""
Channel ထဲသို့ Welcome Menu ကို တစ်ကြိမ် ပို့ပြီး Pin လုပ်ပေးသော script
(GitHub Actions → Run Setup Menu Manually)
"""
import json
import os
import sys

import requests

# GitHub Secrets မှ ယူမည်
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# Admin Username (@ နှင့် Space မပါ)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Balagyi")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def api_call(method, **kwargs):
    """Telegram API ကို ခေါ်ပြီး JSON ပြန်ပေးသည် (error ဖြစ်ရင် None)"""
    try:
        res = requests.post(f"{API}/{method}", timeout=30, **kwargs)
        data = res.json()
        if not data.get("ok"):
            print(f"❌ {method} failed: {data.get('description')}")
            return None
        return data["result"]
    except Exception as e:
        print(f"❌ {method} error: {e}")
        return None


def send_pinned_menu():
    if not BOT_TOKEN or not CHANNEL_ID:
        sys.exit("Error: BOT_TOKEN / CHANNEL_ID secrets မရှိပါ")

    # Bot Username ကို အလိုအလျောက် ယူမည်
    me = api_call("getMe")
    if not me:
        sys.exit("Error: Token မမှန်ပါ")
    bot_username = me["username"]

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "📚 ယခင်သတင်းစာများ (Archive)",
                    "url": f"https://t.me/{bot_username}?start=archive",
                }
            ],
            [
                {
                    "text": "📞 Admin သို့ ဆက်သွယ်ရန်",
                    "url": f"https://t.me/{ADMIN_USERNAME}",
                }
            ],
        ]
    }

    text = (
        "📰 <b>Welcome to MyanmarNewsWatch</b>\n\n"
        "✅ နေ့စဉ် ကြေးမုံသတင်းစာများကို ဤနေရာတွင် ဖတ်ရှုနိုင်ပါသည်။\n"
        "✅ ယခင်ရက်စွဲဟောင်းများ ရှာလိုပါက Archive ခလုတ်ကို နှိပ်ပါ။"
    )

    print(f"Sending Menu to {CHANNEL_ID}...")
    msg = api_call(
        "sendMessage",
        data={
            "chat_id": CHANNEL_ID,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(keyboard),
        },
    )
    if not msg:
        sys.exit("Menu ပို့၍မရပါ (Bot သည် Channel Admin ဖြစ်ရမည်)")
    print("✅ Menu sent!")

    # Pin လုပ်မည် (Bot မှာ 'Pin Messages' အခွင့်အရေး လိုသည်)
    pinned = api_call(
        "pinChatMessage",
        data={
            "chat_id": CHANNEL_ID,
            "message_id": msg["message_id"],
            "disable_notification": True,
        },
    )
    if pinned:
        print("📌 Pinned!")
    else:
        print("⚠️ Pin မလုပ်နိုင်ပါ - Bot ကို 'Pin Messages' အခွင့်အရေး ပေးပါ (သို့) လက်ဖြင့် Pin ပါ")


if __name__ == "__main__":
    send_pinned_menu()
