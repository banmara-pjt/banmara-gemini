import os
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://bang-dream.com/events?event_tag=19"
STATE_FILE = "last_state.txt"

def get_page_items():
    items = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(TARGET_URL)
            
            # ライブ情報が読み込まれるまで待機
            page.wait_for_selector(".liveEventListInfo", timeout=10000)

            soup = BeautifulSoup(page.content(), "html.parser")
            
            # .liveEventListInfo クラスを持つ要素をすべて取得
            for entry in soup.select(".liveEventListInfo"):
                title_element = entry.select_one(".liveEventListTitle")
                
                date_and_place = entry.select(".itemInfoColumnData")
                
                if title_element and len(date_and_place) >= 2:
                    title = title_element.get_text(strip=True)
                    date = date_and_place[0].get_text(strip=True)
                    place = date_and_place[1].get_text(strip=True)
                    
                    # リンクを親の a タグから取得
                    link = entry.find_parent("a")["href"]

                    items.append({
                        "norm": f"{title}|{date}|{link}",
                        "raw": f"{title} | {date} | {place}"
                    })
            browser.close()
        return items

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None

def load_last_state():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if not line.strip().startswith("#")]
        return set(lines)

def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"# Saved Date: {current_time}\n")
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

    # --- 収集ログ ---
    print("--- 収集ログ（収集日時: {}） ---".format(current_time))
    
    print("\n--- 今回取得したデータ ---")
    if new_items_list:
        for item in new_items_list:
            print(f"  - {item['raw']}")
    else:
        print("  データなし")
        
    print("\n--- 前回保存されていたデータ ---")
    if old_items:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("# Saved Date:"):
                saved_date = first_line.replace("# Saved Date: ", "")
                print(f"  （取得日時: {saved_date}）")
        for item in old_items:
            print(f"  - {item}")
    else:
        print("  データなし")

    # --- ログ出力終了 ---

    if new_items_list is None:
        notify_discord(f"🔴 **スクレイピング失敗（収集日時：{current_time}）（Gemini）**\nサイトの形式が変更されたか、その他の問題が発生しました。")
        return

    new_set = set(item["norm"] for item in new_items_list)
    diff_norms = new_set - old_items
    diff_items = [item for item in new_items_list if item["norm"] in diff_norms]

    if not diff_items and new_items_list:
        notify_discord(f"✅ **正常に動作しています（新着情報はありません）（収集日時：{current_time}）（Gemini）**")
    elif not new_items_list:
        notify_discord(f"⚠️ **警告：データ件数がゼロでした（サイト要確認）（収集日時：{current_time}）（Gemini）**")
    else:
        sorted_diff = sorted(list(diff_items), key=lambda x: x['raw'])
        notify_discord(f"📢 **新着情報が見つかりました（収集日時：{current_time}）（Gemini）**")
        for item in sorted_diff:
            notify_discord(f"    - {item['raw']}")

    save_state(new_items_list)

if __name__ == "__main__":
    main()
