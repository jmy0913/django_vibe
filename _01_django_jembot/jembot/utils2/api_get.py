import requests
import os

# 제무재표 api로 받아오는 함수
def get_financial_state(
    corp_code: str,
    bsns_year: str,
    reprt_code: str,
    fs_div: str
) -> list[str]:

    DART_API_KEY = os.getenv("DART_API_KEY")

    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,
        "fs_div": fs_div,
    }


    response = requests.get(url, params=params)
    data = response.json()

    data_list = []

    if data["status"] == "000":
        for item in data["list"]:
            name = item["account_nm"]
            curr = item["thstrm_amount"]
            prev = item.get("frmtrm_amount", "-")
            currency = item.get("currency", "KRW")
            data_list.append(f"{name} : {curr} (당기), {prev} (전기), 통화: {currency}")
        return data_list
    else:
        return [f"[API 오류] {data.get('message', '정의되지 않은 오류')}"]