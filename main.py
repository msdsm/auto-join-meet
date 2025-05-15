import datetime
import time
import webbrowser
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os

# スコープの設定（読み取り専用）
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate_google_calendar():
    """
    Google Calendar APIへの認証を行う
    """
    creds = None
    # 認証済みの場合
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # 未認証の場合json読み込む
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 次回実行用に認証情報を保存
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_today_events(service):
    """
    今日の全てのイベントを取得
    """
    now = datetime.datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + datetime.timedelta(days=1)
    
    try:
        # カレンダーイベントを取得
        events_result = service.events().list(
            calendarId='primary',
            timeMin=today_start.isoformat() + 'Z',
            timeMax=today_end.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    
    except HttpError as error:
        print(f'エラーが発生しました: {error}')
        return []

def extract_google_meet_url(event):
    """
    イベントからGoogle MeetのURLを抽出
    """
    # conferenceDataから直接URLを取得
    if 'conferenceData' in event:
        entry_points = event['conferenceData'].get('entryPoints', [])
        for entry_point in entry_points:
            if entry_point.get('entryPointType') == 'video':
                return entry_point.get('uri')
    
    description = event.get('description', '')
    meet_pattern = r'(https://meet\.google\.com/[a-z-]+)'
    matches = re.findall(meet_pattern, description)
    if matches:
        return matches[0]
    
    return None

def is_time_to_join(event_start_time):
    """
    会議に参加すべき時間かどうかをチェック
    (とりあえず)1分前かどうかで判定
    """
    now = datetime.datetime.now(event_start_time.tzinfo)
    time_diff_seconds = (now - event_start_time).total_seconds()
    # -60秒(1分前)から0秒までTrue
    return -60 <= time_diff_seconds <= 0

def join_google_meet(meet_url):
    """
    ブラウザを開いてGoogle Meetに参加
    """
    print(f"Google Meetに参加します: {meet_url}")
    webbrowser.open_new(meet_url)

def main():
    """
    メインプログラム
    """
    print("Google Meet 自動参加プログラムを開始します...")
    
    # 認証
    creds = authenticate_google_calendar()
    service = build('calendar', 'v3', credentials=creds)
    
    # 参加済みの会議を記録するセット
    joined_meetings = set()
    
    while True:
        print(f"\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - チェック中...")
        
        # 今日のイベントを取得
        events = get_today_events(service)
        
        for event in events:
            event_id = event['id']
            summary = event.get('summary', '無題')
            
            # 既に参加済みの会議はスキップ
            if event_id in joined_meetings:
                continue
            
            # Google MeetのURLを抽出
            meet_url = extract_google_meet_url(event)
            if not meet_url:
                continue
            
            # 開始時間を取得
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:  # 時間が含まれている場合
                start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                
                # 参加時間かどうかチェック
                if is_time_to_join(start_time):
                    print(f"\n会議「{summary}」に参加します。")
                    join_google_meet(meet_url)
                    joined_meetings.add(event_id)
                else:
                    # 次の会議までの時間を表示
                    time_diff = start_time - datetime.datetime.now(start_time.tzinfo)
                    if time_diff.total_seconds() > 0:
                        minutes = int(time_diff.total_seconds() / 60)
                        print(f"会議「{summary}」まで: {minutes}分")
        
        # 1分間待機
        time.sleep(60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nプログラムを終了します。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")