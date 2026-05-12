# sdic-ai-team3

LangGraph Supervisor 아키텍처 기반 기업 재무 분석 에이전트 (DART API + Claude + Streamlit + fpdf2)

---

## 폴더 구조

```
sdic-ai-team3/
├── app.py                  # Streamlit UI, 에이전트 실행 상태 사이드바, KPI 대시보드
├── graph.py                # LangGraph StateGraph, Supervisor 라우팅, conditional edge
├── data.py                 # DART API 호출, 법인코드 조회, SQLite 저장
├── claude_client.py        # Anthropic SDK 래퍼 (모델 고정: claude-haiku-4-5)
├── report.py               # fpdf2 PDF 생성 (Week 4 완성 예정)
├── agents/
│   ├── __init__.py
│   ├── data_agent.py       # DART 재무 데이터 수집 노드
│   ├── analysis_agent.py   # Claude 재무 분석 텍스트 생성 노드
│   └── report_agent.py     # fpdf2 한글 PDF 보고서 생성 노드
└── fonts/
    └── NanumGothic.ttf     # PDF 한글 폰트
```

---

## 설치

```bash
pip install -r requirements.txt
```

프로젝트 루트에 `.env` 파일을 생성하고 아래 두 키를 입력합니다.

```
DART_API_KEY=your_dart_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

- DART API 키 발급: https://opendart.fss.or.kr
- Anthropic API 키 발급: https://console.anthropic.com

---

## 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 5분 시연 시나리오

아래 3개 케이스를 순서대로 입력해 전체 파이프라인을 검증합니다.

### Case 1. 팀 배정 회사 (정상 플로우 전체 확인)

| 팀 | 입력 기업명 |
|---|---|
| Team 1 | `에이피알` |
| Team 2 | `삼성전자` |
| Team 3 | `LG 이노텍` |

**확인 항목**

- 사이드바: Data Agent / Analysis Agent / Report Agent 3개 모두 파란 점(완료)
- 탭 1 (재무 데이터): KPI 카드 4장(매출액, 매출 성장률, 영업이익률, 순이익률) + 재무 현황 테이블 + 연도별 바 차트
- 탭 2 (Claude 분석): 한국어 분석 문단 (영업이익률 수치로 시작)
- PDF 다운로드 버튼 클릭 후 화면 유지 확인

---

### Case 2. 카카오 (업종별 계정명 alias 확인)

검색창에 `카카오` 입력

**확인 항목**

- 카카오는 매출을 "매출액" 대신 "영업수익"으로 보고하는 IT 회사
- 사이드바 3개 완료 및 KPI 카드에 실제 수치 출력 확인
- 0원 또는 N/A 없이 정상 파싱됐는지 확인

---

### Case 3. asdfasdf (오류 처리 확인)

검색창에 `asdfasdf` 입력

**확인 항목**

- 사이드바: Data Agent 완료 / Analysis Agent 대기 / Report Agent 대기
- 화면 중앙에 "데이터를 찾을 수 없습니다" 경고 메시지
- KPI 카드, 차트, PDF 버튼 미노출
- 앱 크래시 없음

---

## 파이프라인 흐름

```
기업명 입력
  └── Supervisor (graph.py)
        ├── data_agent    : DART API 호출 -> financials dict
        │     ├── 데이터 있음  -> analysis_agent
        │     └── 데이터 없음  -> no_data_node -> "데이터를 찾을 수 없습니다"
        ├── analysis_agent: Claude API -> 분석 텍스트
        └── report_agent  : fpdf2 -> PDF 파일
```

---

## Week 4 예고

| 기능 | 내용 |
|---|---|
| SQLite 캐시 | 동일 기업 재검색 시 DART API 재호출 없이 로컬 DB에서 즉시 반환 |
| RAG | 과거 분석 리포트를 임베딩 인덱스로 구축, 유사 기업 사례 참조 |
| Text2SQL | 자연어 질의를 SQLite 쿼리로 변환해 재무 데이터 조회 |
| Streamlit Cloud 배포 | 공개 URL 발급 및 팀 외부 공유 가능 |
