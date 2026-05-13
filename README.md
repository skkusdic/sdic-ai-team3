# sdic-ai-team3

LangGraph Supervisor + Streamlit + DART API + Claude Haiku + fpdf2 로 구축한 기업 재무 분석 AI 에이전트

---

## 폴더 구조

```
sdic-ai-team3/
├── app.py                     # Streamlit UI
├── graph.py                   # LangGraph Supervisor 파이프라인
├── data.py                    # DART API 수집 + SQLite 캐시
├── claude_client.py           # Claude Haiku API 헬퍼
├── report.py                  # (예비) 보고서 유틸
├── agents/
│   ├── __init__.py
│   ├── supervisor_agent.py    # 요청 수신 및 파이프라인 진입
│   ├── data_agent.py          # DART 데이터 수집 노드
│   ├── analysis_agent.py      # Claude 재무 분석 노드
│   ├── no_data_agent.py       # 데이터 없음 종료 노드
│   └── report_agent.py        # fpdf2 PDF 생성 노드
└── fonts/
    └── NanumGothic.ttf        # 한글 PDF 렌더링용 폰트
```

---

## 설치

```bash
pip install -r requirements.txt
```

프로젝트 루트에 `.env` 파일을 만들고 아래 두 키를 입력합니다.

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

---

## 5분 시연 시나리오

팀별 배정 기업은 아래와 같습니다.

| 팀 | 배정 기업 |
|---|---|
| Team 1 | 에이피알 |
| Team 2 | 삼성전자 |
| Team 3 | LG 이노텍 |

### Case 1 - 본인 팀 배정 기업 입력

검색창에 배정 기업명을 입력하고 분석 시작 버튼을 누릅니다.

화면에 떠야 할 것:
- 핵심 재무 지표 KPI 카드 4장 (매출액, 영업이익, 순이익, 영업이익률)
- 5개년 재무 현황 테이블
- 매출액 / 영업이익 / 순이익 추이 라인 차트
- 영업이익률 추이 라인 차트
- YoY 성장률 테이블
- Claude 분석 탭 내 문장 카드 목록
- PDF 리포트 다운로드 버튼

### Case 2 - 카카오 입력

검색창에 `카카오` 를 입력합니다.

화면에 떠야 할 것: Case 1과 동일한 재무 대시보드 (카카오 데이터 기준)

### Case 3 - 존재하지 않는 기업명 입력

검색창에 `asdfasdf` 처럼 DART에 없는 문자열을 입력합니다.

화면에 떠야 할 것:
- 빨간 에러 배너: **"데이터를 찾을 수 없습니다."**
- 분석, PDF 생성 없이 즉시 종료

---

## Week 4 예고

- SQLite 캐시 고도화 - 중복 DART 호출 최소화
- RAG 인덱스 구축 - 재무 문서 임베딩 + 코사인 유사도 검색
- Text2SQL - 자연어 질의를 SQL 로 변환해 SQLite 직접 조회
- Streamlit Cloud 배포 - 공개 URL 로 팀 데모 제공
