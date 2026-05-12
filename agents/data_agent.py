import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import get_financials

_cache: dict = {}


def run_data_agent(state: dict) -> dict:
    company = state.get("company", "")
    if company not in _cache:
        _cache[company] = get_financials(company)
    financials = _cache[company]
    return {
        **state,
        "financials": financials,
        "next_agent": "analysis_agent",
    }


if __name__ == "__main__":
    import json
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 한글 깨짐 방지
    mock_state = {"request": "LG이노텍 재무", "company": "LG이노텍"}
    result = run_data_agent(mock_state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
