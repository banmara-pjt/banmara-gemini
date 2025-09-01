import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://example.com"  # 監視対象のページ

STATE_FILE = "last_state.json"
EVENTS_FILE = "events.json"


def get_page_items():
    response = requests.get(TARGET_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    items = []
    for entry in soup.select(".entry")[:10]:
        title = entry.select_one(".title").get_text(strip=True)
        date = entry.select_one(".date").get_text(strip=True)
        link = entry.select_one("a")["href"]
        items.append({"title": title, "date": date, "link": link})
    return items


def load_last_state():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def save_events(items):
    # 日本時間のタイムスタンプを追加
    now_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "timestamp": now_jst,
        "events": items
    }
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def notify_discord(item):
    # 日本時間の現在時刻を追加
    now_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")

    if item["title"] == "新着なし":
        message = f"🔍 新着なし\n確認時刻: {now_jst}"
    else:
        message = (
            f"📢 **新着情報**\n"
            f"📝 {item['title']}\n"
            f"📅 {item['date']}\n"
            f"🔗 {item['link']}\n"
            f"確認時刻: {now_jst}"
        )
    requests.post(WEBHOOK_URL, json={"content": message})


def main():
    new_items = get_page_items()
    old_items = load_last_state()

    # 辞書リストの比較用に (title, date, link) のタプル化
    old_set = {(i["title"], i["date"], i["link"]) for i in old_items}
    new_set = {(i["title"], i["date"], i["link"]) for i in new_items}

    diff = new_set - old_set
    if diff:
        for title, date, link in diff:
            notify_discord({"title": title, "date": date, "link": link})
        save_state(new_items)
    else:
        notify_discord({"title": "新着なし", "date": "", "link": ""})

    # 常に events.json を更新
    save_events(new_items)


if __name__ == "__main__":
    main()
