import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sdic.db")

_FORBIDDEN = ["DROP", "INSERT", "UPDATE", "DELETE"]


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                corp_code TEXT PRIMARY KEY,
                company   TEXT NOT NULL
            )
        """)
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS news_chunks (
                company    TEXT,
                title      TEXT,
                body       TEXT,
                published  TEXT,
                url        TEXT,
                created_at TEXT,
                PRIMARY KEY (company, title)
            )
        """)
        conn.commit()


def save_financials(company_name: str, financials: dict) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        for year, d in financials.items():
            conn.execute(
                """
                INSERT OR REPLACE INTO financials (company, year, 매출액, 영업이익, 순이익)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    company_name,
                    int(year),
                    d.get("매출액", 0),
                    d.get("영업이익", 0),
                    d.get("순이익", 0),
                ),
            )
        conn.commit()


def load_financials(company_name: str) -> dict:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT year, 매출액, 영업이익, 순이익 FROM financials WHERE company = ?",
            (company_name,),
        ).fetchall()
    if not rows:
        return {}
    return {
        row["year"]: {
            "매출액": row["매출액"],
            "영업이익": row["영업이익"],
            "순이익": row["순이익"],
        }
        for row in rows
    }


def save_news_chunks(company: str, news_list: list) -> None:
    if not news_list:
        return
    init_db()
    from datetime import datetime
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        for item in news_list:
            conn.execute(
                """
                INSERT OR REPLACE INTO news_chunks
                    (company, title, body, published, url, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    company,
                    item.get("title", ""),
                    item.get("body", "") or item.get("summary", ""),
                    item.get("published", ""),
                    item.get("url", ""),
                    created_at,
                ),
            )
        conn.commit()


def load_news_chunks(company: str) -> list:
    init_db()
    if not os.path.exists(DB_PATH):
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT title, body, published, url FROM news_chunks WHERE company=? ORDER BY published DESC",
            (company,),
        ).fetchall()
    return [dict(row) for row in rows]


def execute_sql(query: str) -> list:
    stripped = query.strip()
    if not stripped.upper().startswith("SELECT"):
        raise ValueError("SELECT 문만 허용됩니다.")
    if stripped.count(";") >= 2:
        raise ValueError("다중 statement 금지")
    for kw in _FORBIDDEN:
        if kw in stripped.upper():
            raise ValueError(f"금지된 키워드 포함: {kw}")
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(stripped).fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    init_db()
    print("✅ init_db() 완료")

    save_financials("삼성전자", {2023: {"매출액": 2589000, "영업이익": 65000, "순이익": 55000}})
    print("✅ save_financials() 완료")

    data = load_financials("삼성전자")
    print(f"✅ load_financials(): {data}")

    rows = execute_sql("SELECT * FROM financials")
    print(f"✅ execute_sql(): {rows}")

    try:
        execute_sql("DROP TABLE financials")
    except ValueError as e:
        print(f"✅ DROP 차단 확인: {e}")

    try:
        execute_sql("INSERT INTO financials VALUES ('test', 2023, 0, 0, 0)")
    except ValueError as e:
        print(f"✅ INSERT 차단 확인: {e}")
