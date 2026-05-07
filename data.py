import os
import sqlite3
import requests
import dart_fss
from dotenv import load_dotenv

load_dotenv()
DART_API_KEY = os.getenv("DART_API_KEY")
DB_PATH = "financials.db"

_corp_list_cache = None


def _get_corp_list():
    global _corp_list_cache
    if _corp_list_cache is None:
        dart_fss.set_api_key(DART_API_KEY)
        _corp_list_cache = dart_fss.get_corp_list()
    return _corp_list_cache


def get_corp_code(company_name: str) -> str:
    results = _get_corp_list().find_by_corp_name(company_name, exactly=False)
    if not results:
        return ""
    return results[0].corp_code


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financials (
            company   TEXT,
            year      INTEGER,
            매출액    INTEGER,
            영업이익  INTEGER,
            순이익    INTEGER,
            PRIMARY KEY (company, year)
        )
    """)
    conn.commit()


def _save_to_db(company_name: str, financials: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        _init_db(conn)
        for year, d in financials.items():
            conn.execute(
                """
                INSERT OR REPLACE INTO financials (company, year, 매출액, 영업이익, 순이익)
                VALUES (?, ?, ?, ?, ?)
                """,
                (company_name, year, d.get("매출액", 0), d.get("영업이익", 0), d.get("순이익", 0)),
            )
        conn.commit()


def get_financials(company_name: str) -> dict:
    corp_code = get_corp_code(company_name)
    if not corp_code:
        return {}

    financials = {}
    for year in [2021, 2022, 2023, 2024, 2025]:
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

    _save_to_db(company_name, financials)
    return {"company": company_name, "financials": financials}


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
