import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.supervisor_agent import supervisor_node
from agents.no_data_agent import no_data_node
from agents.data_agent import run_data_agent
from agents.analysis_agent import analysis_agent
from agents.report_agent import run_report_agent


class State(TypedDict):
    request: str
    company: str
    next_agent: str
    financials: dict
    analysis: str
    result: str
    pdf_path: str


def route_after_data(state: State) -> str:
    financials = state.get("financials", {})
    if not financials or not any(v for v in financials.values()):
        return "no_data"
    return "analysis_agent"


graph = StateGraph(State)
graph.add_node("supervisor", supervisor_node)
graph.add_node("data_agent", run_data_agent)
graph.add_node("no_data", no_data_node)
graph.add_node("analysis_agent", analysis_agent)
graph.add_node("report_agent", run_report_agent)

graph.set_entry_point("supervisor")
# supervisor는 항상 data_agent로만 연결 — 데이터 없이 분석/보고서로 건너뛰는 것을 방지
graph.add_edge("supervisor", "data_agent")
graph.add_conditional_edges(
    "data_agent",
    route_after_data,
    {
        "analysis_agent": "analysis_agent",
        "no_data": "no_data",
    },
)
graph.add_edge("no_data", END)
graph.add_edge("analysis_agent", "report_agent")
graph.add_edge("report_agent", END)

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({
        "request": "삼성전자 재무 데이터 수집하고 분석해서 보고서 만들어줘",
        "company": "삼성전자",
        "next_agent": "",
        "financials": {},
        "analysis": "",
        "result": "",
        "pdf_path": "",
    })
    print(f"\n[결과] next_agent = '{result['next_agent']}'")
    print(f"[결과] result    = '{result['result']}'")
