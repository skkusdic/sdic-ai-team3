import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpdf import FPDF


def run_report_agent(state: dict) -> dict:
    company = state.get("company", "Unknown")
    financials = state.get("financials", {})
    analysis = state.get("analysis", "")

    pdf = FPDF()
    pdf.add_page()

    # 한글 폰트 등록 (Windows 맑은 고딕)
    font_path = r"C:\Windows\Fonts\malgun.ttf"
    if os.path.exists(font_path):
        pdf.add_font("Malgun", "", font_path)
        pdf.add_font("Malgun", "B", font_path)
        font_name = "Malgun"
    else:
        font_name = "Helvetica"

    # 제목
    pdf.set_font(font_name, "B", 20)
    pdf.cell(0, 15, f"{company} 기업 분석 보고서", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # 구분선
    pdf.set_draw_color(100, 100, 100)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # 재무 데이터 섹션: 5개년 표
    # 표준 인터페이스 #2: state["financials"]는 {연도: {매출액, 영업이익, 순이익}} 형태
    pdf.set_font(font_name, "B", 13)
    pdf.cell(0, 10, "5개년 재무 데이터 (단위: 억원)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    if financials:
        # 표 헤더
        pdf.set_font(font_name, "B", 11)
        pdf.cell(30, 8, "연도", border=1, align="C")
        pdf.cell(50, 8, "매출액", border=1, align="C")
        pdf.cell(50, 8, "영업이익", border=1, align="C")
        pdf.cell(50, 8, "순이익", border=1, new_x="LMARGIN", new_y="NEXT", align="C")

        # 표 데이터 (연도순 정렬)
        pdf.set_font(font_name, "", 11)
        for year in sorted(financials.keys()):
            metrics = financials[year] if isinstance(financials[year], dict) else {}
            매출액 = metrics.get("매출액", 0)
            영업이익 = metrics.get("영업이익", 0)
            순이익 = metrics.get("순이익", 0)
            pdf.cell(30, 8, str(year), border=1, align="C")
            pdf.cell(50, 8, f"{매출액:,}" if isinstance(매출액, (int, float)) else str(매출액), border=1, align="R")
            pdf.cell(50, 8, f"{영업이익:,}" if isinstance(영업이익, (int, float)) else str(영업이익), border=1, align="R")
            pdf.cell(50, 8, f"{순이익:,}" if isinstance(순이익, (int, float)) else str(순이익), border=1, new_x="LMARGIN", new_y="NEXT", align="R")
    else:
        pdf.set_font(font_name, "", 11)
        pdf.cell(0, 8, "재무 데이터 없음", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # 분석 섹션
    pdf.set_font(font_name, "B", 13)
    pdf.cell(0, 10, "AI 분석 요약", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font(font_name, "", 11)
    analysis_text = analysis if analysis else "분석 데이터가 없습니다."
    pdf.multi_cell(0, 7, analysis_text)
    pdf.ln(6)

    # 푸터
    pdf.set_y(-20)
    pdf.set_font(font_name, "", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "SDIC AI Team3 자동 생성 보고서", align="C")

    # 저장
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{company}_report.pdf")
    pdf.output(pdf_path)

    return {**state, "pdf_path": pdf_path}


def embed_text(text: str) -> list:
    pass  # TODO: 4주차에 OpenAI embeddings로 구현


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 한글 깨짐 방지
    mock_state = {
        "company": "삼성전자",
        "financials": {
            2021: {"매출액": 2796000, "영업이익": 516000, "순이익": 392000},
            2022: {"매출액": 3022000, "영업이익": 431000, "순이익": 553000},
            2023: {"매출액": 2589000, "영업이익": 64000,  "순이익": 151000},
            2024: {"매출액": 3009000, "영업이익": 322000, "순이익": 341000},
            2025: {"매출액": 3204000, "영업이익": 389000, "순이익": 408000},
        },
        "analysis": (
            "이 기업의 영업이익률은 12.1%로 반도체 사이클 회복에 힘입어 전년 대비 크게 개선되었습니다. "
            "매출액은 320조 원으로 5개년 최고치를 기록했으며, 순이익률도 12.7%로 안정적인 수준을 유지하고 있습니다."
        ),
    }

    print("보고서 생성 시작...")
    result = run_report_agent(mock_state)
    print(f"PDF 생성 완료: {result['pdf_path']}")
