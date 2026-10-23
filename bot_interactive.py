"""
Daily Newspaper Bot (Render)
- မနက် ၆:၀၀  : ငွေလဲနှုန်း / ဆီဈေး Morning Post
- မနက် ၆:၀၅+ : ကြေးမုံ (မရရင် မြန်မာ့အလင်း) PDF ကို Channel သို့ အလိုအလျောက်ပို့ (မရသေးရင် ၁၀ မိနစ်တစ်ခါ ပြန်စမ်း၊ ၈:၀၀ အထိ)
- ခလုတ်နှိပ်ရင် PDF ကို တိုက်ရိုက်ပို့ပေးသည်

Environment variables (Render): BOT_TOKEN, CHANNEL_ID
"""

import os
import time
import urllib.parse
from datetime import datetime
from threading import Thread
from urllib.parse import unquote

import pytz
import requests
import telebot
from bs4 import BeautifulSoup
from flask import Flask
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# ===========================
# 1. Setup
# ===========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
PORT = int(os.environ.get("PORT", 8080))

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN environment variable မရှိပါ")

bot = telebot.TeleBot(BOT_TOKEN)
MM_TZ = pytz.timezone("Asia/Yangon")

BASE = "https://www.moi.gov.mm"
PAPERS = {
    "km": {"name": "ကြေးမုံ", "url": f"{BASE}/km/", "path": "/km/"},
    "mal": {"name": "မြန်မာ့အလင်း", "url": f"{BASE}/mal/", "path": "/mal/"},
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TELEGRAM_FILE_LIMIT = 49 * 1024 * 1024  # Bot upload limit ~50MB


def now_mm():
    return datetime.now(MM_TZ)


def full_url(href):
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    return urllib.parse.urljoin(BASE + "/", href)


def safe_send(chat_id, text, **kwargs):
    """Markdown error ဖြစ်ရင် parse_mode မပါဘဲ ပြန်ပို့မည်"""
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"send_message error: {e}")
        if kwargs.get("parse_mode"):
            kwargs.pop("parse_mode")
            try:
                return bot.send_message(chat_id, text, **kwargs)
            except Exception as e2:
                print(f"send_message retry error: {e2}")
        return None


# ===========================
# 2. Scraping Helpers
# ===========================
def find_pdf_link(paper_key):
    """
    MOI category page မှ နောက်ဆုံးထုတ် Article များကို ဖွင့်ပြီး PDF link ရှာသည်။
    ပထမ link မှာ PDF မရှိရင် နောက် link (အများဆုံး ၅ ခု) ကို ဆက်စမ်းသည်။
    """
    info = PAPERS[paper_key]
    try:
        res = requests.get(info["url"], headers=HEADERS, timeout=30)
        soup = BeautifulSoup(res.content, "html.parser")

        candidates = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            url = full_url(href)
            if (
                info["path"] in href
                and any(c.isdigit() for c in href)
                and url.rstrip("/") != info["url"].rstrip("/")
                and url not in candidates
            ):
                candidates.append(url)

        for article_url in candidates[:5]:
            try:
                res2 = requests.get(article_url, headers=HEADERS, timeout=30)
                soup2 = BeautifulSoup(res2.content, "html.parser")
                for a in soup2.find_all("a", href=True):
                    if a["href"].lower().split("?")[0].endswith(".pdf"):
                        return full_url(a["href"])
            except Exception as e:
                print(f"Article fetch error ({article_url}): {e}")
        return None
    except Exception as e:
        print(f"Scraping Error ({paper_key}): {e}")
        return None


def download_pdf(pdf_url):
    """PDF ကို download ဆွဲပြီး (filename, bytes) ပြန်ပေးသည်"""
    try:
        res = requests.get(pdf_url, headers=HEADERS, timeout=120)
        if res.status_code != 200 or not res.content:
            print(f"PDF download failed: HTTP {res.status_code}")
            return None, None
        filename = unquote(pdf_url.split("?")[0].split("/")[-1]) or "newspaper.pdf"
        return filename, res.content
    except Exception as e:
        print(f"PDF download error: {e}")
        return None, None


def send_paper(chat_id, paper_key, with_loading=False):
    """သတင်းစာ PDF ကို ရှာ → download → Telegram သို့ ပို့။ အောင်မြင်ရင် True"""
    name = PAPERS[paper_key]["name"]
    today_str = now_mm().strftime("%d-%m-%Y")

    pdf_url = find_pdf_link(paper_key)
    if not pdf_url:
        return False

    filename, data = download_pdf(pdf_url)
    if data and len(data) <= TELEGRAM_FILE_LIMIT:
        try:
            bot.send_document(
                chat_id,
                (filename, data),
                caption=f"📰 {name}သတင်းစာ ({today_str})",
                timeout=120,
            )
            return True
        except Exception as e:
            print(f"send_document error: {e}")

    # ဖိုင်ကြီးလွန်း/ပို့မရရင် Link ပေးမည်
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"⬇️ {name} Download ယူရန် နှိပ်ပါ", url=pdf_url))
    sent = safe_send(chat_id, f"📰 {name}သတင်းစာ ({today_str})", reply_markup=markup)
    return sent is not None


# ===========================
# 3. User Handlers
# ===========================
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_name = message.from_user.first_name if message.from_user else ""
    msg = (
        f"🙏 မင်္ဂလာပါ {user_name}!\n\n"
        "📰 **ယနေ့ သတင်းစာများ ရယူရန်**\n"
        "အောက်ပါ ခလုတ်များကို နှိပ်၍ တိုက်ရိုက် Download ရယူနိုင်ပါသည်။\n\n"
        "📅 **ရက်ဟောင်းများ ရှာလိုလျှင်**\n"
        "ရက်စွဲကို ရိုက်ထည့်ပါ (ဥပမာ - 21-2-2026)"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📥 ကြေးမုံ (Today)", callback_data="dl_km"),
        InlineKeyboardButton("📥 မြန်မာ့အလင်း (Today)", callback_data="dl_mal"),
    )
    try:
        bot.reply_to(message, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"/start error: {e}")


@bot.callback_query_handler(func=lambda call: call.data in ("dl_km", "dl_mal"))
def handle_download_buttons(call):
    paper_key = call.data.split("_")[1]
    name = PAPERS[paper_key]["name"]
    chat_id = call.message.chat.id

    try:
        bot.answer_callback_query(call.id, f"{name} ကို ရှာဖွေနေပါသည်...")
    except Exception:
        pass

    loading = safe_send(
        chat_id,
        f"🔍 **{name}** ယနေ့ထုတ် PDF ကို ရှာဖွေနေပါသည်... ခေတ္တစောင့်ပါ...",
        parse_mode="Markdown",
    )

    ok = send_paper(chat_id, paper_key)

    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except Exception:
            pass

    if not ok:
        safe_send(
            chat_id,
            f"⚠️ **{name}** ယနေ့စာစောင် Web Page တွင် မတွေ့ရှိရသေးပါ။ (ခေတ္တအကြာမှ ပြန်စမ်းပါ)",
            parse_mode="Markdown",
        )


@bot.message_handler(func=lambda msg: True)
def date_search(message):
    try:
        text = (message.text or "").strip()
        if text and ("-" in text or "/" in text):
            raw_query = f'site:moi.gov.mm "{text}" Kyaymon'
            search_url = "https://www.google.com/search?q=" + urllib.parse.quote(raw_query)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔍 Google တွင် ရှာဖွေရန်", url=search_url))
            bot.reply_to(
                message,
                f"📆 **{text}** အတွက် Archive ရှာဖွေမှု:",
                reply_markup=markup,
                parse_mode="Markdown",
            )
    except Exception as e:
        print(f"date_search error: {e}")


# ===========================
# 4. Morning Post (Market Data)
# ===========================
def get_fuel_prices():
    try:
        res = requests.get(
            "https://maxenergy.com.mm/fuel-prices-list/", headers=HEADERS, timeout=15
        )
        if res.status_code != 200:
            return f"⛽️ စက်သုံးဆီဈေး: ချိတ်ဆက်၍မရပါ (Error {res.status_code})\n"

        soup = BeautifulSoup(res.content, "html.parser")
        table = soup.find("table")
        if not table:
            return "⛽️ စက်သုံးဆီဈေး: Max Website တွင် ဇယားရှာမတွေ့ပါ\n"

        rows = table.find_all("tr")
        if len(rows) < 2:
            return "⛽️ စက်သုံးဆီဈေး: Data အလွတ်ဖြစ်နေပါသည်\n"

        cols = rows[1].find_all("td")
        if len(cols) < 5:
            return "⛽️ စက်သုံးဆီဈေး: Website ပုံစံပြောင်းသွားပါသည်\n"

        return (
            "⛽️ **စက်သုံးဆီဈေး (Max - YGN)**\n"
            f"▪️ 92: {cols[1].text.strip()}\n"
            f"▪️ 95: {cols[2].text.strip()}\n"
            f"▪️ Diesel: {cols[3].text.strip()}\n"
            f"▪️ P-Diesel: {cols[4].text.strip()}\n"
        )
    except requests.exceptions.Timeout:
        return "⛽️ စက်သုံးဆီဈေး: Connection လေးလံနေပါသည်\n"
    except Exception as e:
        print(f"Max Energy Error: {e}")
        return "⛽️ စက်သုံးဆီဈေး: Server Error (or) Website Changed\n"


def get_cbm_rates():
    try:
        data = requests.get("https://forex.cbm.gov.mm/api/latest", timeout=15).json()
        rates = data["rates"]
        date_str = data.get("info", "")

        def r(code):
            return str(rates.get(code, "N/A")).replace(",", "")

        return (
            f"🏦 **ဗဟိုဘဏ် ငွေလဲလှယ်နှုန်း** ({date_str})\n"
            f"🇺🇸 USD: {r('USD')} Ks\n"
            f"🇪🇺 EUR: {r('EUR')} Ks\n"
            f"🇸🇬 SGD: {r('SGD')} Ks\n"
            f"🇹🇭 THB: {r('THB')} Ks\n"
        )
    except Exception as e:
        print(f"CBM Error: {e}")
        return "🏦 CBM Rate: Not Available\n"


def get_gold_price():
    return (
        "🏆 **ရန်ကုန်ရွှေအသင်း (YGEA) ရည်ညွှန်းဈေး**\n"
        "▪️ Website တွင် ဝင်ရောက်ကြည့်ရှုပါ: https://www.ygea.org.mm\n"
    )


def send_morning_post():
    if not CHANNEL_ID:
        print("CHANNEL_ID မသတ်မှတ်ထားပါ")
        return
    market_note = (
        "📉 _(ပြင်ပပေါက်ဈေးများသည် အချိန်နှင့်အမျှ ပြောင်းလဲနိုင်ပါသဖြင့် "
        "သက်ဆိုင်ရာ Dealer များထံတွင် အတည်ပြုပါ)_\n"
    )
    final_msg = (
        "🌤 **မင်္ဂလာမနက်ခင်းပါ**\n"
        "➖➖➖➖➖➖➖➖➖➖\n\n"
        f"{get_cbm_rates()}\n"
        f"{get_fuel_prices()}\n"
        f"{get_gold_price()}\n"
        f"{market_note}\n"
        "🗞 _ဒီနေ့ သတင်းစာ ခဏအကြာတွင် ရောက်ရှိပါမည်..._"
    )
    if safe_send(CHANNEL_ID, final_msg, parse_mode="Markdown"):
        print("Morning briefing sent!")


# ===========================
# 5. Daily Newspaper Job
# ===========================
def daily_paper_job():
    """ကြေးမုံ ရရင် ပြီး၊ မရမှ မြန်မာ့အလင်း။ အောင်မြင်ရင် True"""
    print(f"--- Newspaper job: {now_mm():%d-%m-%Y %H:%M} ---")
    for key in ("km", "mal"):
        if send_paper(CHANNEL_ID, key):
            print(f"✅ {PAPERS[key]['name']} sent")
            return True
    print("⚠️ No newspaper found this attempt")
    return False


# ===========================
# 6. Scheduler
# ===========================
state = {"post": None, "paper": None, "notfound": None, "last_try": 0.0}


def run_scheduler():
    while True:
        try:
            if CHANNEL_ID:
                now = now_mm()
                today = now.date()
                minutes = now.hour * 60 + now.minute

                # ၆:၀၀ - ၆:၅၉ : Morning post (တစ်ရက်တစ်ခါ)
                if 360 <= minutes < 420 and state["post"] != today:
                    state["post"] = today
                    send_morning_post()

                # ၆:၀၅ - ၇:၅၉ : သတင်းစာ (မရသေးရင် ၁၀ မိနစ်တစ်ခါ ပြန်စမ်း)
                if (
                    365 <= minutes < 480
                    and state["paper"] != today
                    and time.time() - state["last_try"] >= 600
                ):
                    state["last_try"] = time.time()
                    if daily_paper_job():
                        state["paper"] = today

                # ၈:၀၀ ထိ မရသေးရင် အကြောင်းကြား (တစ်ရက်တစ်ခါ)
                if (
                    480 <= minutes < 540
                    and state["paper"] != today
                    and state["notfound"] != today
                ):
                    state["notfound"] = today
                    safe_send(
                        CHANNEL_ID,
                        "⛔ ဒီနေ့ သတင်းစာရှာမတွေ့ပါ (သို့) ပိတ်ရက်ဖြစ်နိုင်ပါသည်။",
                    )
        except Exception as e:
            print(f"Scheduler Error: {e}")
        time.sleep(20)


# ===========================
# 7. Web Server (Uptime ping အတွက်)
# ===========================
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


@app.route("/health")
def health():
    return {"status": "ok", "time": now_mm().isoformat()}


def run_http():
    app.run(host="0.0.0.0", port=PORT, threaded=True)


# ===========================
# 8. Main
# ===========================
if __name__ == "__main__":
    Thread(target=run_http, daemon=True).start()
    Thread(target=run_scheduler, daemon=True).start()

    print("Bot started...")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
