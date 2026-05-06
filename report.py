from fpdf import FPDF


def generate_report(company_name: str, financials: dict, analysis: str) -> str:
    """재무 분석 PDF 보고서를 생성한다.

    Args:
        company_name: 기업명
        financials:   연도별 재무 데이터 {"2022": {"매출액": ..., ...}, ...}
        analysis:     Claude가 생성한 재무 분석 텍스트

    Returns:
        저장된 PDF 파일 경로
    """
    pdf = FPDF()
    pdf.add_page()
    # TODO week4: 폰트, 제목, 재무 테이블, 분석 텍스트 추가

    output_path = f"{company_name}_report.pdf"
    pdf.output(output_path)
    return output_path


if __name__ == "__main__":
    path = generate_report("테스트기업", {}, "")
    print(f"PDF 생성 완료: {path}")
