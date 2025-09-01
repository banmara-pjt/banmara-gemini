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
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        for entry in soup.select("a[href^='/events/']")[:10]:
            title_element = entry.select_one(".liveEventListTitle")
            date_element = entry.select_one(".itemInfoColumnData")
            place_element = entry.select_one(".itemInfoColumnData:nth-of-type(2)")

            if title_element and date_element:
                title = title_element.get_text(strip=True)
                date = date_element.get_text(strip=True)
                place = place_element.get_text(strip=True) if place_element else ""
                
                # 差異判定用のキーはタイトル + 日付
                key = f"{title}|{date}"
                
                # 通知用の整形アイテム
                items.append({
                    "key": key,
                    "title": title,
                    "date": date,
                    "place": place
                })
        return items

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None
    finally:
        driver.quit()

def load_last_state():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        keys = [item["key"] for item in items]
        f.write("\n".join(keys))

def notify_discord(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def main():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_items = get_page_items()
    old_keys = load_last_state()

    if new_items is None:
        notify_discord(f"⚠️ **スクレイピング失敗（収集日時：{current_time}）**\nサイトの形式が変更されたか、その他の問題が発生しました。")
        return

    new_keys = set(item["key"] for item in new_items)
    diff_keys = new_keys - old_keys

    if not diff_keys and new_items:
        notify_discord(f"ℹ️ **新着はありません（動作は正常です）（収集日時：{current_time}）**")
    elif not new_items:
        notify_discord(f"⚠️ **データ件数がゼロでした（サイト要確認）（収集日時：{current_time}）**")
    else:
        notify_discord(f"✅ **新着があります（収集日時：{current_time}）**")
        for item in new_items:
            if item["key"] in diff_keys:
                msg = f"📝 {item['title']}\n📅 {item['date']}\n📍 {item['place']}"
                notify_discord(msg)
        save_state(new_items)

if __name__ == "__main__":
    main()
