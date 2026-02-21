import os
import requests
from bs4 import BeautifulSoup
import datetime

# --- GitHub Secrets မှ ရယူခြင်း ---
# ⚠️ ဒီနေရာမှာ Token တိုက်ရိုက်မထည့်ရပါ၊ GitHub Settings တွင် ထည့်ပါမည်
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
MAIN_URL = "https://www.moi.gov.mm/km/"

def send_pdf(file_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {'document': open(file_path, 'rb')}
    data = {'chat_id': CHANNEL_ID, 'caption': caption}
    requests.post(url, files=files, data=data)

def job():
    print(f"[{datetime.datetime.now()}] Job Started via GitHub Actions...")
    
    try:
        # Step 1: Main Page
        response = requests.get(MAIN_URL)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_link = None
        # PDF ပါသော Link ရှာဖွေခြင်း
        for link in soup.find_all('a', href=True):
            href = link['href']
            # '/km/' ပါပြီး ဂဏန်းပါသော Link (ဥပမာ: /km/12345)
            if '/km/' in href and any(char.isdigit() for char in href):
                 article_link = href
                 break 
        
        if not article_link:
            print("No daily link found.")
            return

        if not article_link.startswith('http'):
            full_article_url = "https://www.moi.gov.mm" + article_link
        else:
            full_article_url = article_link
            
        print(f"Found Article: {full_article_url}")

        # Step 2: Get PDF Link
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

            file_name = "daily_newspaper.pdf"
            print("Downloading PDF...")
            
            # Download PDF
            pdf_response = requests.get(pdf_url)
            with open(file_name, 'wb') as f:
                f.write(pdf_response.content)
            
            today_str = datetime.datetime.now().strftime("%d-%m-%Y")
            caption = f"Daily Newspaper ({today_str})"
            
            # Send to Telegram
            print("Sending to Telegram...")
            send_pdf(file_name, caption)
            print("Sent Successfully!")
            
        else:
            print("PDF not found inside the article.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    job()
