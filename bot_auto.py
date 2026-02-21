import os
import requests
from bs4 import BeautifulSoup
import datetime

# --- GitHub Secrets ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# URLs
KM_URL = "https://www.moi.gov.mm/km/"
MAL_URL = "https://www.moi.gov.mm/mal/"

def send_telegram_file(file_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHANNEL_ID, 'caption': caption}
            response = requests.post(url, files=files, data=data)
            print(f"File Sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending file: {e}")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHANNEL_ID, 'text': text}
    requests.post(url, data=data)
    print("Message Sent.")

def check_and_download(url, newspaper_name):
    print(f"Checking {newspaper_name}...")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_link = None
        # PDF ပါသော Link ရှာဖွေခြင်း (ရက်စွဲပါသော Link)
        target_path = '/km/' if 'km' in url else '/mal/'
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            # '/km/' သို့မဟုတ် '/mal/' ပါပြီး ဂဏန်းပါသော Link
            if target_path in href and any(char.isdigit() for char in href):
                 article_link = href
                 break 
        
        if not article_link:
            print(f"No daily link found for {newspaper_name}.")
            return None

        if not article_link.startswith('http'):
            full_article_url = "https://www.moi.gov.mm" + article_link
        else:
            full_article_url = article_link
            
        print(f"Found Article: {full_article_url}")

        # PDF Link ရှာခြင်း
        article_response = requests.get(full_article_url)
        article_soup = BeautifulSoup(article_response.content, 'html.parser')
        
        pdf_url = None
        for link in article_soup.find_all('a', href=True):
            if link['href'].endswith('.pdf'):
                pdf_url = link['href']
                break
        
        if pdf_url:
            if not pdf_url.startswith('http'):
                pdf_url = "https://www.moi.gov.mm" + pdf_url

            print(f"Downloading PDF from {pdf_url}...")
            pdf_response = requests.get(pdf_url)
            
            file_name = f"{newspaper_name}.pdf"
            with open(file_name, 'wb') as f:
                f.write(pdf_response.content)
            
            return file_name
        else:
            print(f"PDF not found inside {newspaper_name}.")
            return None

    except Exception as e:
        print(f"Error checking {newspaper_name}: {e}")
        return None

def job():
    today_str = datetime.datetime.now().strftime("%d-%m-%Y")
    
    # ၁. ကြေးမုံ (Kyemon) ရှာမယ်
    km_file = check_and_download(KM_URL, "Kyemon")
    if km_file:
        caption = f"📰 ကြေးမုံသတင်းစာ ({today_str})"
        send_telegram_file(km_file, caption)
        return # ပြီးပြီ၊ ရပ်မယ်

    # ၂. မတွေ့ရင် မြန်မာ့အလင်း (Myanmar Alin) ရှာမယ်
    mal_file = check_and_download(MAL_URL, "MyanmarAlin")
    if mal_file:
        caption = f"📰 မြန်မာ့အလင်းသတင်းစာ ({today_str})"
        send_telegram_file(mal_file, caption)
        return # ပြီးပြီ၊ ရပ်မယ်

    # ၃. နှစ်ခုလုံး မတွေ့ရင် (ပိတ်ရက်)
    print("No newspapers found today.")
    send_telegram_message("⛔ ဒီနေ့သတင်းစာတိုက်များပိတ်ပါသည်")

if __name__ == "__main__":
    job()
