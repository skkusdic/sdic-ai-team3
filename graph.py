import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import TypedDict
from langgraph.graph import StateGraph, END
from claude_client import ask
from agents.data_agent import run_data_agent
from agents.report_agent import run_report_agent
from agents.analysis_agent import analysis_agent


class State(TypedDict):
    request: str
    company: str
    next_agent: str
    financials: dict
    analysis: str
    result: str


def supervisor_node(state: State) -> State:
    request = state["request"]

    prompt = f"""다음 요청을 보고, 아래 세 에이전트 중 어디로 보내야 할지 판단해줘.

요청: {request}

에이전트 설명:
- data_agent: 기업 재무 데이터를 DART API로 수집·저장
- analysis_agent: 수집된 재무 데이터를 분석해 인사이트 도출
- report_agent: 분석 결과를 PDF 보고서로 작성

data_agent, analysis_agent, report_agent 중 하나만 출력해. 다른 말 없이 에이전트 이름만."""

    response = ask(prompt, max_tokens=50).strip()

    valid_agents = ["data_agent", "analysis_agent", "report_agent"]
    next_agent = "data_agent"
    for agent in valid_agents:
        if agent in response:
            next_agent = agent
            break

    print(f"[supervisor] 요청: '{request}'")
    print(f"[supervisor] Claude 응답: '{response}'")
    print(f"[supervisor] → {next_agent} 로 라우팅 결정")

    return {**state, "next_agent": next_agent}


def route(state: State) -> str:
    return state["next_agent"]


def route_after_data(state: State) -> str:
    financials = state.get("financials", {})
    if not financials or not any(v for v in financials.values()):
        return "no_data"
    return "analysis_agent"


def no_data_node(state: State) -> State:
    print("[data_agent] 재무 데이터 없음 → 파이프라인 종료")
    return {**state, "financials": {}, "result": "데이터를 찾을 수 없습니다"}


graph = StateGraph(State)
graph.add_node("supervisor", supervisor_node)
graph.add_node("data_agent", run_data_agent)
graph.add_node("no_data", no_data_node)
graph.add_node("analysis_agent", analysis_agent)
graph.add_node("report_agent", run_report_agent)

graph.set_entry_point("supervisor")
graph.add_conditional_edges(
    "supervisor",
    route,
    {
        "data_agent": "data_agent",
        "analysis_agent": "analysis_agent",
        "report_agent": "report_agent",
    },
)
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
    })
    print(f"\n[결과] next_agent = '{result['next_agent']}'")
    print(f"[결과] result    = '{result['result']}'")
