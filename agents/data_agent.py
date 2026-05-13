import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import get_financials
from db import load_financials, save_financials


def run_data_agent(state: dict) -> dict:
    company = state.get("company", "")

    cached = load_financials(company)
    if cached:
        print(f"[data_agent] 캐시 hit → DB에서 {company} 데이터 로드")
        return {
            **state,
            "financials": cached,
            "data_source": "cache",
            "next_agent": "analysis_agent",
        }

    print(f"[data_agent] 캐시 miss → DART API 호출: {company}")
    financials = get_financials(company)
    if financials:
        save_financials(company, financials)
    return {
        **state,
        "financials": financials,
        "data_source": "dart",
        "next_agent": "analysis_agent",
    }


if __name__ == "__main__":
    import json
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 한글 깨짐 방지
    mock_state = {"request": "LG이노텍 재무", "company": "LG이노텍"}
    result = run_data_agent(mock_state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
