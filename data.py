import os
import requests
from dotenv import load_dotenv

load_dotenv()
DART_API_KEY = os.getenv("DART_API_KEY")

CORP_CODES = {
    "LG 이노텍": "00105961",
}


def get_financials(company_name: str) -> dict:
    corp_code = CORP_CODES.get(company_name)
    if not corp_code:
        return {}

    financials = {}
    for year in [2022, 2023, 2024]:
        params = {
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": "11011",
            "fs_div": "CFS",
        }
        items = requests.get(
            "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", params=params
        ).json().get("list", [])

        data = {}
        for item in items:
            nm = item.get("account_nm", "").strip()
            amt = item.get("thstrm_amount", "").replace(",", "")
            if not amt or int(amt) == 0:
                continue
            if nm == "매출액" and "매출액" not in data:
                data["매출액"] = int(amt) // 100_000_000
            if nm in ("영업이익", "영업이익(손실)") and "영업이익" not in data:
                data["영업이익"] = int(amt) // 100_000_000
            if nm == "당기순이익" and "순이익" not in data:
                data["순이익"] = int(amt) // 100_000_000
        financials[year] = data

    return {"company": company_name, "financials": financials}


def get_corp_code(company_name: str) -> str:
    # TODO: dart-fss로 기업 코드 조회
    pass


def get_financial_statements(corp_code: str) -> list:
    # TODO: dart-fss로 재무제표 조회
    pass


if __name__ == "__main__":
    result = get_financials("LG 이노텍")
    if not result:
        print("데이터 없음")
    else:
        print(f"[{result['company']}] 재무 데이터 (단위: 억원)\n")
        print(f"{'연도':<6} {'매출액':>10} {'영업이익':>10} {'순이익':>10}")
        print("-" * 40)
        for year, data in result["financials"].items():
            print(f"{year:<6} {data['매출액']:>10,} {data['영업이익']:>10,} {data['순이익']:>10,}")
