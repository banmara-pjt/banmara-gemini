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
        
        # セレクタを新しいHTML構造に合わせる
        for entry in soup.select("a[href^='/events/']")[:10]:
            title_element = entry.select_one(".liveEventListTitle")
            date_element = entry.select_one(".itemInfoColumnData")
            
            if title_element and date_element:
                title = title_element.get_text(strip=True)
                date = date_element.get_text(strip=True)
                link = entry["href"]
                items.append(f"{title}|{date}|{link}")
            
        return items

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        # スクレイピング失敗時はNoneを返す
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

    # 1. スクレイピングが失敗した場合
    if new_items_list is None:
        notify_discord(f"🔴 **スクレイピング失敗（収集日時：{current_time}）**\nサイトの形式が変更されたか、その他の問題が発生しました。")
        return

    # スクレイピング成功後、セットに変換
    new_items = set(new_items_list)
    diff = new_items - old_items

    # 2. 正常に作動して前回と変更がなかった場合
    if not diff:
        notify_discord(f"✅ **正常に動作しています（新着情報はありません）（収集日時：{current_time}）**")
    # 3. サイトの形式が変わり、データをとれなかった場合
    elif not new_items:
        notify_discord(f"⚠️ **警告：サイトの形式が変更された可能性があります（収集日時：{current_time}）**\n情報が取得できませんでした。コードの修正が必要かもしれません。")
        
    # 4. 新着情報があった場合
    else:
        sorted_diff = sorted(list(diff))
        
        notify_discord(f"📢 **新着情報が見つかりました（収集日時：{current_time}）**")
        for item in sorted_diff:
            notify_discord(f"    - {item}")
        
        save_state(new_items)

if __name__ == "__main__":
    main()
