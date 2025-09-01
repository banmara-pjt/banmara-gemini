import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def get_live_info():
    """Seleniumを使ってライブ情報を取得する関数"""
    options = Options()
    options.add_argument("--headless")
    
    # この部分は、GitHub Actionsが自動で設定してくれるため、このままでOK
    driver = webdriver.Chrome(options=options)
    
    url = "https://bang-dream.com/events?event_tag=19"
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-event-list__item"))
        )
    except Exception as e:
        print("ページの読み込みに失敗しました。")
        driver.quit()
        return []

    html_content = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    event_items = soup.find_all('li', class_='c-event-list__item')

    live_info_list = []
    for item in event_items:
        try:
            band_name = item.find('p', class_='event-card-info__head-title').get_text(strip=True)
            date = item.find('p', class_='event-card-info__date').get_text(strip=True)
            title = item.find('p', class_='event-card-info__title').get_text(strip=True)
            place = item.find('p', class_='event-card-info__place').get_text(strip=True)
            live_info_list.append({
                "band_name": band_name,
                "date": date,
                "title": title,
                "place": place
            })
        except AttributeError:
            continue
    
    return live_info_list

def main():
    """メイン処理"""
    data_file = "live_data.json"
    old_data = []

    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            old_data = json.load(f)

    new_data = get_live_info()

    if new_data:
        old_titles = {d['title'] for d in old_data}
        new_events = [event for event in new_data if event['title'] not in old_titles]
        
        if new_events:
            print("🎉 新着ライブ情報が見つかりました！")
            for event in new_events:
                print(f"・{event['title']} - {event['date']} @ {event['place']}")
            
            # ここにDiscord通知のコードを追加します。
            # 次のステップで、bot.pyを作成し、この部分から呼び出します。
        else:
            print("新着情報はありませんでした。")

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
    else:
        print("ライブ情報を取得できませんでした。")

if __name__ == "__main__":
    main()
