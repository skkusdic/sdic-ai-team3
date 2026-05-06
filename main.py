import os
import requests
import streamlit as st
import pandas as pd
import time
import anthropic
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, END

load_dotenv()
DART_API_KEY = os.getenv("DART_API_KEY")
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── data.py ──────────────────────────────────────────────────────────────────

CORP_CODES = {
    "LG 이노텍": "00105961",
}


def get_financials(company_name: str) -> dict:
    corp_code = CORP_CODES.get(company_name)
    if not corp_code:
        return {}

    financials = {}
    for year in [2022, 2023, 2024]:
        params = {
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": "11011",
            "fs_div": "CFS",
        }
        items = requests.get(
            "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", params=params
        ).json().get("list", [])

        data = {}
        for item in items:
            nm = item.get("account_nm", "").strip()
            amt = item.get("thstrm_amount", "").replace(",", "")
            if not amt or int(amt) == 0:
                continue
            if nm == "매출액" and "매출액" not in data:
                data["매출액"] = int(amt) // 100_000_000
            if nm in ("영업이익", "영업이익(손실)") and "영업이익" not in data:
                data["영업이익"] = int(amt) // 100_000_000
            if nm == "당기순이익" and "순이익" not in data:
                data["순이익"] = int(amt) // 100_000_000
        financials[year] = data

    return {"company": company_name, "financials": financials}


def get_corp_code(company_name: str) -> str:
    return CORP_CODES.get(company_name, "")


def get_financial_statements(corp_code: str) -> list:
    # TODO: dart-fss로 재무제표 조회
    pass


# ── graph.py ─────────────────────────────────────────────────────────────────

class State(TypedDict):
    data: dict
    result: str


def load_data(state: State) -> State:
    raw = get_financials("LG 이노텍")
    return {"data": raw, "result": ""}


def process_data(state: State) -> State:
    company = state["data"].get("company", "")
    financials = state["data"].get("financials", {})
    latest_year = max(financials.keys())
    d = financials[latest_year]
    result = (
        f"[{company}] {latest_year}년 분석 준비 완료 - "
        f"매출액 {d.get('매출액', 0):,}억원, "
        f"영업이익 {d.get('영업이익', 0):,}억원, "
        f"순이익 {d.get('순이익', 0):,}억원"
    )
    return {"data": state["data"], "result": result}


graph = StateGraph(State)
graph.add_node("load_data", load_data)
graph.add_node("process_data", process_data)
graph.set_entry_point("load_data")
graph.add_edge("load_data", "process_data")
graph.add_edge("process_data", END)
pipeline = graph.compile()


# ── report.py ────────────────────────────────────────────────────────────────

def generate_report(company: str, financials: list) -> str:
    # TODO Week 3-4: Claude로 분석 리포트 생성
    pass


# ── app.py (Streamlit UI) ─────────────────────────────────────────────────────

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", layout="wide")

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stButton,
.stDataFrame, .stSidebar, h1, h2, h3, p, span, div {
    font-family: 'Pretendard', sans-serif !important;
}

.stApp { background-color: #fafafa; }

[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #efefef;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #333333;
    font-size: 0.9rem;
    line-height: 1.8;
}

h1 {
    color: #111111;
    font-weight: 700;
    font-size: 2rem !important;
    letter-spacing: -0.5px;
    padding-bottom: 0.2rem;
}
h1 span.accent { color: #E8001C; }

.divider {
    height: 2px;
    background: #E8001C;
    width: 48px;
    margin: 0.3rem 0 2rem 0;
    border-radius: 2px;
}

[data-testid="stTextInput"] label {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #888888 !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

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

[data-testid="column"] { display: flex; justify-content: center; }

h2 {
    color: #111111 !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    margin-top: 2rem !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #efefef !important;
    border-radius: 6px !important;
    overflow: hidden;
}

[data-testid="stAlert"] {
    border-radius: 4px !important;
    font-size: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)

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

st.markdown('<h1>AI 재무 컨설팅 <span class="accent">어시스턴트</span></h1>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

company = st.text_input("기업명을 입력하세요", placeholder="예: 삼성전자")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    clicked = st.button("분석 시작")

if clicked:
    if not company.strip():
        st.warning("기업명을 입력해주세요")
    else:
        with st.spinner("데이터 불러오는 중..."):
            time.sleep(1.5)

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

            with st.spinner("LangGraph 파이프라인 실행 중..."):
                graph_state = pipeline.invoke({"data": {}, "result": ""})
            st.info(f"파이프라인 결과: {graph_state['result']}")

            report = generate_report(company, rows)
            if report:
                st.subheader("AI 분석 리포트")
                st.markdown(report)

            st.success("분석 완료!")
