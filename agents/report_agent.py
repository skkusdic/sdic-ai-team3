import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpdf import FPDF
try:
    import rag as _rag
except Exception:
    _rag = None

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_PATH = os.path.join(_PROJECT_ROOT, "fonts", "NanumGothic.ttf")
_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "output")


class KoreanPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("NanumGothic", "", _FONT_PATH)
        self.set_font("NanumGothic", size=12)

    def header(self):
        self.set_font("NanumGothic", size=16)
        self.cell(0, 12, "SDIC AI 기업 재무 분석 리포트", align="C", new_x="LMARGIN", new_y="NEXT")

    def footer(self):
        self.set_y(-15)
        self.set_font("NanumGothic", size=9)
        self.cell(0, 10, f"페이지 {self.page_no()}", align="C")


def _fmt(v):
    if isinstance(v, float) and math.isnan(v):
        return "-"
    return f"{v:,}" if isinstance(v, (int, float)) else str(v)


def generate_pdf(company: str, financials: dict, analysis: str, news: list = None) -> str:
    pdf = KoreanPDF()
    pdf.add_page()

    # 기업명
    pdf.set_font("NanumGothic", size=14)
    pdf.cell(0, 10, f"기업명: {company}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 섹션 번호 카운터
    sec = 1

    # 1. 재무 데이터 섹션
    pdf.set_font("NanumGothic", size=12)
    pdf.cell(0, 10, f"{sec}. 재무 데이터 (단위: 억원)", new_x="LMARGIN", new_y="NEXT")
    sec += 1
    pdf.ln(2)

    col_w = [25, 55, 55, 55]
    headers = ["연도", "매출액", "영업이익", "순이익"]

    pdf.set_font("NanumGothic", size=10)
    for header, w in zip(headers, col_w):
        pdf.cell(w, 8, header, border=1, align="C")
    pdf.ln()

    for year in sorted(financials.keys()):
        row = financials[year]
        pdf.cell(col_w[0], 8, str(year), border=1, align="C")
        pdf.cell(col_w[1], 8, _fmt(row.get("매출액", "-")), border=1, align="R")
        pdf.cell(col_w[2], 8, _fmt(row.get("영업이익", "-")), border=1, align="R")
        pdf.cell(col_w[3], 8, _fmt(row.get("순이익", "-")), border=1, align="R")
        pdf.ln()

    pdf.ln(6)

    # 2. Claude AI 분석 섹션
    pdf.set_font("NanumGothic", size=12)
    pdf.cell(0, 10, f"{sec}. Claude AI 분석", new_x="LMARGIN", new_y="NEXT")
    sec += 1
    pdf.ln(2)

    pdf.set_font("NanumGothic", size=10)
    pdf.multi_cell(0, 7, analysis)

    # 3. 최근 주요 뉴스 섹션
    if news:
        pdf.ln(6)
        pdf.set_font("NanumGothic", size=12)
        pdf.cell(0, 10, f"{sec}. 최근 주요 뉴스", new_x="LMARGIN", new_y="NEXT")
        sec += 1
        pdf.ln(2)

        pdf.set_font("NanumGothic", size=10)
        for item in news:
            title = item.get("title", "")
            summary = item.get("summary", "")
            published = item.get("published", "")

            if title:
                pdf.set_font("NanumGothic", size=10)
                pdf.multi_cell(0, 7, f"■ {title}")
            if published:
                pdf.set_font("NanumGothic", size=9)
                pdf.cell(0, 6, f"   날짜: {published}", new_x="LMARGIN", new_y="NEXT")
            if summary:
                pdf.set_font("NanumGothic", size=9)
                display = summary[:150] + ("..." if len(summary) > 150 else "")
                pdf.multi_cell(0, 6, f"   {display}")
            pdf.ln(3)

    # 4. RAG 기반 연도별 재무 요약
    if _rag is not None:
        _rag_queries = ["매출 추이와 성장성", "영업이익 변동", "순이익 수익성"]
        _seen_years: set = set()
        _rag_lines: list = []
        for _q in _rag_queries:
            for _hit in _rag.search(_q, company, top_k=2):
                if _hit["year"] not in _seen_years:
                    _rag_lines.append(_hit["text"])
                    _seen_years.add(_hit["year"])
        if _rag_lines:
            pdf.ln(6)
            pdf.set_font("NanumGothic", size=12)
            pdf.cell(0, 10, f"{sec}. 연도별 재무 데이터 요약 (RAG)", new_x="LMARGIN", new_y="NEXT")
            sec += 1
            pdf.ln(2)
            pdf.set_font("NanumGothic", size=10)
            for _line in sorted(_rag_lines):
                pdf.multi_cell(0, 7, _line)
                pdf.ln(1)

    # output/ 폴더에 저장
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(_OUTPUT_DIR, f"report_{company}.pdf")
    pdf.output(pdf_path)
    return pdf_path


def run_report_agent(state: dict) -> dict:
    news = state.get("news", [])
    pdf_path = generate_pdf(state["company"], state["financials"], state["analysis"], news)
    return {**state, "pdf_path": pdf_path}


def embed_text(text: str) -> list:
    pass  # TODO: 4주차에 OpenAI embeddings로 구현


if __name__ == "__main__":
    mock_state = {
        "company": "삼성전자",
        "financials": {
            2020: {"매출액": 236_807, "영업이익": 35_994, "순이익": 26_407},
            2021: {"매출액": 279_604, "영업이익": 51_634, "순이익": 39_243},
            2022: {"매출액": 302_231, "영업이익": 43_377, "순이익": 55_654},
            2023: {"매출액": 258_935, "영업이익": 6_566, "순이익": 15_373},
            2024: {"매출액": 300_870, "영업이익": 32_726, "순이익": 34_469},
        },
        "analysis": (
            "삼성전자의 5개년 재무 데이터를 분석한 결과, 2022년 최대 매출(302,231억원)을 기록한 후 "
            "2023년 반도체 업황 부진으로 영업이익이 급감(6,566억원)하였습니다. "
            "2024년에는 메모리 반도체 회복세에 힘입어 영업이익이 32,726억원으로 반등하였습니다."
        ),
        "news": [
            {
                "title": "삼성전자, HBM3E 공급 확대로 AI 반도체 수주 급증",
                "summary": "삼성전자가 엔비디아 등 주요 고객사에 HBM3E 메모리 공급을 확대하며 AI 반도체 시장에서 수주가 급증하고 있다.",
                "url": "https://example.com",
                "published": "2026.05.19",
            },
            {
                "title": "삼성전자 2026년 1분기 영업이익 전망 상향",
                "summary": "증권가에서 삼성전자의 1분기 영업이익 전망치를 상향 조정하였다.",
                "url": "https://example.com",
                "published": "2026.05.15",
            },
        ],
    }

    print("보고서 생성 시작...")
    result = run_report_agent(mock_state)
    print(f"PDF 생성 완료: {result['pdf_path']}")
