import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import TypedDict
from langgraph.graph import StateGraph, END
from claude_client import ask


class State(TypedDict):
    request: str        # 사용자 자연어 요청
    company: str        # 분석 대상 기업명 (data_agent가 사용)
    next_agent: str     # supervisor가 결정한 다음 에이전트 이름
    financials: dict    # data_agent가 채움. {연도: {매출액, 영업이익, 순이익}}
    analysis: str       # analysis_agent가 채움. Claude 분석 문단
    result: str         # 에러 메시지 등 사람이 읽을 출력 (성공 시 빈 문자열)
    pdf_path: str       # report_agent가 채움. 생성된 PDF의 절대 경로


def supervisor_node(state: State) -> State:
    request = state["request"]

    # 재무 데이터가 아직 없으면 무조건 data_agent부터 시작.
    # 그 다음 단계(analysis, report)는 그래프의 정적 edge가 처리한다.
    if not state.get("financials"):
        print(f"[supervisor] 요청: '{request}'")
        print(f"[supervisor] 재무 데이터 없음 → data_agent 로 라우팅")
        return {**state, "next_agent": "data_agent"}

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


def data_agent_node(state: State) -> State:
    from agents.data_agent import run_data_agent
    updated = run_data_agent(state)
    print(f"[data_agent] 재무 데이터 수집 완료: {list(updated.get('financials', {}).keys())}")
    return {**state, "financials": updated.get("financials", {})}


def analysis_agent_node(state: State) -> State:
    from agents.analysis_agent import analyze
    analysis_text = analyze(state.get("financials", {}))
    print(f"[analysis_agent] 분석 완료 ({len(analysis_text)}자)")
    return {**state, "analysis": analysis_text}


def report_agent_node(state: State) -> State:
    from agents.report_agent import run_report_agent
    updated = run_report_agent(state)
    pdf_path = updated.get("pdf_path", "")
    print(f"[report_agent] PDF 생성 완료: {pdf_path}")
    return {**state, "pdf_path": pdf_path}


def route(state: State) -> str:
    return state["next_agent"]


def route_after_data(state: State) -> str:
    if not state.get("financials"):
        return "no_data"
    return "analysis_agent"


def no_data_node(state: State) -> State:
    print("[data_agent] 재무 데이터 없음 → 파이프라인 종료")
    return {**state, "result": "데이터를 찾을 수 없습니다"}


graph = StateGraph(State)
graph.add_node("supervisor", supervisor_node)
graph.add_node("data_agent", data_agent_node)
graph.add_node("no_data", no_data_node)
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
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 한글 깨짐 방지
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
