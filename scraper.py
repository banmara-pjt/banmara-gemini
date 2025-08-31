import json
import time
from selenium import webdriver
from bs4 import BeautifulSoup

# 保存ファイル
OUTPUT_FILE = "events.json"
# 公式サイト (Liveタグ付きのイベント一覧)
URL = "https://bang-dream.com/events?event_tag=19"

def scrape_events():
    # Seleniumブラウザ起動
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 画面を表示せずに実行
    driver = webdriver.Chrome(options=options)

    print(f"アクセス中: {URL}")
    driver.get(URL)
    time.sleep(5)  # ページ読み込み待ち（調整可）

    # ページHTML取得
    html = driver.page_source
    driver.quit()

    # BeautifulSoupで解析
    soup = BeautifulSoup(html, "html.parser")

    events_data = []
    # 各イベントを囲んでいる li
    events = soup.select("ul.liveEventList > li")

    print(f"DEBUG: {len(events)} 件のイベントを検出")

    for event in events:
        # タイトル
        title_tag = event.select_one("p.liveEventListTitle")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # 日時と場所
        date, place = "No Date", "No Place"
        info_rows = event.select(".itemInfoRow")
        for row in info_rows:
            key = row.select_one(".itemInfoColumnTitle")
            value = row.select_one(".itemInfoColumnData")
            if not key or not value:
                continue
            key_text = key.get_text(strip=True)
            if "開催日時" in key_text:
                date = value.get_text(strip=True)
            elif "場所" in key_text:
                place = value.get_text(strip=True)

        # JSON用のdictにまとめる
        events_data.append({
            "title": title,
            "date": date,
            "place": place
        })

    # JSONに保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2)

    if events_data:
        print(f"{len(events_data)} 件のイベントを保存しました → {OUTPUT_FILE}")
    else:
        print("イベント情報が見つかりませんでした")

if __name__ == "__main__":
    scrape_events()
print("Scraper finished successfully")
