import os
import sys
import sqlite3
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from claude_client import ask

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financials.db")

_SCHEMA = """
테이블명: financials
컬럼:
  - company  TEXT    (기업명)
  - year     INTEGER (연도, 예: 2021~2025)
  - 매출액   INTEGER (매출액, 단위: 억원)
  - 영업이익 INTEGER (영업이익, 단위: 억원)
  - 순이익   INTEGER (순이익, 단위: 억원)
"""


def _generate_sql(query: str, company: str) -> str:
    """Claude로 자연어 질문 → SQLite SQL 변환"""
    prompt = (
        f"아래 SQLite 스키마를 보고 질문에 맞는 SELECT SQL을 작성해줘.\n\n"
        f"[스키마]\n{_SCHEMA}\n"
        f"[분석 기업] {company}\n"
        f"[질문] {query}\n\n"
        f"규칙:\n"
        f"- WHERE company='{company}' 조건 반드시 포함\n"
        f"- SELECT 문만 작성 (INSERT/UPDATE/DELETE 금지)\n"
        f"- 컬럼명에 한글이 있으면 큰따옴표로 감싸기: \"매출액\"\n"
        f"- SQL 코드만 출력, 마크다운 코드블록 없이\n\n"
        f"SQL:"
    )
    sql = ask(prompt, max_tokens=300).strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def run(query: str, company: str) -> dict:
    """Text2SQL: SQL 생성 + SQLite 실행 → {sql, dataframe, error}"""
    sql = _generate_sql(query, company)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(sql, conn)
        return {"sql": sql, "dataframe": df, "error": None}
    except Exception as e:
        return {"sql": sql, "dataframe": None, "error": str(e)}
