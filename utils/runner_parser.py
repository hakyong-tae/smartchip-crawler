import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_runner_result(usedata: str, bib: str) -> dict:
    cache_file = f"results_cache/{usedata}.json"
    os.makedirs("results_cache", exist_ok=True)

    # 1. 캐시 확인
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if bib in cached:
            return cached[bib]

    try:
        options = Options()
        # options.add_argument("--headless")  # 필요 시 활성화
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        url = f"https://smartchip.co.kr/return_data_livephoto.asp?nameorbibno={bib}&usedata={usedata}"
        driver.get(url)

        # bib 요소 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h6.green'))
        )

        # 결과 없음 처리
        if "검색 결과가 없습니다" in driver.page_source or "결과가 없습니다" in driver.page_source:
            driver.quit()
            return {"error": "결과가 없습니다. bib 번호 또는 대회 ID를 확인하세요."}

        # ✅ 이름 가져오기 (정확한 구조 반영)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h6.white font"))
            )
            runner_name = driver.find_element(By.CSS_SELECTOR, "h6.white font").text.strip()
        except:
            runner_name = "정보 없음"

        # ✅ bib 번호 가져오기
        try:
            bib_elem = driver.find_element(By.CSS_SELECTOR, 'h6.green + h6.white + h6.green')
            bib_number = bib_elem.text.strip()
        except:
            bib_number = bib  # fallback

        # ✅ 기록 파싱
        font_elements = driver.find_elements(By.CSS_SELECTOR, "font")
        raw_texts = [el.text.strip() for el in font_elements if el.text.strip()]
        texts = []

        for t in raw_texts:
            if "Pace" in t or "min/km" in t:
                continue
            if t:
                texts.append(t)

        # ✅ Km 기준으로 4개씩 묶어서 순서대로 기록 생성
        records = []
        i = 0
        while i + 3 < len(texts):
            if "Km" in texts[i]:
                records.append({
                    "지점": texts[i],
                    "시간": texts[i+1],
                    "도착시각": texts[i+2],
                    "페이스": texts[i+3]
                })
                i += 4
            else:
                i += 1

        driver.quit()

        result = {
            "이름": runner_name,
            "배번호": bib_number,
            "기록": records
        }

        # 캐시에 저장
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                all_cache = json.load(f)
        else:
            all_cache = {}

        all_cache[bib] = result
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_cache, f, ensure_ascii=False, indent=2)

        return result

    except Exception as e:
        return {"error": f"파싱 중 오류 발생: {str(e)}"}
