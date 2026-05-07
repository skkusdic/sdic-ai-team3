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

    # 재무 데이터 섹션
    pdf.set_font(font_name, "B", 13)
    pdf.cell(0, 10, "주요 재무 데이터", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font(font_name, "", 11)
    field_map = {
        "매출액": financials.get("매출액", "N/A"),
        "영업이익": financials.get("영업이익", "N/A"),
        "순이익": financials.get("순이익", "N/A"),
    }
    for label, value in field_map.items():
        if isinstance(value, (int, float)):
            display = f"{value:,.0f} 원"
        else:
            display = str(value)
        pdf.cell(50, 8, f"{label}:", new_x="RIGHT", new_y="TOP")
        pdf.cell(0, 8, display, new_x="LMARGIN", new_y="NEXT")
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
    pdf.cell(0, 10, "SDIC AI Team3 — 자동 생성 보고서", align="C")

    # 저장
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{company}_report.pdf")
    pdf.output(pdf_path)

    return {**state, "pdf_path": pdf_path}


def embed_text(text: str) -> list:
    pass  # TODO: 4주차에 OpenAI embeddings로 구현


if __name__ == "__main__":
    mock_state = {
        "company": "삼성전자",
        "financials": {
            "매출액": 302_231_700_000_000,
            "영업이익": 6_566_900_000_000,
            "순이익": 15_373_200_000_000,
        },
        "analysis": (
            "이 기업의 영업이익률은 2.2%로 반도체 업황 부진의 영향을 받았습니다. "
            "매출액은 302조 원으로 글로벌 전자 기업 중 최상위권을 유지하고 있으며, "
            "순이익은 15조 원으로 비영업 수익이 양호한 것으로 나타납니다. "
            "전반적으로 수익성은 다소 낮으나 재무 건전성은 안정적인 수준입니다."
        ),
    }

    print("보고서 생성 시작...")
    result = run_report_agent(mock_state)
    print(f"PDF 생성 완료: {result['pdf_path']}")
