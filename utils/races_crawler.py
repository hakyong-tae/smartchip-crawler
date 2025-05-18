import requests
import json
import os
import time
from bs4 import BeautifulSoup

# ===== 설정 =====
STATE_FILE = "last_checked_id.json"
DEFAULT_START_ID = 85
MAX_SUCCESS = 7
MAX_FAIL = 10
RACE_URL_TEMPLATE = "https://www.smartchip.co.kr/web/race/{}/record.jsp"

# ===== 상태 불러오기 / 저장 =====
def load_last_checked_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("last_checked_id", DEFAULT_START_ID)
    return DEFAULT_START_ID

def save_last_checked_id(race_id):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_checked_id": race_id}, f)

# ===== 단일 대회 기록 조회 가능 여부 판별 =====
def is_race_valid(race_id):
    try:
        url = RACE_URL_TEMPLATE.format(race_id)
        print(f"🔍 Checking race_id {race_id}... ", end="")
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        if "기록조회" in soup.text or "기록 검색" in soup.text or "Record" in soup.text:
            print("✅ Valid race")
            return True
        else:
            print("❌ Not valid")
            return False
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return False

# ===== 메인 크롤링 루프 =====
def crawl_races():
    start_id = load_last_checked_id()
    print(f"🚀 Starting crawl from race_id: {start_id}")

    success_count = 0
    fail_count = 0

    for race_id in range(start_id, 10000):
        is_valid = is_race_valid(race_id)
        time.sleep(1.0)  # 서버 부하 방지 (1초 대기)

        if is_valid:
            success_count += 1
            if success_count >= MAX_SUCCESS:
                save_last_checked_id(start_id + 1)
                print(f"✅ Success limit reached ({MAX_SUCCESS}). Next start_id will be {start_id + 1}.")
                break
        else:
            fail_count += 1
            if fail_count >= MAX_FAIL:
                save_last_checked_id(start_id)  # 실패 시 같은 start_id 유지
                print(f"🚫 Fail limit reached ({MAX_FAIL}). Will retry from {start_id} next time.")
                break

# ===== 실행 =====
if __name__ == "__main__":
    crawl_races()
