from typing import TypedDict
from langgraph.graph import StateGraph, END


class State(TypedDict):
    data: dict
    result: str


# node1
def load_data(state: State) -> State:
    samsung_financials = {
        "매출액": 300_000_000_000_000,
        "영업이익": 32_000_000_000_000,
        "순이익": 26_000_000_000_000,
    }
    return {"data": samsung_financials, "result": ""}

# node2
def process_data(state: State) -> State:
    data = state["data"]
    result = f"분석 준비 완료: 매출액 {data['매출액']}원, 영업이익 {data['영업이익']}원"
    print(result)
    return {"data": data, "result": result}


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
