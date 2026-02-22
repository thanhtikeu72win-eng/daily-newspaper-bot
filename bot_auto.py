import os
import requests
from bs4 import BeautifulSoup
import datetime
from urllib.parse import unquote

# --- Secrets ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# URLs
KM_URL = "https://www.moi.gov.mm/km/"
MAL_URL = "https://www.moi.gov.mm/mal/"

def send_telegram_file(file_path, caption):
    """File ကို Telegram သို့ ပို့ခြင်း"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHANNEL_ID, 'caption': caption}
            print(f"Uploading {file_path} to Telegram...")
            response = requests.post(url, files=files, data=data, timeout=120) # Timeout တိုးထားသည်
            if response.status_code == 200:
                print("✅ File Sent Successfully!")
                return True
            else:
                print(f"❌ Failed to send: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error sending file: {e}")
        return False

def send_telegram_message(text):
    """စာသား Message ပို့ခြင်း"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHANNEL_ID, 'text': text}
    requests.post(url, data=data)

def check_and_download(url, newspaper_name):
    print(f"🔍 Checking {newspaper_name}...")
    try:
        # Website ကို ချိတ်ဆက်ခြင်း (Timeout 30s)
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_link = None
        target_path = '/km/' if 'km' in url else '/mal/'
        
        # Link ရှာဖွေခြင်း logic
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Link ထဲမှာ target path ပါပြီး ဂဏန်းတွေ ပါရမယ် (ရက်စွဲ)
            if target_path in href and any(char.isdigit() for char in href):
                 article_link = href
                 break # ပထမဆုံးတွေ့တာကို ယူမယ် (Latest)
        
        if not article_link:
            print(f"⚠️ No link found for {newspaper_name}.")
            return None

        full_article_url = article_link if article_link.startswith('http') else "https://www.moi.gov.mm" + article_link
        print(f"📄 Found Page: {full_article_url}")

        # PDF ရှာခြင်း
        article_response = requests.get(full_article_url, timeout=30)
        article_soup = BeautifulSoup(article_response.content, 'html.parser')
        
        pdf_url = None
        for link in article_soup.find_all('a', href=True):
            if link['href'].lower().endswith('.pdf'):
                pdf_url = link['href']
                break
        
        if pdf_url:
            full_pdf_url = pdf_url if pdf_url.startswith('http') else "https://www.moi.gov.mm" + pdf_url
            print(f"⬇️ Downloading PDF: {full_pdf_url}")
            
            # Download (Timeout 120s)
            pdf_response = requests.get(full_pdf_url, timeout=120)
            
            # ဖိုင်နာမည် ရယူခြင်း
            original_filename = unquote(full_pdf_url.split('/')[-1])
            
            with open(original_filename, 'wb') as f:
                f.write(pdf_response.content)
            
            print(f"💾 Saved as: {original_filename}")
            return original_filename
        else:
            print(f"⚠️ PDF not found inside page.")
            return None

    except Exception as e:
        print(f"❌ Error processing {newspaper_name}: {e}")
        return None

def job():
    today_str = datetime.datetime.now().strftime("%d-%m-%Y")
    print(f"--- Starting Job: {today_str} ---")
    
    # ၁. ကြေးမုံ
    km_file = check_and_download(KM_URL, "Kyemon")
    if km_file:
        caption = f"📰 ကြေးမုံသတင်းစာ ({today_str})"
        success = send_telegram_file(km_file, caption)
        if success:
            return # ကြေးမုံရရင် ပြီးပြီ

    # ၂. မြန်မာ့အလင်း (ကြေးမုံမရမှ ရှာမယ်)
    mal_file = check_and_download(MAL_URL, "MyanmarAlin")
    if mal_file:
        caption = f"📰 မြန်မာ့အလင်းသတင်းစာ ({today_str})"
        success = send_telegram_file(mal_file, caption)
        if success:
            return

    # ၃. နှစ်ခုလုံး မတွေ့ရင်
    print("⛔ No newspapers found.")
    send_telegram_message("⛔ ဒီနေ့ သတင်းစာတိုက်များပိတ်ပါသည်။")

if __name__ == "__main__":
    job()
