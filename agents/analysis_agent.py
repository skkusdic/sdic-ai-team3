import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_client import ask


def analyze(financials: dict) -> str:
    """5개년 재무 데이터를 받아 한국어 분석 문단을 생성한다.

    Args:
        financials: {연도: {"매출액": int, "영업이익": int, "순이익": int}, ...}

    Returns:
        Claude가 생성한 3-5문장 한국어 분석 문단.
    """
    if not financials:
        return "재무 데이터가 없어 분석을 진행할 수 없습니다."

    years = sorted(financials.keys())
    rows = []
    for year in years:
        d = financials[year]
        revenue = d.get("매출액", 0)
        operating = d.get("영업이익", 0)
        net = d.get("순이익", 0)
        op_margin = (operating / revenue * 100) if revenue else 0
        net_margin = (net / revenue * 100) if revenue else 0
        rows.append(
            f"- {year}: 매출 {revenue:,}억원, "
            f"영업이익 {operating:,}억원 (영업이익률 {op_margin:.1f}%), "
            f"순이익 {net:,}억원 (순이익률 {net_margin:.1f}%)"
        )

    latest_year = years[-1]
    latest = financials[latest_year]
    latest_revenue = latest.get("매출액", 0)
    latest_op = latest.get("영업이익", 0)
    latest_op_margin = (latest_op / latest_revenue * 100) if latest_revenue else 0

    rows_block = "\n".join(rows)

    prompt = (
        f"다음 5개년 재무 데이터를 바탕으로 기업 분석 문단을 작성해줘.\n\n"
        f"연도별 데이터 (단위: 억원):\n{rows_block}\n\n"
        f"조건:\n"
        f"- 반드시 \"이 기업의 영업이익률은 {latest_op_margin:.1f}%로\" 로 시작할 것\n"
        f"- 3~5문장으로 구성\n"
        f"- 매출 추세, 영업이익률 변화, 순이익률 변화를 종합한 분석\n"
        f"- 구체적인 수치를 활용한 전문적인 한국어 분석"
    )

    return ask(prompt, max_tokens=512)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 한글 깨짐 방지
    mock_financials = {
        2021: {"매출액": 149_883, "영업이익": 12_642, "순이익": 9_283},
        2022: {"매출액": 197_975, "영업이익": 12_718, "순이익": 8_625},
        2023: {"매출액": 207_096, "영업이익": 8_308,  "순이익": 5_525},
        2024: {"매출액": 215_500, "영업이익": 6_900,  "순이익": 4_800},
        2025: {"매출액": 220_000, "영업이익": 7_500,  "순이익": 5_200},
    }

    print("=== 5개년 재무 분석 (mock 데이터) ===")
    result = analyze(mock_financials)
    print(result)
