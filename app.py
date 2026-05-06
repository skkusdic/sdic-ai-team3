import streamlit as st
import pandas as pd
import time
from data import get_financials
from graph import app as graph_app
from report import generate_report

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", layout="wide")

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stButton,
.stDataFrame, .stSidebar, h1, h2, h3, p, span, div {
    font-family: 'Pretendard', sans-serif !important;
}

/* 배경 */
.stApp { background-color: #fafafa; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #efefef;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #333333;
    font-size: 0.9rem;
    line-height: 1.8;
}

/* 메인 타이틀 */
h1 {
    color: #111111;
    font-weight: 700;
    font-size: 2rem !important;
    letter-spacing: -0.5px;
    padding-bottom: 0.2rem;
}
h1 span.accent { color: #E8001C; }

/* 구분선 */
.divider {
    height: 2px;
    background: #E8001C;
    width: 48px;
    margin: 0.3rem 0 2rem 0;
    border-radius: 2px;
}

/* 라벨 */
[data-testid="stTextInput"] label {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #888888 !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* 입력창 */
[data-testid="stTextInput"] input {
    border: 1px solid #E8001C !important;
    border-radius: 4px !important;
    padding: 0.55rem 0.8rem !important;
    font-size: 0.95rem !important;
    background: #ffffff !important;
    color: #111111 !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stTextInput"] input:focus {
    border: 1.5px solid #E8001C !important;
    box-shadow: 0 0 0 3px rgba(232,0,28,0.08) !important;
}

/* 버튼 래퍼 — 가운데 정렬 */
.btn-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 1.6rem;
}

/* 버튼 */
.stButton > button {
    background-color: #E8001C !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em;
    padding: 0.75rem 3.5rem !important;
    transition: background 0.2s, transform 0.1s;
    box-shadow: 0 2px 10px rgba(232,0,28,0.18) !important;
}
.stButton > button:hover {
    background-color: #c0001a !important;
    transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

/* 버튼 컬럼 가운데 정렬 */
[data-testid="column"] { display: flex; justify-content: center; }

/* 서브헤더 */
h2 {
    color: #111111 !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    margin-top: 2rem !important;
}

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border: 1px solid #efefef !important;
    border-radius: 6px !important;
    overflow: hidden;
}

/* 경고 / 성공 메시지 */
[data-testid="stAlert"] {
    border-radius: 4px !important;
    font-size: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### 팀 정보")
    st.markdown("""
**팀 이름**
sdic-ai-team3

**분석 기업명**
삼성전자

**현재 주차**
2주차
""")

# 타이틀
st.markdown('<h1>AI 재무 컨설팅 <span class="accent">어시스턴트</span></h1>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# 입력창
company = st.text_input("기업명을 입력하세요", placeholder="예: 삼성전자")

# 버튼 가운데 정렬
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    clicked = st.button("분석 시작")

if clicked:
    if not company.strip():
        st.warning("기업명을 입력해주세요")
    else:
        with st.spinner("데이터 불러오는 중..."):
            time.sleep(1.5)

        # data.py에서 재무 데이터 조회
        result = get_financials(company)

        if not result:
            st.error(f"'{company}'에 대한 데이터를 찾을 수 없습니다.")
        else:
            financials = result["financials"]
            rows = [
                {
                    "연도": year,
                    "매출액 (억원)": v["매출액"],
                    "영업이익 (억원)": v["영업이익"],
                    "순이익 (억원)": v["순이익"],
                }
                for year, v in financials.items()
            ]
            df = pd.DataFrame(rows).set_index("연도")

            st.subheader(f"{company} 재무 현황 (2022~2024)")
            st.dataframe(df, use_container_width=True)

            # graph.py LangGraph 파이프라인 실행
            with st.spinner("LangGraph 파이프라인 실행 중..."):
                graph_state = graph_app.invoke({"data": {}, "result": ""})
            st.info(f"파이프라인 결과: {graph_state['result']}")

            # report.py Claude 리포트 생성
            report = generate_report(company, rows)
            if report:
                st.subheader("AI 분석 리포트")
                st.markdown(report)

            st.success("분석 완료!")
