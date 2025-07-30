from difflib import get_close_matches
import re
import os
import json


# 입력된 회사명을 corp_list에 있는 회사명 중 가장 유사한 회사명으로 정규화
def normalize_company_name(user_input: str, corp_list: list[dict]) -> str:
    # 입력 정규화
    user_input_norm = user_input.strip().lower().replace("(주)", "").replace("주식회사", "").replace(" ", "")

    # corp_name과 corp_eng_name 둘 다 비교 대상으로 만듦
    all_names = []
    mapping = {}

    for corp in corp_list:
        kor = corp["corp_name"]
        eng = corp["corp_eng_name"]

        kor_norm = kor.lower().replace("(주)", "").replace("주식회사", "").replace(" ", "")
        eng_norm = eng.lower().replace("(주)", "").replace("co.,ltd.", "").replace(",", "").replace(" ", "")

        # 각 이름을 매핑 테이블에 저장
        all_names.extend([kor_norm, eng_norm])
        mapping[kor_norm] = kor
        mapping[eng_norm] = kor  # 반환은 항상 kor 기준

    # 유사한 이름 찾기
    matches = get_close_matches(user_input_norm, all_names, n=1, cutoff=0.6)
    if matches:
        matched = matches[0]
        return mapping[matched]

    return None


# extract chain이 준 응답에서 회사명과 연도 추출하는 함수
def parse_extracted_text(text: str) -> dict:
    company_match = re.search(r"회사\s*:\s*(.+)", text)
    year_match = re.search(r"연도\s*:\s*(\d{4}(?:,\s*\d{4})*)", text)

    company = company_match.group(1).strip() if company_match else None
    if company and company.lower() in ["없음", "none", "no", "x"]:
        company = None

    years = year_match.group(1) if year_match else "2024"
    year_list = [y.strip() for y in years.split(",")]

    return {
        "company": company,
        "year_list": year_list
    }



# 회사명으로 회사코드 가져오는 함수
def find_corporation_code(company_name: str) -> str:
    """
    사용자가 입력한 기업명을 기반으로 DART 기업코드를 반환합니다.
    유사한 기업명도 자동 정규화하여 검색합니다.
    """
    company_name = company_name.strip("'\"")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'corp_list.json')

        with open(file_path, encoding='utf-8') as f:
            corp_list = json.load(f)

    except Exception as e:
        return f"[ERROR] corp_list.json 로드 실패: {str(e)}"

    # Step 1: 정규화된 이름 찾기
    normalized_name = normalize_company_name(company_name, corp_list)
    if not normalized_name:
        return f"[ERROR] '{company_name}'에 유사한 기업명을 찾을 수 없습니다."

    # Step 2: 기업 코드 반환
    for corp in corp_list:
        if corp["corp_name"] == normalized_name:
            return corp["corp_code"]

    return f"[ERROR] '{normalized_name}'에 해당하는 기업 코드를 찾을 수 없습니다."