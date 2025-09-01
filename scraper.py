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
            place_element = entry.select(".itemInfoColumnData")
            
            if title_element and date_element:
                title = title_element.get_text(strip=True)
                date = date_element.get_text(strip=True)
                link = entry["href"]
                place = place_element[1].get_text(strip=True) if len(place_element) > 1 else ""
                items.append(f"{title} | {date} | {place} | {link}")
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
        f.write("\n".join(items))

def notify_discord(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def main():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_items_list = get_page_items()
    old_items = load_last_state()

    if new_items_list is None:
        notify_discord(f"⚠️ サイトにアクセスできません（収集日時：{current_time}）")
        return

    new_items = set(new_items_list)
    diff = new_items - old_items

    if not new_items_list:
        notify_discord(f"⚠️ データ件数がゼロでした（サイト要確認）（収集日時：{current_time}）")
    elif not diff:
        notify_discord(f"ℹ️ 新着はありません（動作は正常です）（収集日時：{current_time}）")
    else:
        sorted_diff = [item for item in new_items_list if item in diff]  # 公式順
        notify_discord(f"✅ 新着があります（収集日時：{current_time}）")
        for item in sorted_diff:
            notify_discord(f"    - {item}")
        save_state(new_items)

if __name__ == "__main__":
    main()
