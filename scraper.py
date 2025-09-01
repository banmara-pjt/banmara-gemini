import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://bang-dream.com/events?event_tag=19"
STATE_FILE = "last_state.txt"

def get_page_items():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # ここでChromeの場所を明示的に指定する！
    options.binary_location = '/usr/bin/google-chrome-stable'

    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)

    items = []
    try:
        driver.get(TARGET_URL)
        
        driver.implicitly_wait(10)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        for entry in soup.select(".c-event__list_item")[:10]:
            title_element = entry.select_one(".c-event__list_title")
            date_element = entry.select_one(".c-event__list_date")
            link_element = entry.select_one("a")

            if title_element and date_element and link_element:
                title = title_element.get_text(strip=True)
                date = date_element.get_text(strip=True)
                link = link_element["href"]
                items.append(f"{title}|{date}|{link}")
            
        print("--- スクレイピング結果 ---")
        for item in items:
            print(item)
        print("--- ---------------- ---")
        
        return items

    except Exception as e:
        print(f"An error occurred during scraping with Selenium: {e}")
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

    diff = new_items - old_items
    if diff:
        for item in diff:
            notify_discord(f"📢 新着情報: {item}")
        save_state(new_items)
    else:
        notify_discord("✅ 新着なし")

if __name__ == "__main__":
    main()
