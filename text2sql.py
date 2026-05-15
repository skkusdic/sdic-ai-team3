import os
import re
import sys
import sqlite3
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from claude_client import ask
from db import DB_PATH  # data_agent과 동일한 DB 사용

_SCHEMA = """
테이블명: financials
컬럼:
  - company  TEXT    (기업명)
  - year     INTEGER (연도, 예: 2021~2025)
  - 매출액   INTEGER (매출액, 단위: 억원)
  - 영업이익 INTEGER (영업이익, 단위: 억원)
  - 순이익   INTEGER (순이익, 단위: 억원)
"""

# DDL/DML 및 파일 접근 키워드 차단
_DANGEROUS = re.compile(
    r'\b(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|TRUNCATE|REPLACE'
    r'|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|LOAD_EXTENSION'
    r'|EXEC|EXECUTE)\b',
    re.IGNORECASE,
)

# AVG/SUM/COUNT/MAX/MIN 등 집계 함수만 있는 단순 집계 쿼리 패턴
_AGGREGATE_ONLY = re.compile(
    r'^\s*SELECT\s+(AVG|SUM|COUNT|MIN|MAX)\s*\(',
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> str | None:
    """검증 실패 시 오류 메시지, 통과 시 None 반환"""
    stripped = sql.strip()
    if not stripped.upper().startswith("SELECT"):
        return "생성된 SQL이 SELECT 구문으로 시작하지 않습니다."
    if _DANGEROUS.search(stripped):
        return "SQL에 허용되지 않는 키워드가 포함되어 있습니다."
    # 세미콜론 이후 추가 구문 차단 (쿼리 체이닝 방지)
    if stripped.rstrip(";").count(";") > 0:
        return "단일 SELECT 구문만 허용됩니다."
    return None


def _add_limit(sql: str, limit: int = 100) -> str:
    """LIMIT 절이 없으면 추가. 단순 집계 쿼리(GROUP BY 없는 AVG/SUM 등)엔 추가 안 함."""
    if re.search(r'\bLIMIT\b', sql, re.IGNORECASE):
        return sql
    # GROUP BY 없는 순수 집계 → 결과가 항상 1행이므로 LIMIT 불필요
    has_group_by = bool(re.search(r'\bGROUP\s+BY\b', sql, re.IGNORECASE))
    if _AGGREGATE_ONLY.match(sql) and not has_group_by:
        return sql
    return sql.rstrip(";").rstrip() + f" LIMIT {limit}"


def _generate_sql(query: str, company: str) -> str:
    """Claude로 자연어 질문 → SQLite SQL 변환"""
    prompt = (
        f"아래 SQLite 스키마를 보고 질문에 맞는 SELECT SQL을 작성해줘.\n\n"
        f"[스키마]\n{_SCHEMA}\n"
        f"[분석 기업] {company}\n"
        f"[질문] {query}\n\n"
        f"규칙:\n"
        f"- WHERE company='{company}' 조건 반드시 포함\n"
        f"- SELECT 문만 작성 (INSERT/UPDATE/DELETE/DROP 등 절대 금지)\n"
        f"- 컬럼명에 한글이 있으면 큰따옴표로 감싸기: \"매출액\"\n"
        f"- AVG, SUM 등 계산 컬럼은 반드시 한글 AS 별칭 사용 예: AVG(\"매출액\") AS 평균_매출액\n"
        f"- SQL 코드만 출력, 마크다운 코드블록 없이\n\n"
        f"SQL:"
    )
    sql = ask(prompt, max_tokens=300).strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def run(query: str, company: str) -> dict:
    """Text2SQL: SQL 생성 + 검증 + SQLite 실행 → {sql, dataframe, error}"""
    # DB 존재 여부 확인
    if not os.path.exists(DB_PATH):
        return {"sql": "", "dataframe": None, "error": "재무 DB가 없습니다. 먼저 기업 분석을 실행해주세요."}

    sql = _generate_sql(query, company)

    if not sql:
        return {"sql": sql, "dataframe": None, "error": "SQL 생성에 실패했습니다. 다시 시도해주세요."}

    err = _validate_sql(sql)
    if err:
        return {"sql": sql, "dataframe": None, "error": err}

    sql = _add_limit(sql)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(sql, conn)
        # AVG/SUM 등 집계 시 데이터 없으면 NULL 1행 반환 → 실질적으로 빈 결과
        if df.empty or df.dropna(how="all").empty:
            return {"sql": sql, "dataframe": None, "error": "조회 결과가 없습니다."}
        return {"sql": sql, "dataframe": df, "error": None}
    except Exception as e:
        return {"sql": sql, "dataframe": None, "error": str(e)}
