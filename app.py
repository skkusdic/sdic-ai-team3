import os
import streamlit as st
import pandas as pd
import plotly.express as px
from graph import app as graph_app
import rag
import text2sql

# Streamlit Cloud: secrets → 환경변수 복사 (로컬엔 secrets.toml 없으므로 예외 무시)
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", layout="wide", initial_sidebar_state="expanded")

# 세션 상태 초기화
if "agent_status" not in st.session_state:
    st.session_state.agent_status = {"data": False, "news": False, "analysis": False, "report": False}
if "final_state" not in st.session_state:
    st.session_state["final_state"] = None
if "company" not in st.session_state:
    st.session_state["company"] = ""
if "error" not in st.session_state:
    st.session_state["error"] = ""
if "data_source" not in st.session_state:
    st.session_state["data_source"] = ""
if "ai_result" not in st.session_state:
    st.session_state["ai_result"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "chat_company" not in st.session_state:
    st.session_state["chat_company"] = ""

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stButton,
.stDataFrame, .stSidebar, h1, h2, h3, p, span, div {
    font-family: 'Pretendard', sans-serif !important;
}

/* 배경 — 순백 */
.stApp { background-color: #f5f8fc; }

/* Streamlit 헤더 + 사이드바 접기 버튼(keyboard_double) 전체 숨김 */
header { display: none !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] > div:first-child button { display: none !important; }

/* 메인 콘텐츠 */
.block-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 2rem 1rem 4rem 1rem !important;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e8eef5;
}

/* 팀 정보 박스 */
.team-info-box {
    border: 2px solid #0066cc;
    border-radius: 12px;
    padding: 1.3rem 1.4rem;
    margin-top: 0.5rem;
    background: #f0f5ff;
}
.team-info-box .info-label {
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    color: #0066cc !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.1rem;
}
.team-info-box .info-value {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #0a1f4d !important;
    margin-bottom: 0.9rem;
}
.team-info-box .info-value:last-child { margin-bottom: 0; }

/* 메인 타이틀 */
h1 {
    color: #0a1f4d;
    font-weight: 700;
    font-size: 3.1rem !important;
    letter-spacing: -0.5px;
    padding-bottom: 0.5rem;
    text-align: center;
    white-space: nowrap;
    text-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
h1 span.accent { color: #0066cc; }

/* 구분선 */
.divider {
    height: 3px;
    background: linear-gradient(90deg, transparent, #0066cc, transparent);
    width: 100%;
    margin: 0.5rem 0 2rem 0;
}

/* 탭 상단 여백 */
[data-testid="stTabs"] {
    margin-top: 2rem !important;
}

/* Streamlit form — 흰 박스 완전 제거 */
[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
}
[data-testid="stForm"] > div {
    border: none !important;
    background: transparent !important;
}

/* 라벨 — 검색바 위 가운데 */
[data-testid="stTextInput"] label {
    display: block !important;
    text-align: center !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    color: #aab8cc !important;
    margin-bottom: 0.8rem !important;
    letter-spacing: 0.02em;
}

/* 입력창 — 테두리 잘림 방지: 모든 부모 레벨 overflow visible */
[data-testid="stTextInput"],
[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stTextInput"] > div > div > div {
    overflow: visible !important;
}
[data-testid="stTextInput"] {
    display: block !important;
    max-width: 600px !important;
    margin: 0 auto !important;
    padding-bottom: 6px !important;
}
[data-testid="stTextInput"] > div {
    width: 100% !important;
}
[data-testid="stTextInput"] input {
    border: none !important;
    border-radius: 16px !important;
    padding: 1.45rem 2.2rem !important;
    font-size: 1.38rem !important;
    font-weight: 700 !important;
    background: #ffffff !important;
    color: #0a1f4d !important;
    box-shadow: 0 3px 12px rgba(0,0,0,0.09) !important;
    outline: none !important;
    text-align: center !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
[data-testid="stTextInput"] input:focus {
    border: none !important;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.13) !important;
}
[data-testid="stTextInput"] input::placeholder {
    color: #aabbcc !important;
    font-size: 1.38rem !important;
    font-weight: 400 !important;
}

/* 버튼 — 파란색, columns로 가운데 배치 */
[data-testid="stFormSubmitButton"] {
    margin-top: 1rem !important;
}
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.8rem !important;
    transition: all 0.3s;
    box-shadow: 0 3px 10px rgba(0,102,204,0.25) !important;
    width: 100% !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #0052a3 0%, #003d7a 100%) !important;
    transform: translateY(-2px);
    box-shadow: 0 5px 14px rgba(0,102,204,0.35) !important;
}

/* 서브헤더 */
h2 {
    color: #0a1f4d !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    margin-top: 2.5rem !important;
    margin-bottom: 1.5rem !important;
    text-align: center;
}

/* 핵심 지표 대시보드 */
.kpi-card {
    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
    color: #ffffff;
    padding: 1.6rem 1.2rem 1.4rem 1.2rem;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0,102,204,0.25);
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    min-height: 170px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.3rem;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,102,204,0.35);
}

.kpi-label {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    opacity: 0.95;
    margin-bottom: 0.4rem;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
    word-break: break-word;
}

.kpi-unit {
    font-size: 0.8rem;
    opacity: 0.75;
    margin-top: 0.1rem;
}

.kpi-delta {
    font-size: 0.95rem;
    font-weight: 700;
    margin-top: 0.6rem;
    padding: 0.3rem 0.8rem;
    border-radius: 6px;
    background: rgba(255,255,255,0.15);
    display: inline-block;
}

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border: 1px solid #e8eef5 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* 분석 소주제 뱃지 */
.analysis-topic {
    display: inline-block;
    background: #0066cc;
    color: #ffffff;
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: 0.04em;
    padding: 0.5rem 1.3rem;
    border-radius: 8px;
    margin-bottom: 0.6rem;
    margin-top: 1.4rem;
}

.analysis-text {
    color: #222222;
    font-size: 1.15rem;
    line-height: 1.9;
    margin-top: 0.4rem;
    margin-bottom: 0.2rem;
}

/* 탭 텍스트 */
[data-baseweb="tab"] {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    padding: 0.8rem 1.5rem !important;
}
[data-baseweb="tab"] p,
[data-baseweb="tab"] span,
[data-baseweb="tab"] div {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
}

/* 재무 테이블 — 연한 블루 미니멀 */
.fin-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.93rem;
    margin-top: 0.5rem;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 6px rgba(0,102,204,0.08);
}
.fin-table thead tr { background: #dbeafe; }
.fin-table thead th {
    padding: 0.85rem 1rem;
    text-align: center;
    font-weight: 700;
    color: #1e40af;
    font-size: 0.85rem;
    letter-spacing: 0.03em;
}
.fin-table tbody tr:nth-child(odd)  { background: #f0f7ff; }
.fin-table tbody tr:nth-child(even) { background: #ffffff; }
.fin-table tbody tr {
    border-bottom: 1px solid #e0ecff;
    transition: background 0.15s;
}
.fin-table tbody tr:hover { background: #dbeafe; }
.fin-table tbody td {
    padding: 0.78rem 1rem;
    text-align: center;
    color: #0a1f4d;
    font-weight: 500;
}
.fin-table tbody td:first-child {
    font-weight: 700;
    color: #1e40af;
}

/* 경고/성공 메시지 */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-size: 0.95rem !important;
    border: 1px solid #e8eef5 !important;
}

/* 입력창 하단 잘림 방지 */
[data-testid="stTextInput"] > div > div {
    padding-bottom: 4px !important;
    overflow: visible !important;
}

/* 에이전트 블링크 애니메이션 */
@keyframes agentBlink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.15; }
}
.agent-dot-blink {
    animation: agentBlink 1.0s ease-in-out infinite;
    display: inline-block;
}

/* PDF 다운로드 버튼 — 미니멀 블루, 가운데 */
[data-testid="stDownloadButton"] {
    margin-top: 2rem !important;
}
[data-testid="stDownloadButton"] button {
    background: #0066cc !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 2.5rem !important;
    box-shadow: 0 3px 10px rgba(0,102,204,0.22) !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #0052a3 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 14px rgba(0,102,204,0.32) !important;
}

/* Claude 분석 탭 내 h1 크기 유지, 가운데 정렬 */
[data-testid="stMarkdownContainer"] h1 {
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
    color: #0a1f4d !important;
    text-shadow: none !important;
}

/* AI 질문 탭 — 모던 회색 라디오 버튼 */
[data-testid="stRadio"] {
    width: 100% !important;
    margin: 0.3rem 0 1.2rem 0 !important;
}
[data-testid="stRadio"] > div:last-child {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    gap: 2rem !important;
    white-space: nowrap !important;
}
[data-baseweb="radio"] {
    padding: 0.3rem 0.5rem !important;
    cursor: pointer !important;
}
[data-baseweb="radio"] p {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    margin: 0 !important;
}
[data-baseweb="radio"]:has(input:checked) p {
    color: #1e293b !important;
    font-weight: 700 !important;
}

/* AI 질문 폼 버튼만 숨김 — 탭 안에 있는 것만 타겟 (분석 시작 버튼 유지) */
[role="tabpanel"] [data-testid="stFormSubmitButton"] {
    display: none !important;
}

/* AI 애널리스트 채팅 전송 버튼 숨김 — Enter 키로 제출 */
[data-testid="stForm"]:has(input[placeholder$="질문하세요"]) [data-testid="stFormSubmitButton"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### 팀 정보")
    st.markdown("""
<div class="team-info-box">
<div class="info-label">팀 이름</div>
<div class="info-value">sdic-ai-team3</div>
<div class="info-label">분석 기업명</div>
<div class="info-value">LG 이노텍</div>
<div class="info-label">현재 주차</div>
<div class="info-value">4주차</div>
</div>
""", unsafe_allow_html=True)

    if st.session_state.get("data_source"):
        src = st.session_state["data_source"]
        if src == "cache":
            st.markdown(
                "<div style='background:#f0fff4;border:1px solid #34d399;border-radius:8px;"
                "padding:0.6rem 1rem;font-size:0.85rem;color:#065f46;font-weight:700;'>"
                "⚡ 캐시 hit — DB에서 로드</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:#eff6ff;border:1px solid #60a5fa;border-radius:8px;"
                "padding:0.6rem 1rem;font-size:0.85rem;color:#1e40af;font-weight:700;'>"
                "🌐 DART API 호출</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    agents = [
        ("data",     "Data Agent",     "DART 데이터 수집"),
        ("news",     "News Agent",     "최신 뉴스 수집"),
        ("analysis", "Analysis Agent", "AI 재무 분석"),
        ("report",   "Report Agent",   "보고서 생성"),
    ]
    loading = st.session_state.agent_status["data"] and not st.session_state.agent_status["analysis"]
    agent_rows = ""
    for key, name, desc in agents:
        active = st.session_state.agent_status[key]
        is_blinking = loading and key == "data"
        dot   = "●" if active else "○"
        color = "#0066cc" if active else "#aab8cc"
        dot_span = (
            f"<span class='agent-dot-blink' style='font-size:1.1rem;color:{color};'>{dot}</span>"
            if is_blinking else
            f"<span style='font-size:1.1rem;color:{color};'>{dot}</span>"
        )
        agent_rows += (
            f"<div style='display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0;'>"
            f"{dot_span}"
            f"<div><div style='font-weight:700;font-size:0.88rem;color:#0a1f4d;'>{name}</div>"
            f"<div style='font-size:0.75rem;color:#8899bb;'>{desc}</div></div>"
            f"</div>"
        )
    st.markdown(
        f"<div style='display:flex;flex-direction:column;align-items:center;width:100%;'>"
        f"  <div>"
        f"    <div style='text-align:center;font-weight:700;font-size:1.05rem;"
        f"color:#0a1f4d;margin-bottom:0.6rem;'>에이전트 실행 상태</div>"
        f"    {agent_rows}"
        f"  </div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # 데이터 소스 표시
    if st.session_state["final_state"]:
        data_source = st.session_state["final_state"].get("data_source", "")
        if data_source:
            st.markdown("---")
            src_color = "#0066cc" if data_source == "dart" else "#00aa66"
            st.markdown(
                f"<div style='text-align:center;margin-top:0.3rem;'>"
                f"<span style='font-size:0.78rem;font-weight:700;color:#8899bb;'>데이터 소스</span><br>"
                f"<span style='font-size:1rem;font-weight:800;color:{src_color};'>{data_source.upper()}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

# 타이틀
st.markdown('<h1>AI 재무 컨설팅 <span class="accent">어시스턴트</span></h1>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# 입력창 + 버튼
with st.form("search_form", clear_on_submit=False):
    company = st.text_input("기업명을 입력하세요", placeholder="예: LG 이노텍")
    _, btn_col, _ = st.columns([3, 2, 3])
    with btn_col:
        clicked = st.form_submit_button("분석 시작", use_container_width=True)

if clicked:
    if not company.strip():
        st.error("기업명을 입력해주세요")
    else:
        st.session_state["company"] = company
        st.session_state.agent_status = {"data": True, "news": False, "analysis": False, "report": False}
        st.session_state["error"] = ""
        st.rerun()

# Data Agent가 활성화됐고 실제 분석 실행이 필요한 경우
if st.session_state.agent_status["data"] and not st.session_state.agent_status["analysis"] and st.session_state["company"].strip():
    try:
        with st.spinner("DART 데이터 조회 및 AI 분석 중..."):
            graph_state = graph_app.invoke({
                "request": f"{st.session_state['company']} 재무 분석해줘",
                "company": st.session_state["company"],
                "next_agent": "",
                "financials": {},
                "news": [],
                "analysis": "",
                "result": "",
                "pdf_path": "",
                "data_source": None,
            })

        if not graph_state.get("financials"):
            st.session_state["error"] = "데이터를 찾을 수 없습니다."
            st.session_state["final_state"] = None
            st.session_state.agent_status = {"data": False, "analysis": False, "report": False}
        else:
            st.session_state["error"] = ""
            st.session_state["final_state"] = graph_state
            st.session_state["data_source"] = graph_state.get("data_source", "")
            st.session_state.agent_status = {"data": True, "news": True, "analysis": True, "report": True}
    except Exception as e:
        import traceback
        st.session_state["error"] = f"분석 오류: {type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        st.session_state["final_state"] = None
        st.session_state.agent_status = {"data": False, "news": False, "analysis": False, "report": False}
    st.rerun()

# delta_pct: (curr-prev)/prev*100 을 '+12.3%' 형식 문자열로
def delta_pct(curr, prev):
    if not prev:
        return None
    return f"{(curr - prev) / prev * 100:+.1f}%"

def kpi_card_html(label, value, delta):
    if delta:
        is_pos = str(delta).startswith("+")
        color  = "#86efac" if is_pos else "#fca5a5"
        arrow  = "▲" if is_pos else "▼"
        delta_block = f"<div class='kpi-delta' style='color:{color};'>{arrow} {delta}</div>"
    else:
        delta_block = ""
    return (
        f"<div class='kpi-card'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>"
        f"{delta_block}"
        f"</div>"
    )

def render_fin_table(headers, rows_data):
    header_html = "".join(f"<th>{h}</th>" for h in headers)
    rows_html   = "".join(
        f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>"
        for row in rows_data
    )
    return (
        f"<table class='fin-table'>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table>"
    )

# 결과 표시
if st.session_state["error"]:
    st.error(st.session_state["error"])
elif st.session_state["final_state"] is not None:
    final_state   = st.session_state["final_state"]
    company_label = st.session_state["company"]
    financials    = final_state.get("financials", {})
    analysis      = final_state.get("analysis", "")
    news          = final_state.get("news", [])
    pdf_path      = final_state.get("pdf_path", "")

    # DataFrame 생성
    rows = []
    for year, v in sorted(financials.items()):
        rev = v.get('매출액', 0)
        op  = v.get('영업이익', 0)
        net = v.get('순이익', 0)
        rows.append({
            '연도': year,
            '매출액 (억원)': rev,
            '영업이익 (억원)': op,
            '순이익 (억원)': net,
            '영업이익률 (%)': round(op / rev * 100, 1) if rev else 0,
        })
    df = pd.DataFrame(rows)

    # 최신·전년 지표
    sorted_years = sorted(financials.keys())
    latest_year  = sorted_years[-1]
    prev_year    = sorted_years[-2] if len(sorted_years) >= 2 else None
    latest   = financials.get(latest_year, {})
    previous = financials.get(prev_year, {}) if prev_year else {}

    rev = latest.get('매출액', 0)
    op  = latest.get('영업이익', 0)
    net = latest.get('순이익', 0)
    prev_rev = previous.get('매출액', 0)
    prev_op  = previous.get('영업이익', 0)
    prev_net = previous.get('순이익', 0)

    curr_margin = round(op / rev * 100, 1) if rev else 0
    prev_margin = round(prev_op / prev_rev * 100, 1) if prev_rev else 0
    margin_delta = f"{curr_margin - prev_margin:+.1f}%p"

    # 탭
    tab_data, tab_claude, tab_ai = st.tabs(["재무 데이터", "Claude 분석", "AI 질문 (RAG + Text2SQL)"])

    with tab_data:
        # KPI 카드 4장 (HTML, 라벨에 연도 괄호 없음)
        st.markdown(
            f"<h2 style='margin-top:1.5rem;'>핵심 재무 지표 ({latest_year}년 기준)</h2>",
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(kpi_card_html("매출액",    f"{rev:,} 억원",   delta_pct(rev, prev_rev)), unsafe_allow_html=True)
        with c2:
            st.markdown(kpi_card_html("영업이익",  f"{op:,} 억원",    delta_pct(op,  prev_op)),  unsafe_allow_html=True)
        with c3:
            st.markdown(kpi_card_html("순이익",    f"{net:,} 억원",   delta_pct(net, prev_net)), unsafe_allow_html=True)
        with c4:
            st.markdown(kpi_card_html("영업이익률", f"{curr_margin} %", margin_delta),            unsafe_allow_html=True)

        # 재무 현황 표 (HTML, 미니멀 블루)
        fin_rows = [
            [int(row['연도']), f"{int(row['매출액 (억원)']):,}", f"{int(row['영업이익 (억원)']):,}",
             f"{int(row['순이익 (억원)']):,}", f"{row['영업이익률 (%)']:.1f}%"]
            for _, row in df.iterrows()
        ]
        st.markdown(
            f"<h2 style='margin-top:1.5rem;margin-bottom:0.3rem;'>{company_label} 재무 현황</h2>"
            + render_fin_table(['연도', '매출액 (억원)', '영업이익 (억원)', '순이익 (억원)', '영업이익률 (%)'], fin_rows),
            unsafe_allow_html=True,
        )

        # 3지표 라인 차트 (팝 컬러, 굵은 선, 제목 가운데)
        fig_line = px.line(
            df, x='연도', y=['매출액 (억원)', '영업이익 (억원)', '순이익 (억원)'],
            markers=True, title=f"{company_label} 매출액 / 영업이익 / 순이익 추이",
            color_discrete_sequence=['#0066FF', '#FF6B35', '#00C49A'],
            labels={'value': '금액 (억원)', 'variable': '지표'},
        )
        fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
        fig_line.update_layout(
            title=dict(x=0.5, xanchor='center'),
            template='plotly_white',
            font=dict(family='Pretendard, sans-serif', size=12),
            margin=dict(l=80, r=40, t=60, b=40),
            legend_title_text='지표',
        )
        fig_line.update_xaxes(tickformat='d')
        st.plotly_chart(fig_line, use_container_width=True)

        # 영업이익률 라인 차트 (팝 컬러, 굵은 선, 제목 가운데)
        fig_margin = px.line(
            df, x='연도', y='영업이익률 (%)',
            markers=True, title=f"{company_label} 영업이익률 추이",
        )
        fig_margin.update_traces(line_color='#FF6B6B', line=dict(width=3), marker=dict(size=8))
        fig_margin.update_layout(
            title=dict(x=0.5, xanchor='center'),
            template='plotly_white',
            font=dict(family='Pretendard, sans-serif', size=12),
            margin=dict(l=80, r=40, t=60, b=40),
        )
        fig_margin.update_xaxes(tickformat='d')
        st.plotly_chart(fig_margin, use_container_width=True)

        # YoY 성장률 표 (HTML, 동일 디자인)
        yoy = df[['연도']].copy()
        for col in ['매출액 (억원)', '영업이익 (억원)', '순이익 (억원)']:
            col_name = col.replace(' (억원)', '')
            yoy[col_name + ' YoY'] = df[col].pct_change().apply(
                lambda x: f"{x * 100:+.1f}%" if pd.notna(x) and x == x else "—"
            )
        yoy.iloc[0, 1:] = "—"
        yoy_rows = [[int(r['연도'])] + list(r[1:]) for _, r in yoy.iterrows()]
        st.markdown(
            "<h2 style='margin-top:1.5rem;margin-bottom:0.3rem;'>YoY 성장률</h2>"
            + render_fin_table(list(yoy.columns), yoy_rows),
            unsafe_allow_html=True,
        )

    with tab_claude:
        if analysis:
            import re

            def highlight(text):
                return re.sub(
                    r'(\d[\d,\.]*\s*(?:억원|%p|%|배))',
                    r'<strong style="color:#0066cc;font-weight:800;">\1</strong>',
                    text,
                )

            # # 기호 제거 + 짧은 제목 줄(15자 미만) 필터링
            raw = [re.sub(r'^#+\s*', '', p).strip()
                   for p in re.split(r'\n+', analysis.strip()) if p.strip()]
            content_lines = [l for l in raw if len(l) >= 15]

            # 전체 내용을 문장 단위로 분리
            full_text = ' '.join(content_lines)
            sentences = [s.strip() for s in re.split(r'(?<!\d)\.(?!\d)', full_text) if len(s.strip()) > 5]

            # 3개 버킷으로 분배
            _BUCKETS_DEF = [
                ("경영 성과", ["매출", "영업이익", "순이익", "기록", "달성", "억원", "이익"]),
                ("평가",     ["평가", "수준", "산업", "경쟁", "격차", "나타나", "불과", "낮은", "높은"]),
                ("시사점",   ["시사", "과제", "필요", "개선", "효율", "절감", "강화", "판단", "위해", "전망", "향후"]),
            ]

            def assign_bucket(text):
                for bucket, kws in _BUCKETS_DEF:
                    if any(kw in text for kw in kws):
                        return bucket
                return "평가"

            buckets = {"경영 성과": [], "평가": [], "시사점": []}
            for s in sentences:
                buckets[assign_bucket(s)].append(s)

            # 비어있는 버킷은 균등 재분배
            if any(len(v) == 0 for v in buckets.items() if True):
                all_s = []
                for v in buckets.values():
                    all_s.extend(v)
                n = len(all_s)
                if n > 0:
                    chunk = max(1, n // 3)
                    keys = list(buckets.keys())
                    for i, k in enumerate(keys):
                        buckets[k] = all_s[i * chunk: (i + 1) * chunk if i < 2 else n]

            st.markdown(
                "<h2 style='margin-top:1.5rem;margin-bottom:0.4rem;'>기업 재무 분석</h2>",
                unsafe_allow_html=True,
            )
            cards = ""
            for topic, sents in buckets.items():
                if not sents:
                    continue
                para_text = '. '.join(sents).strip()
                if not para_text.endswith('.'):
                    para_text += '.'
                highlighted = highlight(para_text)
                cards += (
                    f"<div style='background:#f8faff;border-left:4px solid #0066cc;"
                    f"border-radius:0 10px 10px 0;"
                    f"padding:1.1rem 1.4rem;margin-bottom:1rem;"
                    f"box-shadow:0 1px 4px rgba(0,102,204,0.07);'>"
                    f"<div style='display:inline-block;background:#0066cc;color:#fff;"
                    f"font-weight:700;font-size:0.78rem;letter-spacing:0.06em;"
                    f"padding:0.2rem 0.7rem;border-radius:5px;margin-bottom:0.55rem;'>"
                    f"{topic}</div>"
                    f"<p style='margin:0;line-height:1.85;color:#1a1a2e;"
                    f"font-size:1.05rem;font-weight:500;'>{highlighted}</p>"
                    f"</div>"
                )
            st.markdown(
                f"<div style='margin-top:0;'>{cards}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='color:#aab8cc;text-align:center;padding:4rem 0;font-size:1.2rem;'>분석 결과가 없습니다</p>",
                unsafe_allow_html=True,
            )

        # 최근 주요 뉴스 섹션
        if news:
            st.markdown(
                "<h2 style='margin-top:2rem;margin-bottom:0.6rem;'>최근 주요 뉴스</h2>",
                unsafe_allow_html=True,
            )
            for item in news:
                title     = item.get("title", "")
                summary   = item.get("summary", "")
                published = item.get("published", "")
                url       = item.get("url", "")

                title_html = (
                    f"<a href='{url}' target='_blank' style='color:#0066cc;font-weight:700;"
                    f"font-size:1rem;text-decoration:none;'>{title}</a>"
                    if url else
                    f"<span style='color:#0a1f4d;font-weight:700;font-size:1rem;'>{title}</span>"
                )
                date_html = (
                    f"<span style='color:#8899bb;font-size:0.8rem;margin-left:0.5rem;'>{published}</span>"
                    if published else ""
                )
                summary_html = (
                    f"<p style='margin:0.4rem 0 0 0;color:#334155;font-size:0.93rem;line-height:1.7;'>{summary}</p>"
                    if summary else ""
                )

                st.markdown(
                    f"<div style='background:#f8faff;border-left:4px solid #60a5fa;"
                    f"border-radius:0 10px 10px 0;"
                    f"padding:1rem 1.4rem;margin-bottom:0.8rem;"
                    f"box-shadow:0 1px 4px rgba(0,102,204,0.07);'>"
                    f"<div>{title_html}{date_html}</div>"
                    f"{summary_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with tab_ai:
        _TEXT2SQL_KEYWORDS = {"평균", "합계", "최대", "최소", "몇", "얼마", "합", "계산", "비교", "sum", "avg", "max", "min"}

        st.markdown(
            "<h2 style='margin-top:1.5rem;margin-bottom:0.3rem;'>재무 Q&A</h2>"
            "<p style='text-align:center;color:#8899bb;font-size:0.88rem;margin-bottom:1rem;'>"
            "DART 공시 재무제표를 기반으로 수치·지표를 정확하게 조회합니다</p>",
            unsafe_allow_html=True,
        )

        _rag_has_data = rag.has_data(company_label)

        if not _rag_has_data:
            st.markdown(
                "<div style='background:#fff8f0;border:1px solid #f59e0b;border-radius:10px;"
                "padding:1.2rem 1.5rem;text-align:center;color:#92400e;font-size:1rem;font-weight:600;'>"
                "재무 데이터가 DB에 존재하지 않습니다. 먼저 기업 분석을 실행해주세요.</div>",
                unsafe_allow_html=True,
            )
        else:
            _, radio_col, _ = st.columns([2, 3, 2])
            with radio_col:
                ai_mode = st.radio(
                    "검색 모드",
                    ["자동", "RAG (문서 검색)", "Text2SQL (데이터 조회)"],
                    horizontal=True,
                    label_visibility="collapsed",
                )
            with st.form("ai_question_form"):
                ai_query = st.text_input(
                    "질문을 입력하세요",
                    placeholder="예: 영업이익률이 가장 높은 연도는? / 매출액 평균은?",
                )
                ai_clicked = st.form_submit_button("검색", use_container_width=False)
            st.markdown(
                "<p style='text-align:center;color:#aab8cc;font-size:0.82rem;"
                "margin-top:0.3rem;letter-spacing:0.02em;'>↵  Enter 키로 검색</p>",
                unsafe_allow_html=True,
            )

            if ai_clicked and ai_query.strip():
                if ai_mode == "자동":
                    use_sql = any(kw in ai_query for kw in _TEXT2SQL_KEYWORDS)
                else:
                    use_sql = ai_mode.startswith("Text2SQL")

                with st.spinner("AI가 답변을 생성 중입니다..."):
                    if use_sql:
                        result = text2sql.run(ai_query, company_label)
                        st.session_state["ai_result"] = {"type": "sql", "data": result}
                    else:
                        result = rag.answer(ai_query, company_label)
                        st.session_state["ai_result"] = {"type": "rag", "data": result}

            if st.session_state["ai_result"]:
                res = st.session_state["ai_result"]

                if res["type"] == "rag":
                    d = res["data"]
                    import re as _re
                    clean_answer = _re.sub(r'^#+\s*', '', d.get('answer', ''), flags=_re.MULTILINE).strip()
                    st.markdown(
                        "<div style='background:#f0f7ff;border-left:4px solid #0066cc;"
                        "border-radius:0 10px 10px 0;padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>"
                        f"<p style='margin:0;font-size:1.05rem;line-height:1.8;color:#1a1a2e;font-weight:500;'>"
                        f"{clean_answer}</p></div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("**참조 데이터 (상위 3건)**")
                    for i, r in enumerate(d.get("results", []), 1):
                        st.markdown(
                            f"<div style='background:#fff;border:1px solid #dbeafe;border-radius:8px;"
                            f"padding:0.7rem 1rem;margin-bottom:0.5rem;font-size:0.9rem;color:#334155;'>"
                            f"<span style='color:#0066cc;font-weight:700;'>#{i}</span> "
                            f"<span style='color:#64748b;'>유사도 {r['score']:.4f}</span> — {r['text']}</div>",
                            unsafe_allow_html=True,
                        )

                elif res["type"] == "sql":
                    d = res["data"]
                    st.markdown("**생성된 SQL**")
                    st.code(d.get("sql", ""), language="sql")
                    if d.get("error"):
                        st.error(f"SQL 실행 오류: {d['error']}")
                    elif d.get("dataframe") is not None:
                        st.markdown("**조회 결과**")
                        _df = d["dataframe"].copy()
                        # 숫자 컬럼 천단위 + 소수점 정리 (정수면 쉼표만, 소수면 소수 1자리)
                        for _col in _df.select_dtypes(include="number").columns:
                            _df[_col] = _df[_col].apply(
                                lambda x: f"{int(round(x)):,}" if x == round(x) else f"{x:,.1f}"
                            )
                        st.dataframe(_df, use_container_width=True)
                        st.caption("※ 금액 단위: 억원")

    # AI 애널리스트 채팅 섹션 (Streamlit >= 1.37 필요)
    _chat_supported = hasattr(st, "chat_message")

    st.markdown(
        "<hr style='border:none;border-top:2px solid #e8eef5;margin:2.5rem 0 0 0;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h2 style='margin-top:1.2rem;margin-bottom:0.2rem;text-align:center;'>뉴스·시황 분석</h2>"
        "<p style='text-align:center;color:#8899bb;font-size:0.88rem;margin-bottom:0;'>"
        "최신 뉴스와 재무 흐름을 종합해 시장 맥락과 투자 시사점을 해석합니다</p>",
        unsafe_allow_html=True,
    )
    if _chat_supported and st.session_state["chat_history"]:
        _, _clr_col, _ = st.columns([4, 2, 4])
        with _clr_col:
            if st.button("대화 초기화", key="clear_chat", use_container_width=True):
                st.session_state["chat_history"] = []
                st.rerun()

    if not _chat_supported:
        st.warning("AI 애널리스트 채팅은 Streamlit 1.23 이상에서 사용 가능합니다. `pip install -r requirements.txt`로 업데이트해주세요.")
    else:
        # 기업 변경 시 채팅 초기화
        if st.session_state["chat_company"] != company_label:
            st.session_state["chat_history"] = []
            st.session_state["chat_company"] = company_label

        # 채팅 비어있을 때 예시 질문 힌트
        if not st.session_state["chat_history"]:
            _examples = [
                "왜 영업이익률이 감소했어?",
                "최근 AI 관련 뉴스만 요약해줘",
                "반도체 업황이 어떤 영향을 주고 있어?",
                "최근 수주 관련 뉴스 알려줘",
                "경쟁사와 비교하면 어때?",
            ]
            _ex_html = "".join(
                f"<span style='display:inline-block;background:#f0f5ff;border:1px solid #c7d7f5;"
                f"border-radius:20px;padding:0.28rem 0.85rem;font-size:0.82rem;color:#0066cc;"
                f"margin:0.2rem;font-weight:500;'>{q}</span>"
                for q in _examples
            )
            st.markdown(
                f"<div style='text-align:center;padding:0.5rem 0 1.2rem 0;'>"
                f"<span style='color:#8899bb;font-size:0.82rem;font-weight:600;'>예시 질문 </span>"
                f"{_ex_html}</div>",
                unsafe_allow_html=True,
            )

        # 채팅 기록 표시
        for _msg in st.session_state["chat_history"]:
            if _msg["role"] == "user":
                st.markdown(
                    f"<p style='text-align:center;color:#0066cc;font-weight:700;"
                    f"font-size:1rem;padding:0.5rem 0;margin:0.2rem 0;'>{_msg['content']}</p>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(_msg["content"])

        # 채팅 입력 폼 (가운데 정렬, 버튼 CSS로 숨김)
        with st.form("chat_form", clear_on_submit=True):
            _, _ci, _ = st.columns([1, 5, 1])
            with _ci:
                _chat_prompt = st.text_input(
                    "질문 입력",
                    placeholder=f"{company_label}에 대해 질문하세요",
                    label_visibility="collapsed",
                )
            _chat_submit = st.form_submit_button("전송", use_container_width=False)

        if _chat_submit and _chat_prompt.strip():
            with st.spinner("분석 중..."):
                _chat_result = rag.chat_answer(
                    _chat_prompt, company_label,
                    analysis=analysis,
                    financials=financials,
                )
                _chat_response = _chat_result["answer"]
            st.session_state["chat_history"].append({"role": "user",      "content": _chat_prompt})
            st.session_state["chat_history"].append({"role": "assistant", "content": _chat_response})
            st.rerun()

    # PDF 다운로드 버튼 (탭 밖, 가운데 배치)
    if pdf_path:
        try:
            with open(pdf_path, "rb") as f:
                _, mid, _ = st.columns([2, 1, 2])
                with mid:
                    st.download_button(
                        label="PDF 리포트 다운로드",
                        data=f,
                        file_name=f"{company_label}_재무분석.pdf",
                        mime="application/pdf",
                    )
        except FileNotFoundError:
            st.warning(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

