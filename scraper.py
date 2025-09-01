import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

URL = "https://bang-dream.com/events"
JSON_FILE = "events.json"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def load_events():
    if not os.path.exists(JSON_FILE):
        return {"timestamp": None, "events": []}
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(events):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def scrape_events():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # 公式サイトのイベントリストを取得
    event_items = soup.select(".p-event__list-item")

    events = []
    for item in event_items:
        title = item.select_one(".p-event__list-item__title").get_text(strip=True)
        date = item.select_one(".p-event__list-item__date").get_text(strip=True)
        link = item.select_one("a")["href"]

        events.append({
            "title": title,
            "date": date,
            "link": link
        })

    return events


def send_discord_notification(new_events):
    if not WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL が設定されていません")
        return

    content = "**新しいイベント情報が追加されました！**\n\n"
    for event in new_events:
        content += f"📌 {event['date']} - [{event['title']}]({event['link']})\n"

    payload = {"content": content}
    requests.post(WEBHOOK_URL, json=payload)


def main():
    old_data = load_events()
    old_events = old_data.get("events", [])

    new_events = scrape_events()

    # 差分チェック
    diff = [e for e in new_events if e not in old_events]

    if diff:
        print(f"新しいイベント {len(diff)} 件を検出しました")
        send_discord_notification(diff)
    else:
        print("新着なし")

    # データ更新
    save_events({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": new_events
    })


if __name__ == "__main__":
    main()
