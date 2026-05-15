import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def supervisor_node(state: dict) -> dict:
    company = state.get("company", "")
    print(f"[supervisor] 요청 접수: '{company}' 분석 시작 → data_agent 로 전달")
    return state
