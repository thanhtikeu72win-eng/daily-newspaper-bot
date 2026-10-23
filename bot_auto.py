"""
Manual backup script (GitHub Actions → Run workflow)
ကြေးမုံ (မရရင် မြန်မာ့အလင်း) PDF ကို Telegram Channel သို့ ပို့သည်။
"""
import os
import sys
import datetime
import urllib.parse
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

# --- Secrets ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

BASE = "https://www.moi.gov.mm"
PAPERS = [
    {"name": "ကြေးမုံ", "url": f"{BASE}/km/", "path": "/km/"},
    {"name": "မြန်မာ့အလင်း", "url": f"{BASE}/mal/", "path": "/mal/"},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MM_TZ = datetime.timezone(datetime.timedelta(hours=6, minutes=30))
FILE_LIMIT = 49 * 1024 * 1024


def full_url(href):
    return href if href.startswith("http") else urllib.parse.urljoin(BASE + "/", href)


def send_telegram_file(file_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            print(f"Uploading {file_path} to Telegram...")
            res = requests.post(
                url,
                files={"document": f},
                data={"chat_id": CHANNEL_ID, "caption": caption},
                timeout=120,
            )
        if res.status_code == 200:
            print("✅ File Sent Successfully!")
            return True
        print(f"❌ Failed to send: {res.text}")
        return False
    except Exception as e:
        print(f"❌ Error sending file: {e}")
        return False


def send_telegram_message(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHANNEL_ID, "text": text},
            timeout=30,
        )
    except Exception as e:
        print(f"❌ Error sending message: {e}")


def check_and_download(paper):
    name = paper["name"]
    print(f"🔍 Checking {name}...")
    try:
        res = requests.get(paper["url"], headers=HEADERS, timeout=30)
        soup = BeautifulSoup(res.content, "html.parser")

        candidates = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            url = full_url(href)
            if (
                paper["path"] in href
                and any(c.isdigit() for c in href)
                and url.rstrip("/") != paper["url"].rstrip("/")
                and url not in candidates
            ):
                candidates.append(url)

        if not candidates:
            print(f"⚠️ No link found for {name}.")
            return None

        for article_url in candidates[:5]:
            print(f"📄 Trying page: {article_url}")
            try:
                res2 = requests.get(article_url, headers=HEADERS, timeout=30)
                soup2 = BeautifulSoup(res2.content, "html.parser")
                for a in soup2.find_all("a", href=True):
                    if a["href"].lower().split("?")[0].endswith(".pdf"):
                        pdf_url = full_url(a["href"])
                        print(f"⬇️ Downloading PDF: {pdf_url}")
                        pdf = requests.get(pdf_url, headers=HEADERS, timeout=120)
                        if pdf.status_code != 200 or not pdf.content:
                            print(f"⚠️ PDF download failed: HTTP {pdf.status_code}")
                            continue
                        if len(pdf.content) > FILE_LIMIT:
                            print("⚠️ PDF too large for Telegram")
                            send_telegram_message(f"📰 {name}: {pdf_url}")
                            return "SENT_LINK"
                        filename = unquote(pdf_url.split("?")[0].split("/")[-1]) or "newspaper.pdf"
                        with open(filename, "wb") as f:
                            f.write(pdf.content)
                        print(f"💾 Saved as: {filename}")
                        return filename
            except Exception as e:
                print(f"⚠️ Page error ({article_url}): {e}")

        print(f"⚠️ PDF not found for {name}.")
        return None
    except Exception as e:
        print(f"❌ Error processing {name}: {e}")
        return None


def job():
    today_str = datetime.datetime.now(MM_TZ).strftime("%d-%m-%Y")
    print(f"--- Starting Job: {today_str} ---")

    for paper in PAPERS:
        result = check_and_download(paper)
        if result == "SENT_LINK":
            return
        if result and send_telegram_file(result, f"📰 {paper['name']}သတင်းစာ ({today_str})"):
            return

    print("⛔ No newspapers found.")
    send_telegram_message("⛔ ဒီနေ့ သတင်းစာရှာမတွေ့ပါ (သို့) ပိတ်ရက်ဖြစ်နိုင်ပါသည်။")


if __name__ == "__main__":
    if not BOT_TOKEN or not CHANNEL_ID:
        sys.exit("BOT_TOKEN / CHANNEL_ID secrets မရှိပါ")
    job()
