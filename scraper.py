import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://bang-dream.com/events?event_tag=19"
STATE_FILE = "last_state.txt"

def get_page_items():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)

    items = []
    try:
        driver.get(TARGET_URL)
        
        driver.implicitly_wait(10)
        
        print("--- ページHTML ---")
        print(driver.page_source)
        print("--- ---------- ---")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        for entry in soup.select("a[href^='/events/']")[:10]:
            title_element = entry.select_one(".liveEventListTitle")
            date_element = entry.select_one(".itemInfoColumnData")
            
            if title_element and date_element:
                title = title_element.get_text(strip=True)
                date = date_element.get_text(strip=True)
                link = entry["href"]
                items.append(f"{title}|{date}|{link}")
            
        print("--- スクレイピング結果 ---")
        for item in items:
            print(item)
        print("--- ---------------- ---")
        
        return items

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return []
    finally:
        driver.quit()

def load_last_state():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(items))

def notify_discord(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def main():
    new_items = set(get_page_items())
    old_items = load_last_state()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    diff = new_items - old_items
    if diff:
        sorted_diff = sorted(list(diff))
        
        # 収集日時を含めた通知メッセージ
        notify_discord(f"📢 **新着情報が見つかりました（収集日時：{current_time}）**")
        for item in sorted_diff:
            notify_discord(f"    - {item}")
        
        save_state(new_items)
    else:
        # 収集日時を含めた通知メッセージ
        notify_discord(f"✅ **新着情報はありません（収集日時：{current_time}）**")

if __name__ == "__main__":
    main()
