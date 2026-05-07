import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import get_financials


def run_data_agent(state: dict) -> dict:
    company = state.get("company", "")
    financials_result = get_financials(company)
    return {
        **state,
        "financials": financials_result.get("financials", {}),
        "next_agent": "analysis_agent",
    }


if __name__ == "__main__":
    import json
    mock_state = {"request": "LG이노텍 재무", "company": "LG이노텍"}
    result = run_data_agent(mock_state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
