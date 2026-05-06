from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from data import get_financials
from claude_client import ask


class State(TypedDict):
    company_name: str
    data: dict
    result: str
    next: str


# supervisor
def supervisor_node(state: State) -> State:
    if not state.get("data"):
        print("[supervisor] → data_agent 호출")
        return {"next": "data_agent"}
    if not state.get("result"):
        print("[supervisor] → analysis_agent 호출")
        return {"next": "analysis_agent"}
    print("[supervisor] → 완료")
    return {"next": END}


def route(state: State) -> Literal["data_agent", "analysis_agent", "__end__"]:
    return state["next"]


# data_agent
def data_agent(state: State) -> State:
    company = state.get("company_name") or "LG 이노텍"
    raw = get_financials(company)
    print(f"[data_agent] {raw['company']} 재무 데이터 로드 완료 (단위: 억원)")
    for year, d in sorted(raw["financials"].items()):
        print(f"  {year}년  매출액 {d.get('매출액', 0):>10,}  영업이익 {d.get('영업이익', 0):>10,}  순이익 {d.get('순이익', 0):>10,}")
    return {"company_name": company, "data": raw, "next": ""}


# analysis_agent
def analysis_agent(state: State) -> State:
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
    return {"result": analysis, "next": ""}


# pipeline
graph = StateGraph(State)
graph.add_node("supervisor", supervisor_node)
graph.add_node("data_agent", data_agent)
graph.add_node("analysis_agent", analysis_agent)

graph.set_entry_point("supervisor")
graph.add_conditional_edges("supervisor", route, {
    "data_agent": "data_agent",
    "analysis_agent": "analysis_agent",
    END: END,
})
graph.add_edge("data_agent", "supervisor")
graph.add_edge("analysis_agent", "supervisor")

app = graph.compile()

if __name__ == "__main__":
    final_state = app.invoke({"company_name": "LG 이노텍", "data": {}, "result": "", "next": ""})
