from typing import TypedDict
from langgraph.graph import StateGraph, END
from data import get_financials


class State(TypedDict):
    data: dict
    result: str


# node1
def load_data(state: State) -> State:
    raw = get_financials("LG 이노텍")
    return {"data": raw, "result": ""}


# node2
def process_data(state: State) -> State:
    company = state["data"].get("company", "")
    financials = state["data"].get("financials", {})
    latest_year = max(financials.keys())
    d = financials[latest_year]
    result = (
        f"[{company}] {latest_year}년 분석 준비 완료 - "
        f"매출액 {d.get('매출액', 0):,}억원, "
        f"영업이익 {d.get('영업이익', 0):,}억원, "
        f"순이익 {d.get('순이익', 0):,}억원"
    )
    print(result)
    return {"data": state["data"], "result": result}


# pipeline
graph = StateGraph(State)
graph.add_node("load_data", load_data)
graph.add_node("process_data", process_data)

graph.set_entry_point("load_data")
graph.add_edge("load_data", "process_data")
graph.add_edge("process_data", END)

app = graph.compile()

# 실행
if __name__ == "__main__":
    final_state = app.invoke({"data": {}, "result": ""})
