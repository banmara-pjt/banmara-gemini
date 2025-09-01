import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options # Serviceは使わない

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://bang-dream.com/events?event_tag=19"
STATE_FILE = "last_state.txt"

def get_page_items():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # ここでServiceもexecutable_pathも指定しない！
    driver = webdriver.Chrome(options=options)

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

# load_last_state(), save_state(), notify_discord(), main() は変更なし
# ... (省略)
