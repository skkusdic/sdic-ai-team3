import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_client import ask


def analyze(financials: dict, news: list = None) -> str:
    revenue = financials.get("매출액", 0)
    operating_profit = financials.get("영업이익", 0)
    net_profit = financials.get("순이익", 0)

    operating_margin = (operating_profit / revenue * 100) if revenue else 0
    net_margin = (net_profit / revenue * 100) if revenue else 0

    news_section = ""
    if news:
        news_lines = "\n\n".join(
            f"[기사 {i+1}] ({a.get('published', '최근')}) {a['title']}\n{a.get('body') or a.get('summary', '')}"
            for i, a in enumerate(news)
        )
        news_section = f"\n\n최신 투자 관련 뉴스 (기사 본문 포함):\n{news_lines}"

    prompt = f"""다음 재무 데이터{'와 최신 뉴스' if news else ''}를 바탕으로 기업 분석 문단을 작성해줘.

매출액: {revenue:,}억원
영업이익: {operating_profit:,}억원
순이익: {net_profit:,}억원
영업이익률: {operating_margin:.1f}%
순이익률: {net_margin:.1f}%{news_section}

조건:
- 반드시 "이 기업의 영업이익률은 {operating_margin:.1f}%로" 로 시작할 것
- {'최신 뉴스 동향을 재무 분석에 자연스럽게 반영할 것' if news else '수익성과 재무 건전성을 분석할 것'}
- 3~5문장으로 구성
- 전문적인 한국어로 작성
- 구체적인 수치를 활용할 것"""

    return ask(prompt, max_tokens=600)


def analysis_agent(state: dict) -> dict:
    financials = state.get("financials", {})
    news = state.get("news", [])
    years_with_data = [y for y, v in financials.items() if v] if financials else []
    latest = financials[max(years_with_data)] if years_with_data else {}
    analysis_text = analyze(latest, news)
    return {**state, "analysis": analysis_text}


if __name__ == "__main__":
    mock_financials = {
        "매출액": 302_231,
        "영업이익": 6_566,
        "순이익": 15_373,
    }
    mock_news = [
        {
            "title": "삼성전자, HBM3E 공급 확대로 AI 반도체 수주 급증",
            "summary": "삼성전자가 엔비디아 등 주요 고객사에 HBM3E 메모리 공급을 확대하며 AI 반도체 시장에서 수주가 급증하고 있다.",
            "url": "",
            "published": "2026.05.19",
        }
    ]

    print("=== 삼성전자 재무+뉴스 분석 ===")
    result = analyze(mock_financials, mock_news)
    print(result)
