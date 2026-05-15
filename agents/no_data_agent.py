import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def no_data_node(state: dict) -> dict:
    company = state.get("company", "")
    print(f"[no_data] '{company}' 재무 데이터 없음 → 파이프라인 종료")
    return {
        **state,
        "financials": {},
        "result": f"'{company}' 재무 데이터를 찾을 수 없습니다. DART에 등록된 정확한 기업명을 입력해주세요.",
    }
