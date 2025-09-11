import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE" # ここにDiscord Webhook URLを設定

# ウェブページのURL
url = "https://bang-dream.com/events"

def scrape_events():
    """ウェブサイトからイベント情報をスクレイピングする"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        events_section = soup.find("section", class_="c-section-event-list")
        event_items = events_section.find_all("li", class_="c-section-event-list__item")
        
        events = []
        for item in event_items:
            title_tag = item.find("h3", class_="c-section-event-list__item__ttl")
            title = title_tag.text.strip() if title_tag else "タイトルなし"

            date_tag = item.find("p", class_="c-section-event-list__item__date")
            date = date_tag.text.strip() if date_tag else ""

            location_tag = item.find("p", class_="c-section-event-list__item__place")
            location = location_tag.text.strip() if location_tag else ""

            link_tag = item.find("a", class_="c-section-event-list__item__link")
            link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ""

            events.append({
                "title": title,
                "date": date,
                "location": location,
                "link": link
            })
        return events
    except Exception as e:
        print(f"スクレイピング中にエラーが発生しました: {e}")
        return None

def format_event_for_file(event):
    """イベント情報をファイル保存用にフォーマットする"""
    return f"{event['title']}|{event['date']}|{event['link']}"

def format_event_for_discord(event):
    """イベント情報をDiscord通知用にフォーマットする"""
    return f"- **{event['title']}**\n  - 日程: {event['date']}\n  - 場所: {event['location']}\n  - 詳細: {urljoin(url, event['link']) if event['link'] else 'なし'}"

def urljoin(base, url_path):
    """ベースURLと相対パスを結合する"""
    if url_path.startswith('/'):
        return base.split('/events')[0] + url_path
    return url_path

def send_discord_notification(message, username="イベント通知Bot"):
    """Discordに通知を送る"""
    payload = {
        "content": message,
        "username": username
    }
    requests.post(WEBHOOK_URL, json=payload)

def load_last_state(file_path="last_state.txt"):
    """前回保存したイベント情報をファイルから読み込む"""
    events = {}
    last_scrape_time = None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines and lines[0].startswith("収集日時:"):
                time_str = lines[0].replace("収集日時: ", "").strip()
                last_scrape_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                lines = lines[1:]
            
            for line in lines:
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    title, date, link = parts[0], parts[1], parts[2]
                    events[title] = {"date": date, "link": link}
    except FileNotFoundError:
        print("前回保存されたファイルが見つかりません。")
    except Exception as e:
        print(f"ファイル読み込み中にエラーが発生しました: {e}")
    
    return events, last_scrape_time

def save_current_state(events, file_path="last_state.txt"):
    """現在のイベント情報をファイルに保存する"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for event in events:
            f.write(format_event_for_file(event) + "\n")

def main():
    last_state, last_scrape_time = load_last_state()
    current_events = scrape_events()
    
    if current_events is None:
        print("スクレイピングに失敗したため、処理を中断します。")
        return

    # 差分を検出
    new_events = []
    if last_state:
        last_state_set = {f"{k}|{v['date']}|{v['link']}" for k, v in last_state.items()}
    else:
        last_state_set = set()

    current_events_set = {format_event_for_file(e) for e in current_events}
    new_events_data = current_events_set - last_state_set
    
    for event_str in new_events_data:
        parts = event_str.split("|")
        if len(parts) >= 3:
            title, date, link = parts[0], parts[1], parts[2]
            for event in current_events:
                if event['title'] == title and event['date'] == date:
                    new_events.append(event)
                    break
    
    # ログ出力
    print("\n--- last_state.txtの内容 ---")
    if last_scrape_time:
        print(f"収集日時: {last_scrape_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("前回保存されたファイルが見つかりません。")
    if last_state:
        for title, info in last_state.items():
            print(f"{title}|{info['date']}|{info['link']}")
    print("------------------------")
    print(f"--- 収集ログ（収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}） ---")
    print("\n--- 今回取得したデータ ---")
    for event in current_events:
        print(f"  - {event['title']} | {event['date']} | {event['location']}")
    
    print("\n--- 前回保存されていたデータ ---")
    if last_state:
        for event in last_state.items():
            title, info = event
            print(f"  - {title}|{info['date']}|{info['link']}")
    else:
        print("前回保存されたデータがありません。")
    print("------------------------")

    # Discord通知
    if new_events:
        message = "新しいイベント情報が公開されました！\n\n"
        for event in new_events:
            message += format_event_for_discord(event) + "\n"
        send_discord_notification(message)
        print("新しいイベント情報をDiscordに送信しました。")
    else:
        print("新しいイベント情報はありませんでした
