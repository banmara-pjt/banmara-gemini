import os
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://bang-dream.com/events"
STATE_FILE = "last_state.txt"

def get_page_items():
    items = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(TARGET_URL)
            
            page.wait_for_selector(".c-section-event-list", timeout=10000)

            soup = BeautifulSoup(page.content(), "html.parser")
            
            for entry in soup.select(".c-section-event-list__item"):
                title_element = entry.select_one(".c-section-event-list__item__ttl")
                date_element = entry.select_one(".c-section-event-list__item__date")
                place_element = entry.select_one(".c-section-event-list__item__place")
                link_element = entry.select_one(".c-section-event-list__item__link")
                
                title = title_element.get_text(strip=True) if title_element else ""
                date = date_element.get_text(strip=True) if date_element else ""
                place = place_element.get_text(strip=True) if place_element else ""
                link = link_element["href"] if link_element and "href" in link_element.attrs else ""
                
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
    
    # === デバッグ用 ===
    print("\n--- last_state.txtの内容 ---")
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        print(f.read())
    print("------------------------")
    # === デバッグ終了 ===
    
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        # 取得日時の行をスキップ
        if lines and "収集日時:" in lines[0]:
            lines = lines[1:]
        
        return set(line.strip() for line in lines)

def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(f"収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n".join([item["norm"] for item in items]))

def notify_discord(message, use_timestamp=False):
    try:
        if use_timestamp:
            jst = timezone(timedelta(hours=9))
            jst_time = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S JST")
            message = f"{message} (タイムスタンプ: {jst_time})"
        
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def main():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_items_list = get_page_items()
    old_items = load_last_state()

    print("--- 収集ログ（収集日時: {}） ---".format(current_time))
    
    print("\n--- 今回取得したデータ ---")
    if new_items_list:
        for item in new_items_list:
            print(f"  - {item['raw']}")
    else:
        print("  データなし")
        
    print("\n--- 前回保存されていたデータ ---")
    if old_items:
        for item in old_items:
            print(f"  - {item}")
    else:
        print("  データなし")

    if new_items_list is None:
        notify_discord(f"🔴 **スクレイピング失敗（収集日時：{current_time}）（Gemini）**\nサイトの形式が変更されたか、その他の問題が発生しました。", use_timestamp=True)
        return

    new_set = set(item["norm"] for item in new_items_list)
    old_set = set(old_items)
    diff_norms = new_set - old_set
    diff_items = [item for item in new_items_list if item["norm"] in diff_norms]

    if not diff_items and new_items_list:
        notify_discord(f"✅ **正常に動作しています（新着情報はありません）**")
    elif not new_items_list:
        notify_discord(f"⚠️ **警告：データ件数がゼロでした（サイト要確認）**")
    else:
        sorted_diff = sorted(list(diff_items), key=lambda x: x['raw'])
        notify_discord(f"📢 **新着情報が見つかりました**")
        for item in sorted_diff:
            notify_discord(f"    - {item['raw']}")

    save_state(new_items_list)

if __name__ == "__main__":
    main()
