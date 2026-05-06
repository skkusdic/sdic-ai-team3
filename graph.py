from typing import TypedDict
from langgraph.graph import StateGraph, END
from data import get_financials
from claude_client import ask


class State(TypedDict):
    company_name: str
    data: dict
    result: str


# node1
def load_data(state: State) -> State:
    company = state.get("company_name") or "LG 이노텍"
    raw = get_financials(company)
    print(f"[load_data] {raw['company']} 재무 데이터 로드 완료 (단위: 억원)")
    for year, d in sorted(raw["financials"].items()):
        print(f"  {year}년  매출액 {d.get('매출액', 0):>10,}  영업이익 {d.get('영업이익', 0):>10,}  순이익 {d.get('순이익', 0):>10,}")
    return {"company_name": company, "data": raw, "result": ""}


# node2
def analyze(state: State) -> State:
    company = state["data"].get("company", "")
    financials = state["data"].get("financials", {})

    rows = "\n".join(
        f"  {year}년: 매출액 {d.get('매출액', 0):,}억원, "
        f"영업이익 {d.get('영업이익', 0):,}억원, "
        f"순이익 {d.get('순이익', 0):,}억원"
        for year, d in sorted(financials.items())
    )
    prompt = (
        f"다음은 {company}의 최근 3개년 연결재무제표 요약입니다 (단위: 억원).\n"
        f"{rows}\n\n"
        "위 데이터를 바탕으로 매출 성장성, 수익성(영업이익률·순이익률), "
        "전년 대비 주요 변화를 한국어로 3~5문장으로 분석해줘."
    )

    analysis = ask(prompt, max_tokens=600)
    print(f"\n=== Claude 재무 분석: {company} ===")
    print(analysis)
    return {"data": state["data"], "result": analysis}


# pipeline
graph = StateGraph(State)
graph.add_node("load_data", load_data)
graph.add_node("analyze", analyze)

graph.set_entry_point("load_data")
graph.add_edge("load_data", "analyze")
graph.add_edge("analyze", END)

app = graph.compile()

# 실행
if __name__ == "__main__":
    final_state = app.invoke({"company_name": "LG 이노텍", "data": {}, "result": ""})
