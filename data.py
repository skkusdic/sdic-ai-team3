import os
from dotenv import load_dotenv

load_dotenv()
DART_API_KEY = os.getenv("DART_API_KEY")


def get_financials(company_name: str) -> dict:
    # TODO: dart-fss 연동으로 실제 데이터 조회
    mock_data = {
        "LG 이노텍": {
            "company": "LG 이노텍",
            "financials": {
                2022: {"매출액": 19_630, "영업이익": 1_101, "순이익": 762},
                2023: {"매출액": 20_176, "영업이익": 1_023, "순이익": 704},
                2024: {"매출액": 21_540, "영업이익": 1_187, "순이익": 831},
            },
        }
    }
    return mock_data.get(company_name, {})


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
