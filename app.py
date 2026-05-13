import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from graph import app as graph_app

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", layout="wide", initial_sidebar_state="expanded")

# 세션 상태 초기화
if "agent_status" not in st.session_state:
    st.session_state.agent_status = {"data": False, "analysis": False, "report": False}
if "final_state" not in st.session_state:
    st.session_state["final_state"] = None
if "company" not in st.session_state:
    st.session_state["company"] = ""
if "error" not in st.session_state:
    st.session_state["error"] = ""

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
    margin-top: 1.2rem !important;
}
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    padding: 0.9rem 2.2rem !important;
    transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(0,102,204,0.3) !important;
    width: 100% !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #0052a3 0%, #003d7a 100%) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,102,204,0.4) !important;
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
<div class="info-value">3주차</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    agents = [
        ("data",     "Data Agent",     "DART 데이터 수집"),
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
        st.session_state.agent_status = {"data": True, "analysis": False, "report": False}
        st.session_state["error"] = ""
        st.rerun()

# Data Agent가 활성화됐고 실제 분석 실행이 필요한 경우
if st.session_state.agent_status["data"] and not st.session_state.agent_status["analysis"] and st.session_state["company"].strip():
    with st.spinner("DART 데이터 조회 및 AI 분석 중..."):
        graph_state = graph_app.invoke({
            "request": f"{st.session_state['company']} 재무 분석해줘",
            "company": st.session_state["company"],
            "next_agent": "",
            "financials": {},
            "analysis": "",
            "result": "",
            "pdf_path": "",
        })

    if not graph_state.get("financials"):
        st.session_state["error"] = graph_state.get("result", "") or "데이터를 찾을 수 없습니다."
        st.session_state["final_state"] = None
        st.session_state.agent_status = {"data": False, "analysis": False, "report": False}
    else:
        st.session_state["error"] = ""
        st.session_state["final_state"] = graph_state
        st.session_state.agent_status = {"data": True, "analysis": True, "report": True}
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
    tab_data, tab_claude = st.tabs(["재무 데이터", "Claude 분석"])

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
            clean = re.sub(r'\n+', ' ', analysis).strip()
            sentences = [s.strip() for s in re.split(r'(?<!\d)\.(?!\d)', clean) if s.strip()]

            def highlight(text):
                # 숫자+단위(억원, %, %p, 배) 파란 볼드 강조
                return re.sub(
                    r'(\d[\d,\.]*\s*(?:억원|%p|%|배))',
                    r'<strong style="color:#0066cc;font-weight:800;">\1</strong>',
                    text,
                )

            cards = ""
            for i, s in enumerate(sentences, 1):
                highlighted = highlight(s)
                cards += (
                    f"<div style='"
                    f"display:flex;align-items:flex-start;gap:1rem;"
                    f"background:#f8faff;border-left:4px solid #0066cc;"
                    f"border-radius:0 10px 10px 0;"
                    f"padding:1.1rem 1.4rem;margin-bottom:0.9rem;"
                    f"box-shadow:0 1px 4px rgba(0,102,204,0.07);'>"
                    f"<span style='min-width:1.7rem;height:1.7rem;"
                    f"background:#0066cc;color:#fff;font-weight:800;"
                    f"font-size:0.85rem;border-radius:50%;"
                    f"display:flex;align-items:center;justify-content:center;"
                    f"flex-shrink:0;margin-top:0.05rem;'>{i}</span>"
                    f"<p style='margin:0;line-height:1.85;color:#1a1a2e;"
                    f"font-size:1.05rem;font-weight:500;'>{highlighted}.</p>"
                    f"</div>"
                )
            st.markdown(
                f"<div style='margin-top:1.5rem;'>{cards}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='color:#aab8cc;text-align:center;padding:4rem 0;font-size:1.2rem;'>분석 결과가 없습니다</p>",
                unsafe_allow_html=True,
            )

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
