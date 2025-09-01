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
            
            place_elements = entry.select(".itemInfoColumnData")
            if len(place_elements) > 1:
                place_text = place_elements[1].get_text(strip=True)
            else:
                place_text = "場所不明"

            if title_element and date_element:
                title = title_element.get_text(strip=True)
                date = date_element.get_text(strip=True)
                link = entry["href"]

                # 差分判定用に、前回と同じ形式の文字列（title|date|link）を'norm'に格納
                # 通知用に、場所を含んだ文字列を'raw'に格納
                items.append({
                    "norm": f"{title}|{date}|{link}",
                    "raw": f"{title} | {date} | {place_text}"
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
        f.write("\n".join([item["norm"] for item in items]))

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
        notify_discord(f"🔴 **スクレイピング失敗（収集日時：{current_time}）**\nサイトの形式が変更されたか、その他の問題が発生しました。")
        return

    new_set = set(item["norm"] for item in new_items_list)
    diff_norms = new_set - old_items
    diff_items = [item for item in new_items_list if item["norm"] in diff_norms]

    if not diff_items and new_items_list:
        notify_discord(f"✅ **正常に動作しています（新着情報はありません）（収集日時：{current_time}）**")
    elif not new_items_list:
        notify_discord(f"⚠️ **警告：データ件数がゼロでした（サイト要確認）（収集日時：{current_time}）**")
    else:
        notify_discord(f"📢 **新着情報が見つかりました（収集日時：{current_time}）**")
        for item in diff_items:
            notify_discord(f"    - {item['raw']}")

    save_state(new_items_list)

if __name__ == "__main__":
    main()
