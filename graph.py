from typing import TypedDict
from langgraph.graph import StateGraph, END
from claude_client import ask


class State(TypedDict):
    request: str
    next_agent: str
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

    # Claude 응답에서 유효한 에이전트 이름 추출
    valid_agents = ["data_agent", "analysis_agent", "report_agent"]
    next_agent = "data_agent"  # 기본값
    for agent in valid_agents:
        if agent in response:
            next_agent = agent
            break

    print(f"[supervisor] 요청: '{request}'")
    print(f"[supervisor] Claude 응답: '{response}'")
    print(f"[supervisor] → {next_agent} 로 라우팅 결정")

    return {**state, "next_agent": next_agent}


def data_agent_node(state: State) -> State:
    # TODO: 세션 당일 agents/data_agent.py 연결
    return state


def analysis_agent_node(state: State) -> State:
    # TODO: 세션 당일 agents/analysis_agent.py 연결
    return state


def report_agent_node(state: State) -> State:
    # TODO: 세션 당일 report.py 연결
    return state


def route(state: State) -> str:
    return state["next_agent"]


graph = StateGraph(State)
graph.add_node("supervisor", supervisor_node)
graph.add_node("data_agent", data_agent_node)
graph.add_node("analysis_agent", analysis_agent_node)
graph.add_node("report_agent", report_agent_node)

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
graph.add_edge("data_agent", END)
graph.add_edge("analysis_agent", END)
graph.add_edge("report_agent", END)

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({
        "request": "삼성전자 재무 분석해줘",
        "next_agent": "",
        "result": "",
    })
    print(f"\n[결과] next_agent = '{result['next_agent']}'")
