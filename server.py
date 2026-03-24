from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

app = Flask(__name__)
CORS(app)

# 메뉴 항목 — 원하는 대로 추가/수정
MENU_ITEMS = ['밀크티1', '밀크티2','티칵테일1','티칵테일2']

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 본인 스프레드시트 ID로 교체
SPREADSHEET_ID = '1rq0309WKMN_FKG9Ig092YPFKldxoI-ROvenEO6gEazc'


def get_sheet():
    """Google Sheets 연결 반환.
    Railway 환경변수 GOOGLE_CREDENTIALS_JSON 우선,
    없으면 로컬 credentials.json 파일 사용.
    """
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        creds_dict = json.loads(creds_json)
    else:
        with open('credentials.json', 'r') as f:
            creds_dict = json.load(f)

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1


def init_sheet():
    """헤더가 없으면 자동으로 첫 행에 추가"""
    ws = get_sheet()
    if not ws.row_values(1):
        ws.append_row(['시간'] + MENU_ITEMS)
        print('[초기화] 헤더 행 추가 완료')


@app.route('/record', methods=['POST'])
def record():
    """버튼 클릭 시 호출 — 해당 항목 1, 나머지 0으로 행 추가"""
    data = request.get_json()
    item = data.get('item')

    if item not in MENU_ITEMS:
        return jsonify({'ok': False, 'error': f'알 수 없는 항목: {item}'}), 400

    ws = get_sheet()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    row = [now] + [1 if m == item else 0 for m in MENU_ITEMS]
    ws.append_row(row)

    print(f'[기록] {now} | {item}')
    return jsonify({'ok': True, 'recorded': item, 'time': now})


@app.route('/history', methods=['GET'])
def history():
    """최근 기록 20개 반환"""
    ws = get_sheet()
    all_rows = ws.get_all_values()
    if not all_rows:
        return jsonify({'headers': [], 'rows': []})

    headers = all_rows[0]
    recent = all_rows[1:][-20:][::-1]
    return jsonify({'headers': headers, 'rows': recent})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    init_sheet()
    port = int(os.environ.get('PORT', 5000))
    print(f'서버 시작: http://localhost:{port}')
    app.run(host='0.0.0.0', port=port)
