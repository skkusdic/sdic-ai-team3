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
    # 네이버/카카오 계열
    "네이버": "NAVER",
    "카카오뱅크": "카카오뱅크",
    "카카오페이": "카카오페이",
    # KT/SK/LG 계열 한글 전음 → 영문 표기
    "케이티": "KT",
    "케이티앤지": "KT&G",
    "에스케이텔레콤": "SK텔레콤",
    "에스케이하이닉스": "SK하이닉스",
    "에스케이이노베이션": "SK이노베이션",
    "에스케이": "SK",
    "에스케이네트웍스": "SK네트웍스",
    "에스케이바이오사이언스": "SK바이오사이언스",
    "엘지전자": "LG전자",
    "엘지이노텍": "LG이노텍",
    "엘지화학": "LG화학",
    "엘지에너지솔루션": "LG에너지솔루션",
    "엘지생활건강": "LG생활건강",
    "엘지유플러스": "LG유플러스",
    "엘지디스플레이": "LG디스플레이",
    # 현대/기아
    "현대차": "현대자동차",
    "기아차": "기아",
    "현대모비스": "현대모비스",
    "현대위아": "현대위아",
    "현대글로비스": "현대글로비스",
    "현대건설": "현대건설",
    # 포스코/롯데/한화
    "포스코": "POSCO홀딩스",
    "포스코홀딩스": "POSCO홀딩스",
    "롯데케미칼": "롯데케미칼",
    "롯데쇼핑": "롯데쇼핑",
    "한화솔루션": "한화솔루션",
    "한화에어로스페이스": "한화에어로스페이스",
    # 삼성 계열
    "삼성sdI": "삼성SDI",
    "삼성sdi": "삼성SDI",
    "삼성바이오로직스": "삼성바이오로직스",
    "삼성물산": "삼성물산",
    "삼성생명": "삼성생명보험",
    "삼성화재": "삼성화재해상보험",
    "삼성전기": "삼성전기",
    "삼성에스디에스": "삼성SDS",
    "삼성sds": "삼성SDS",
    # 기타
    "비비큐": "BBQ",
    "대한항공": "대한항공",
    "아시아나": "아시아나항공",
    "셀트리온": "셀트리온",
    "에이치엠엠": "HMM",
    "hmm": "HMM",
    "아모레퍼시픽": "아모레퍼시픽",
    "에스원": "S-1",
    "크래프톤": "크래프톤",
    "엔씨소프트": "엔씨소프트",
    "넥슨": "넥슨코리아",
    "카카오게임즈": "카카오게임즈",
    "두산에너빌리티": "두산에너빌리티",
    "두산밥캣": "두산밥캣",
    "고려아연": "고려아연",
    "기업은행": "IBK기업은행",
    "신한은행": "신한은행",
    "하나은행": "하나은행",
    "우리은행": "우리은행",
    "국민은행": "KB국민은행",
}

# 계정명 alias: 회사별·업종별로 표기가 다름
_REVENUE_NAMES = {
    "매출액", "영업수익", "수익(매출액)", "영업수익(매출액)",
    "매출", "총매출액", "순매출액",
    # 금융/보험/지주사
    "이자수익", "보험료수익", "수수료수익",
    "영업수익합계", "총영업수익",
}
_OP_INCOME_NAMES = {
    "영업이익", "영업이익(손실)",
    "영업손익", "영업이익(영업손실)",
}
_NET_INCOME_NAMES = {
    "당기순이익", "당기순이익(손실)",
    "분기순이익", "분기순이익(손실)",
    "당기순손익", "연결당기순이익",
    "당기순이익(당기순손실)",
}


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
      1) 입력 문자열 정확 매칭 (및 소문자 정규화 변형)
      2) 공백 제거 후 정확 매칭
      3) 별칭 변환 후 정확 매칭
      4) Substring 폴백 (원문 → 공백제거 → 별칭)
    """
    corp_list = _get_corp_list()
    raw = company_name.strip()
    no_space = raw.replace(" ", "")
    no_space_lower = no_space.lower()

    # 별칭 후보 수집 (소문자 키도 매칭)
    alias_candidates = []
    for key in (no_space, no_space_lower):
        if key in _CORP_ALIASES:
            alias_candidates.append(_CORP_ALIASES[key])

    # 전체 후보: 원문 → 공백제거 → 별칭
    exact_candidates = [raw]
    if no_space and no_space != raw:
        exact_candidates.append(no_space)
    exact_candidates.extend(alias_candidates)

    # Exact match preferred
    for candidate in exact_candidates:
        results = corp_list.find_by_corp_name(candidate, exactly=True) or []
        code = _pick_listed(results)
        if code:
            return code

    # Substring fallback (원문·공백제거·별칭 순)
    for candidate in exact_candidates:
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
        print(f"[DART] '{company_name}' - DART 기업 목록에서 corp_code를 찾지 못했습니다.")
        return {}

    print(f"[DART] '{company_name}' → corp_code={corp_code}")
    financials = {}
    for year in [2021, 2022, 2023, 2024, 2025]:
        data = _extract_year(corp_code, year, "CFS")
        if not data:
            data = _extract_year(corp_code, year, "OFS")
        if data:
            financials[str(year)] = data
        else:
            print(f"[DART] {year}년 데이터 없음 (corp_code={corp_code})")

    if financials:
        _save_to_db(company_name, financials)
    else:
        print(f"[DART] '{company_name}' - 재무 데이터를 가져오지 못했습니다. (계정명 불일치 또는 미공시)")
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
