import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def analyze(financials: dict) -> str:
    revenue = financials.get("매출액", 0)
    operating_profit = financials.get("영업이익", 0)
    net_profit = financials.get("순이익", 0)

    operating_margin = (operating_profit / revenue * 100) if revenue else 0
    net_margin = (net_profit / revenue * 100) if revenue else 0

    prompt = f"""다음 재무 데이터를 바탕으로 기업 분석 문단을 작성해줘.

매출액: {revenue:,}원
영업이익: {operating_profit:,}원
순이익: {net_profit:,}원
영업이익률: {operating_margin:.1f}%
순이익률: {net_margin:.1f}%

조건:
- 반드시 "이 기업의 영업이익률은 {operating_margin:.1f}%로" 로 시작할 것
- 3~5문장으로 구성
- 수익성과 재무 건전성에 대한 전문적인 한국어 분석
- 구체적인 수치를 활용할 것"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


if __name__ == "__main__":
    mock_financials = {
        "매출액": 302_231_700_000_000,
        "영업이익": 6_566_900_000_000,
        "순이익": 15_373_200_000_000,
    }

    print("=== 삼성전자 재무 분석 ===")
    result = analyze(mock_financials)
    print(result)
