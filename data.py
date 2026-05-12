import os
import sqlite3
import requests
import dart_fss
from dotenv import load_dotenv

load_dotenv()
DART_API_KEY = os.getenv("DART_API_KEY")
DB_PATH = "financials.db"

_corp_list_cache = None

# DART에 영문/약어로 등록된 회사 한글 별칭
_CORP_ALIASES = {
    "네이버": "NAVER",
    "케이티": "KT",
    "에스케이텔레콤": "SK텔레콤",
    "엘지전자": "LG전자",
    "엘지이노텍": "LG이노텍",
    "엘지화학": "LG화학",
    "엘지에너지솔루션": "LG에너지솔루션",
    "엘지생활건강": "LG생활건강",
    "엘지유플러스": "LG유플러스",
    "에스케이하이닉스": "SK하이닉스",
    "에스케이이노베이션": "SK이노베이션",
    "현대차": "현대자동차",
    "기아차": "기아",
    "포스코": "POSCO홀딩스",
    "비비큐": "BBQ",
}

# 계정명 alias: 회사별로 표기가 다름
_REVENUE_NAMES = {"매출액", "영업수익", "수익(매출액)", "영업수익(매출액)"}
_OP_INCOME_NAMES = {"영업이익", "영업이익(손실)"}
_NET_INCOME_NAMES = {"당기순이익", "당기순이익(손실)", "분기순이익", "분기순이익(손실)"}


def _get_corp_list():
    global _corp_list_cache
    if _corp_list_cache is None:
        dart_fss.set_api_key(DART_API_KEY)
        _corp_list_cache = dart_fss.get_corp_list()
    return _corp_list_cache


def _pick_listed(results: list) -> str:
    """결과 리스트에서 stock_code가 있는 (상장된) 회사를 우선 선택.

    DART corp 리스트에는 동명의 비상장·말소법인이 함께 있어
    results[0]가 우리가 원하는 상장사가 아닌 경우가 잦다.
    예: '카카오' → 00918444 (말소) vs 00258801 (코스피 035720).
    상장된 항목이 있으면 그것을 우선, 없으면 첫 결과.
    """
    if not results:
        return ""
    for r in results:
        stock_code = getattr(r, "stock_code", None)
        if stock_code:
            return r.corp_code
    return results[0].corp_code


def get_corp_code(company_name: str) -> str:
    """기업명을 받아 DART corp_code를 반환한다.

    안정성을 위해 다음 순서로 시도하며, 각 단계에서 상장된
    회사를 우선 선택한다:
      1) 입력 문자열 정확 매칭
      2) 공백 제거 후 정확 매칭
      3) 입력 문자열 substring 매칭
      4) 공백 제거 후 substring 매칭
    """
    corp_list = _get_corp_list()
    raw = company_name.strip()
    no_space = raw.replace(" ", "")
    candidates = [raw]
    if no_space and no_space != raw:
        candidates.append(no_space)
    # 한글 → DART 등록명 별칭 (네이버 → NAVER 등)
    if no_space in _CORP_ALIASES:
        candidates.append(_CORP_ALIASES[no_space])

    # Exact match preferred
    for candidate in candidates:
        results = corp_list.find_by_corp_name(candidate, exactly=True) or []
        code = _pick_listed(results)
        if code:
            return code

    # Substring fallback
    for candidate in candidates:
        results = corp_list.find_by_corp_name(candidate, exactly=False) or []
        code = _pick_listed(results)
        if code:
            return code

    return ""


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


def _load_from_db(company_name: str) -> dict:
    """SQLite에서 5개년 재무 데이터 조회. 없으면 빈 dict."""
    if not os.path.exists(DB_PATH):
        return {}
    with sqlite3.connect(DB_PATH) as conn:
        _init_db(conn)
        rows = conn.execute(
            "SELECT year, 매출액, 영업이익, 순이익 FROM financials WHERE company = ? ORDER BY year",
            (company_name,),
        ).fetchall()
    return {
        str(year): {"매출액": rev, "영업이익": op, "순이익": net}
        for year, rev, op, net in rows
        if rev is not None and op is not None and net is not None
    }


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


def _extract_year(corp_code: str, year: int, fs_div: str) -> dict:
    """단일 연도·재무제표 종류로 DART API 호출 후 파싱."""
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": "11011",
        "fs_div": fs_div,
    }
    try:
        items = requests.get(
            "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", params=params, timeout=10
        ).json().get("list", [])
    except Exception:
        return {}

    data = {}
    for item in items:
        nm = item.get("account_nm", "").strip()
        amt_str = item.get("thstrm_amount", "").replace(",", "").strip()
        if not amt_str:
            continue
        try:
            amt = int(amt_str)
        except ValueError:
            continue
        if amt == 0:
            continue
        if nm in _REVENUE_NAMES and "매출액" not in data:
            data["매출액"] = amt // 100_000_000
        if nm in _OP_INCOME_NAMES and "영업이익" not in data:
            data["영업이익"] = amt // 100_000_000
        if nm in _NET_INCOME_NAMES and "순이익" not in data:
            data["순이익"] = amt // 100_000_000
    return data


def get_financials(company_name: str) -> dict:
    """기업명을 받아 5개년 재무 데이터를 반환한다.

    반환 형식: {'2021': {"매출액": int, "영업이익": int, "순이익": int}, ...}
    데이터를 찾지 못하면 빈 dict {}.

    CFS(연결재무제표) 우선, 없으면 OFS(별도재무제표)로 폴백.
    """
    # SQLite 캐시 우선 조회 (DART 호출 회피)
    cached = _load_from_db(company_name)
    if cached:
        return cached

    corp_code = get_corp_code(company_name)
    if not corp_code:
        return {}

    financials = {}
    for year in [2021, 2022, 2023, 2024, 2025]:
        data = _extract_year(corp_code, year, "CFS")
        if not data:
            data = _extract_year(corp_code, year, "OFS")
        if data:
            financials[str(year)] = data

    if financials:
        _save_to_db(company_name, financials)
    return financials


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 한글 깨짐 방지
    for name in ["LG 이노텍", "삼성전자", "카카오", "네이버", "SK하이닉스"]:
        result = get_financials(name)
        if not result:
            print(f"[{name}] 데이터 없음")
        else:
            print(f"\n[{name}] 재무 데이터 (단위: 억원)")
            print(f"{'연도':<6} {'매출액':>10} {'영업이익':>10} {'순이익':>10}")
            print("-" * 40)
            for year, d in sorted(result.items()):
                print(f"{year:<6} {d.get('매출액',0):>10,} {d.get('영업이익',0):>10,} {d.get('순이익',0):>10,}")
