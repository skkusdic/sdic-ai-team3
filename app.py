import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from graph import app as graph_app
from report import generate_report

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", layout="wide", initial_sidebar_state="expanded")

# 에이전트 상태 초기화
if "agent_status" not in st.session_state:
    st.session_state.agent_status = {"data": False, "analysis": False, "report": False}

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stButton,
.stDataFrame, .stSidebar, h1, h2, h3, p, span, div {
    font-family: 'Pretendard', sans-serif !important;
}

/* 배경 — 순백 */
.stApp { background-color: #f5f8fc; }

/* Streamlit 헤더 전체 숨김 */
header { display: none !important; }
[data-testid="stHeader"] { display: none !important; }

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
    font-size: 2.2rem !important;
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
    border: 3px solid #0066cc !important;
    border-radius: 16px !important;
    padding: 1.2rem 2rem !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    background: #ffffff !important;
    color: #0a1f4d !important;
    box-shadow: 0 3px 10px rgba(0,102,204,0.15) !important;
    outline: none !important;
    text-align: center !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
[data-testid="stTextInput"] input:focus {
    border: 3px solid #0052a3 !important;
    box-shadow: 0 0 0 4px rgba(0,102,204,0.15) !important;
}
[data-testid="stTextInput"] input::placeholder {
    color: #aabbcc !important;
    font-size: 1.25rem !important;
    font-weight: 400 !important;
}

/* 버튼 — 가운데 정렬, 파란색 */
[data-testid="stFormSubmitButton"] {
    display: flex !important;
    justify-content: center !important;
    margin-top: 1.2rem !important;
}
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    padding: 0.9rem 2.5rem !important;
    transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(0,102,204,0.3) !important;
    width: 280px !important;
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
    font-weight: 600 !important;
    padding: 0.8rem 1.5rem !important;
}
[data-baseweb="tab"] p,
[data-baseweb="tab"] span,
[data-baseweb="tab"] div {
    font-size: 1.1rem !important;
}

/* 재무 테이블 커스텀 */
.fin-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 1.1rem;
    margin-top: 0.5rem;
}
.fin-table thead tr {
    border-bottom: 2px solid #0066cc;
}
.fin-table thead th {
    padding: 0.9rem 1rem;
    text-align: center;
    font-weight: 700;
    color: #0066cc;
    font-size: 0.95rem;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.fin-table tbody tr {
    border-bottom: 1px solid #e8eef5;
    transition: background 0.15s;
}
.fin-table tbody tr:hover { background: #f0f5ff; }
.fin-table tbody td {
    padding: 0.9rem 1rem;
    text-align: center;
    color: #0a1f4d;
    font-weight: 500;
}
.fin-table tbody td:first-child {
    font-weight: 700;
    color: #0066cc;
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
    st.markdown("### 에이전트 실행 상태")

    agents = [
        ("data",     "Data Agent",     "DART 데이터 수집"),
        ("analysis", "Analysis Agent", "AI 재무 분석"),
        ("report",   "Report Agent",   "보고서 생성"),
    ]
    for key, name, desc in agents:
        active = st.session_state.agent_status[key]
        dot   = "●" if active else "○"
        color = "#0066cc" if active else "#aab8cc"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0;'>"
            f"<span style='font-size:1.1rem;color:{color};'>{dot}</span>"
            f"<div><div style='font-weight:700;font-size:0.88rem;color:#0a1f4d;'>{name}</div>"
            f"<div style='font-size:0.75rem;color:#8899bb;'>{desc}</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

# 타이틀
st.markdown('<h1>AI 재무 컨설팅 <span class="accent">어시스턴트</span></h1>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# 입력창 + 버튼
with st.form("search_form", clear_on_submit=False):
    company = st.text_input("기업명을 입력하세요", placeholder="예: LG 이노텍")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        clicked = st.form_submit_button("분석 시작", use_container_width=True)

if clicked:
    if not company.strip():
        st.error("기업명을 입력해주세요")
    else:
        # Data Agent 시뮬레이션 — 상태 ● 표시
        st.session_state.agent_status = {"data": True, "analysis": False, "report": False}
        st.rerun()

# 분석 결과가 있을 때 (session_state에서 결과 복원)
if "financials" not in st.session_state:
    st.session_state.financials = {}
if "analysis" not in st.session_state:
    st.session_state.analysis = ""
if "company_result" not in st.session_state:
    st.session_state.company_result = ""

# Data Agent가 활성화됐고 실제 분석 실행이 필요한 경우
if st.session_state.agent_status["data"] and not st.session_state.agent_status["analysis"] and company.strip():
    with st.spinner("DART 데이터 조회 및 AI 분석 중..."):
        graph_state = graph_app.invoke({"company_name": company, "data": {}, "result": "", "next": ""})

    data = graph_state.get("data", {})
    st.session_state.financials = data.get("financials", {})
    st.session_state.analysis = graph_state.get("result", "")
    st.session_state.company_result = company
    st.session_state.agent_status = {"data": True, "analysis": True, "report": True}
    st.rerun()

# 결과 표시
if st.session_state.financials:
    financials = st.session_state.financials
    analysis = st.session_state.analysis
    company_label = st.session_state.company_result

    # 최신 연도 핵심 지표
    latest_year = max(financials.keys())
    prev_year = latest_year - 1
    latest = financials.get(latest_year, {})
    previous = financials.get(prev_year, {})

    revenue = latest.get('매출액', 0)
    operating_profit = latest.get('영업이익', 0)
    net_profit = latest.get('순이익', 0)
    prev_revenue = previous.get('매출액', 0)
    prev_operating = previous.get('영업이익', 0)
    prev_net = previous.get('순이익', 0)

    revenue_growth = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    operating_margin = (operating_profit / revenue * 100) if revenue > 0 else 0
    net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
    prev_op_margin = (prev_operating / prev_revenue * 100) if prev_revenue > 0 else 0
    prev_net_margin = (prev_net / prev_revenue * 100) if prev_revenue > 0 else 0
    op_margin_delta = operating_margin - prev_op_margin
    net_margin_delta = net_margin - prev_net_margin
    revenue_delta = revenue - prev_revenue

    def delta_html(val, fmt="+,.0f", unit="억원"):
        if val > 0:
            return f"<div class='kpi-delta' style='color:#86efac;'>▲ {val:{fmt}} {unit}</div>"
        elif val < 0:
            return f"<div class='kpi-delta' style='color:#fca5a5;'>▼ {abs(val):{fmt[1:]}} {unit}</div>"
        return f"<div class='kpi-delta' style='opacity:0.6;'>— 0 {unit}</div>"

    def delta_pct_html(val):
        if val > 0:
            return f"<div class='kpi-delta' style='color:#86efac;'>▲ {val:+.1f}%p vs {prev_year}년</div>"
        elif val < 0:
            return f"<div class='kpi-delta' style='color:#fca5a5;'>▼ {abs(val):.1f}%p vs {prev_year}년</div>"
        return f"<div class='kpi-delta' style='opacity:0.6;'>— 0%p vs {prev_year}년</div>"

    # KPI 카드
    st.markdown(f"<h2 style='margin-top: 2rem;'>핵심 재무 지표 ({latest_year}년 기준)</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">매출액</div>
            <div class="kpi-value">{revenue:,.0f}</div>
            <div class="kpi-unit">억원</div>
            {delta_html(revenue_delta)}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        g_color = "#86efac" if revenue_growth > 0 else "#fca5a5"
        g_arrow = "▲" if revenue_growth > 0 else "▼"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">매출 성장률</div>
            <div class="kpi-value">{revenue_growth:+.1f}%</div>
            <div class="kpi-unit">전년 대비</div>
            <div class="kpi-delta" style="color:{g_color};">{g_arrow} {prev_year}년 → {latest_year}년</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">영업이익률</div>
            <div class="kpi-value">{operating_margin:.1f}%</div>
            <div class="kpi-unit">{operating_profit:,.0f}억원</div>
            {delta_pct_html(op_margin_delta)}
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">순이익률</div>
            <div class="kpi-value">{net_margin:.1f}%</div>
            <div class="kpi-unit">{net_profit:,.0f}억원</div>
            {delta_pct_html(net_margin_delta)}
        </div>
        """, unsafe_allow_html=True)

    # 결과 탭
    st.markdown("<br>", unsafe_allow_html=True)
    tab_data, tab_claude = st.tabs(["📊 재무 데이터", "🤖 Claude 분석"])

    with tab_data:
        # 멀티플 바 차트
        st.markdown(f"<h2 style='margin-top: 1.5rem;'>재무 지표 비교 (2020~2025)</h2>", unsafe_allow_html=True)
        chart_data = pd.DataFrame([
            {"연도": str(year), "매출액": v.get('매출액', 0), "영업이익": v.get('영업이익', 0), "순이익": v.get('순이익', 0)}
            for year, v in sorted(financials.items())
        ])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data["연도"], y=chart_data["매출액"], name='매출액',
            marker_color='#0066cc', marker_line_width=0
        ))
        fig.add_trace(go.Bar(
            x=chart_data["연도"], y=chart_data["영업이익"], name='영업이익',
            marker_color='#ff6b6b', marker_line_width=0
        ))
        fig.add_trace(go.Bar(
            x=chart_data["연도"], y=chart_data["순이익"], name='순이익',
            marker_color='#4ecdc4', marker_line_width=0
        ))
        fig.update_layout(
            barmode='group',
            xaxis_title="연도", yaxis_title="금액 (억원)",
            hovermode='x unified', template='plotly_white',
            height=400, margin=dict(l=40, r=40, t=20, b=40),
            font=dict(family='Pretendard, sans-serif', size=12),
            plot_bgcolor='#f9fbfd',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            bargap=0.2, bargroupgap=0.05
        )
        st.plotly_chart(fig, use_container_width=True)

        # 재무 테이블 — 커스텀 HTML
        st.markdown(f"<h2 style='margin-top: 1.5rem;'>{company_label} 재무 현황 (2020~2025)</h2>", unsafe_allow_html=True)
        table_rows = "".join([
            f"<tr><td>{year}</td><td>{v.get('매출액', 0):,}</td>"
            f"<td>{v.get('영업이익', 0):,}</td><td>{v.get('순이익', 0):,}</td></tr>"
            for year, v in sorted(financials.items())
        ])
        st.markdown(f"""
        <table class="fin-table">
            <thead><tr>
                <th>연도</th><th>매출액 (억원)</th>
                <th>영업이익 (억원)</th><th>순이익 (억원)</th>
            </tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
        """, unsafe_allow_html=True)

    with tab_claude:
        if analysis:
            import re
            # 소수점 분리 방지: 숫자.숫자 는 분리하지 않음
            clean = re.sub(r'\n+', ' ', analysis).strip()
            sentences = [s.strip() for s in re.split(r'(?<!\d)\.(?!\d)', clean) if s.strip()]
            topics = ["매출 성장성", "수익성", "영업이익률", "순이익률", "전년 대비", "변화"]

            blocks = []
            for sentence in sentences:
                matched = next((t for t in topics if t in sentence), None)
                badge = f"<div class='analysis-topic'>{matched}</div>" if matched else ""
                blocks.append(f"{badge}<p class='analysis-text'>{sentence}.</p>")

            st.markdown("".join(blocks), unsafe_allow_html=True)
        else:
            st.markdown(
                "<p style='color:#aab8cc;text-align:center;padding:4rem 0;font-size:1.2rem;'>세션 당일 연결 예정</p>",
                unsafe_allow_html=True,
            )

    generate_report(company_label, financials, analysis)
    st.success("✅ 분석 완료! PDF 보고서가 생성되었습니다.")
