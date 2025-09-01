import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://example.com"
STATE_FILE = "last_state.txt"

def get_page_items():
    try:
        response = requests.get(TARGET_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items = []
        for entry in soup.select(".entry")[:10]:
            title = entry.select_one(".title").get_text(strip=True)
            date = entry.select_one(".date").get_text(strip=True)
            link = entry.select_one("a")["href"]
            items.append(f"{title}|{date}|{link}")
        return items
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return []

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

    diff = new_items - old_items
    if diff:
        for item in diff:
            notify_discord(f"📢 新着情報: {item}")
        save_state(new_items)
    else:
        notify_discord("✅ 新着なし")

if __name__ == "__main__":
    main()
