import sys
import os
import json
import requests
import time
from datetime import datetime

DEFAULT_START_ID = 85
SUCCESS_LIMIT = 7
FAIL_LIMIT = 10

def load_last_checked_id():
    path = "output/last_checked_id.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f).get("last_checked_id", DEFAULT_START_ID)
    return DEFAULT_START_ID

def save_last_checked_id(race_id):
    os.makedirs("output", exist_ok=True)
    with open("output/last_checked_id.json", "w") as f:
        json.dump({"last_checked_id": race_id}, f)

def build_usedata(race_id: int, base_date: str):
    dt = datetime.strptime(base_date, "%Y-%m-%d")
    yyyymm = dt.strftime("%Y%m")
    return f"{yyyymm}0000{str(race_id).zfill(3)}"

def is_race_valid(race_id: int, base_date: str):
    try:
        usedata = build_usedata(race_id, base_date)
        url = f"https://smartchip.co.kr/Search_Ballyno.html?usedata={usedata}"
        print(f"🔍 Checking usedata={usedata} → {url}")
        res = requests.get(url, timeout=5)
        res.raise_for_status()

        if "기록조회" in res.text or "기록 검색" in res.text or "bib number" in res.text:
            print("✅ Valid race")
            return {
                "race_id": race_id,
                "usedata": usedata,
                "url": url
            }
        else:
            print("❌ Not valid")
            return None
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None

def crawl_races(base_date: str):
    start_id = load_last_checked_id()
    print(f"\n🚀 Starting crawl from race_id: {start_id}")

    success_count = 0
    fail_count = 0
    race_list = []

    for race_id in range(start_id, 10000):
        result = is_race_valid(race_id, base_date)
        time.sleep(1.0)  # 예의상 1초 대기

        if result:
            race_list.append(result)
            success_count += 1
            if success_count >= SUCCESS_LIMIT:
                save_last_checked_id(start_id + 1)
                print(f"✅ Success limit reached ({SUCCESS_LIMIT}). Next start_id = {start_id + 1}")
                break
        else:
            fail_count += 1
            if fail_count >= FAIL_LIMIT:
                save_last_checked_id(start_id)
                print(f"🚫 Fail limit reached ({FAIL_LIMIT}). Will retry from {start_id} next time.")
                break

    # 저장
    output_filename = f"output/events_{base_date}.json"
    os.makedirs("output", exist_ok=True)
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(race_list, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved {len(race_list)} races to {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❗ Usage: python races_crawler.py YYYY-MM-DD")
        sys.exit(1)

    base_date = sys.argv[1]  # e.g., '2025-05-18'
    crawl_races(base_date)
