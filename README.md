# SDIC AI Team 3 — 기업 재무 분석 에이전트

🔗 **배포 URL**: https://sdic-ai-team3.streamlit.app/

LangGraph 멀티 에이전트 파이프라인으로 기업 재무 데이터를 수집·분석하고, RAG와 Text2SQL 기반 AI 질의응답을 제공하는 Streamlit 웹 애플리케이션입니다.

---

## 팀 구성

| 역할 | 이름 | 담당 파일 |
|---|---|---|
| Pipeline Lead | 채예진 | `graph.py`, `agents/report_agent.py` |
| Data Lead | 이윤이 | `data.py`, `db.py` |
| UI Lead | 이정원 | `app.py`, `rag.py`, `text2sql.py` |

**분석 대상 기업**: LG 이노텍

---

## 기술 스택

| 분류 | 기술 |
|---|---|
| AI 파이프라인 | LangGraph 1.x (Supervisor 패턴) |
| LLM | Claude Haiku (`claude-haiku-4-5`) via Anthropic API |
| 데이터 수집 | DART-FSS API (공시 재무제표) |
| 검색 (RAG) | TF-IDF + 코사인 유사도 (scikit-learn) |
| 자연어 SQL | Text2SQL — Claude → SQLite |
| 데이터 저장 | SQLite (`data/sdic.db`) |
| 시각화 | Plotly, Streamlit |
| PDF 생성 | fpdf2 + NanumGothic |
| UI | Streamlit 1.x |

---

## 폴더 구조

```
sdic-ai-team3/
├── app.py                  # Streamlit UI — 탭·KPI 카드·차트·AI 질문
├── graph.py                # LangGraph Supervisor 파이프라인
├── rag.py                  # TF-IDF RAG — 재무 청크 검색 + Claude 답변
├── text2sql.py             # 자연어 → SQL 변환 + 안전 실행
├── data.py                 # DART-FSS API 수집 로직
├── db.py                   # SQLite CRUD (data/sdic.db)
├── claude_client.py        # Claude API 래퍼 (모델 고정: claude-haiku-4-5)
├── report.py               # 보고서 유틸
├── agents/
│   ├── supervisor_agent.py # 파이프라인 진입 노드
│   ├── data_agent.py       # DART 수집 + DB 캐시 노드
│   ├── analysis_agent.py   # Claude 재무 분석 노드
│   ├── report_agent.py     # fpdf2 PDF 생성 노드 (RAG 보충 포함)
│   └── no_data_agent.py    # 데이터 없음 종료 노드
├── data/
│   └── sdic.db             # SQLite 재무 데이터베이스
├── output/                 # 생성된 PDF 저장 경로
├── fonts/
│   └── NanumGothic.ttf     # 한글 PDF 폰트
├── .env                    # API 키 (git 제외)
└── requirements.txt
```

---

## 데이터 흐름

```
기업명 입력 (app.py)
  └─▶ LangGraph Supervisor (graph.py)
        ├─▶ Data Agent      : DB 캐시 확인 → 없으면 DART API 호출 → SQLite 저장
        ├─▶ Analysis Agent  : 최신 연도 재무 데이터 → Claude 분석문 생성
        └─▶ Report Agent    : RAG 청크 보충 → fpdf2 PDF 생성
  └─▶ 결과 출력 (app.py)
        ├─ 재무 데이터 탭   : KPI 카드, 재무 테이블, Plotly 차트, YoY 성장률
        ├─ Claude 분석 탭   : 경영 성과·평가·시사점 카드
        └─ AI 질문 탭       : RAG 문서 검색 또는 Text2SQL 데이터 조회
```

---

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```
DART_API_KEY=your_dart_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

- DART API 키 발급: https://opendart.fss.or.kr
- Anthropic API 키 발급: https://console.anthropic.com

### 3. 앱 실행

```bash
streamlit run app.py
```

---

## 주요 기능

### 재무 데이터 탭
- 핵심 지표 KPI 카드 4장 (매출액·영업이익·순이익·영업이익률, 전년 대비 증감률)
- 5개년 재무 현황 테이블
- 매출액 / 영업이익 / 순이익 추이 라인 차트
- 영업이익률 추이 라인 차트
- YoY 성장률 테이블

### Claude 분석 탭
- 경영 성과·평가·시사점 3개 카드로 분류된 AI 분석 문단

### AI 어시스턴트에 질문하기 탭
- **RAG 모드**: TF-IDF 코사인 유사도로 관련 재무 청크 검색 후 Claude 답변 생성
- **Text2SQL 모드**: 자연어 질문 → SQL 자동 생성 → SQLite 직접 조회
- **자동 모드**: 질문 키워드로 RAG / Text2SQL 자동 선택

### PDF 리포트
- fpdf2 기반 한글 PDF 자동 생성
- 재무 데이터 표 + Claude 분석 + RAG 연도별 요약 3섹션 구성

---

## 보안 규칙

- **API 키**: `.env` 파일에만 저장, 절대 코드에 하드코딩 금지
- **모델 고정**: `claude_client.py`만 통해 호출, 모델은 `claude-haiku-4-5` 고정
- **SQL 안전장치**: SELECT 전용, DDL/DML 키워드 차단, 쿼리 체이닝 방지, LIMIT 자동 추가
- **CI 검증**: `.github/workflows/model-check.yml` — push마다 모델명 자동 검사

---

## 5분 데모 시나리오

### Case 1 — LG 이노텍 (배정 기업)
검색창에 `LG 이노텍` 입력 → 분석 시작

확인 항목:
- 사이드바 `DART` 표시 (첫 호출)
- KPI 카드·차트·분석·PDF 버튼 정상 출력
- 두 번째 입력 시 사이드바 `CACHE` 즉시 반응

### Case 2 — AI 질문 (RAG)
AI 질문 탭 → `2023년 수익성 평가는?`

확인 항목:
- 참조 데이터 최대 3건 + Claude 답변 출력
- 답변 수치가 참조 청크와 일치

### Case 3 — AI 질문 (Text2SQL)
AI 질문 탭 → `5년 평균 매출액은?`

확인 항목:
- `SELECT AVG(...) AS 평균_매출액` SQL 표시
- 조회 결과 행 + 단위(억원) 표시

### Case 4 — 오류 처리
검색창에 `asdfasdf` 입력

확인 항목:
- 빨간 에러 배너: "데이터를 찾을 수 없습니다."
- AI 질문 탭: "재무 데이터가 DB에 존재하지 않습니다." 메시지 (입력폼 비활성)
