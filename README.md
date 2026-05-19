# SDIC AI Team 3 — 기업 재무·뉴스 통합 분석 에이전트

🔗 **배포 URL**: https://sdic-ai-team3.streamlit.app/

DART 재무 데이터와 최신 뉴스를 함께 수집하고, LangGraph 멀티 에이전트 구조로 AI 기업 분석 및 PDF 보고서를 자동 생성하는 Streamlit 웹 애플리케이션입니다.

기존 재무 수치 중심 분석에서 한 단계 나아가, 최신 뉴스 기사 본문까지 Claude에게 입력해 실제 투자 분석에 가까운 형태의 결과물을 만듭니다.

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
| 재무 데이터 수집 | DART-FSS API (공시 재무제표) |
| 뉴스 수집 | Google News RSS + 네이버 뉴스 본문 크롤링 |
| 검색 (RAG) | TF-IDF + 코사인 유사도 (scikit-learn) |
| 자연어 SQL | Text2SQL (Claude → SQLite) |
| 데이터 저장 | SQLite (`data/sdic.db`) |
| 시각화 | Plotly, Streamlit |
| PDF 생성 | fpdf2 + NanumGothic |
| UI | Streamlit 1.x |

---

## 폴더 구조

```
sdic-ai-team3/
├── app.py                  # Streamlit UI (탭, KPI 카드, 차트, 뉴스 카드, AI 질문)
├── graph.py                # LangGraph 멀티 에이전트 파이프라인 정의
├── rag.py                  # TF-IDF RAG (재무 청크 검색 + Claude 답변)
├── text2sql.py             # 자연어 → SQL 변환 + 안전 실행
├── data.py                 # DART-FSS API 수집 로직
├── db.py                   # SQLite CRUD (data/sdic.db)
├── claude_client.py        # Claude API 래퍼 (모델 고정: claude-haiku-4-5)
├── report.py               # 보고서 유틸
├── agents/
│   ├── supervisor_agent.py # 파이프라인 진입 노드
│   ├── data_agent.py       # DART 수집 + DB 캐시 노드
│   ├── news_agent.py       # 뉴스 수집, 본문 크롤링, 관련성 필터링 노드 (신규)
│   ├── analysis_agent.py   # 재무 + 뉴스 통합 Claude 분석 노드
│   ├── report_agent.py     # fpdf2 PDF 생성 노드 (뉴스 섹션 포함)
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

## 시스템 구조

에이전트 4개가 순서대로 실행되며, 각자 맡은 역할이 명확하게 나뉩니다.

```
기업명 입력 (app.py)
  └─▶ Supervisor Agent   : 요청을 받아 파이프라인 시작
        │
        ▼
      Data Agent         : DART API에서 기업 재무 데이터 수집 (DB 캐시 활용)
        │
        ▼
      News Agent         : 최신 뉴스 수집 → 기사 본문 크롤링 → AI 관련성 필터링 → 상위 2개 선별
        │
        ├─▶ (재무 데이터 없음) No Data Agent : 안내 메시지 출력 후 종료
        │
        ▼
      Analysis Agent     : 재무 데이터 + 뉴스 본문을 함께 Claude에 입력 → 분석문 생성
        │
        ▼
      Report Agent       : PDF 보고서 자동 생성 (재무 표 + 분석 + 뉴스 + RAG 요약)
        │
        ▼
      결과 출력 (app.py)
        ├─ 재무 데이터 탭  : KPI 카드, 재무 테이블, Plotly 차트, YoY 성장률
        ├─ Claude 분석 탭  : 경영 성과·평가·시사점 카드 + 최근 뉴스 카드
        └─ AI 질문 탭      : RAG 문서 검색 또는 Text2SQL 데이터 조회
```

### 에이전트 역할 요약

| 에이전트 | 하는 일 |
|---|---|
| Data Agent | 기업 재무 데이터(매출·영업이익·순이익)를 공공 데이터(DART)에서 가져옵니다. 이미 가져온 기업이면 저장된 데이터를 바로 씁니다. |
| News Agent | 입력한 기업 이름으로 최신 뉴스를 수집하고, 기사 본문을 직접 읽어 투자 관련성이 높은 기사 2개를 추립니다. |
| Analysis Agent | 재무 수치와 뉴스 기사 내용을 함께 Claude에 전달해 통합 분석문을 작성합니다. |
| Report Agent | 재무 데이터, AI 분석, 주요 뉴스를 하나의 PDF 파일로 만들어 저장합니다. |

---

## 뉴스 수집 및 필터링

### 동작 방식

1. **뉴스 수집**: 입력한 기업명에 "실적 전망 수주" 키워드를 붙여 Google News RSS에서 최근 기사 최대 10개를 가져옵니다.

2. **기사 본문 크롤링**: 각 기사 제목으로 네이버 뉴스를 검색해 실제 기사 페이지를 찾고, 본문 텍스트를 직접 읽습니다 (최대 400자). 단순 제목만 쓰지 않고 실제 기사 내용을 활용합니다.

3. **AI 관련성 필터링**: 수집한 기사 목록 전체를 Claude에 보내 투자 분석에 얼마나 유용한지 0~10점으로 채점합니다.

   - 높은 점수를 받는 기사: 실적 발표, 수주 계약, 목표주가 변경, AI·반도체 모멘텀, 산업 전망
   - 낮은 점수를 받는 기사 (제외): 행사 참가, 봉사활동, 홍보성 보도, 사건·사고

4. **Top-K 선별**: 점수 기준으로 상위 2개 기사만 최종 선택해 분석에 활용합니다.

### 결과 활용

선별된 뉴스 2개는 다음 3곳에 반영됩니다.

- **Claude 분석 프롬프트**: 재무 수치와 기사 본문이 함께 입력되어 뉴스 팩트가 분석문에 녹아납니다.
- **Streamlit UI**: Claude 분석 탭 하단에 뉴스 카드 형태로 제목·날짜·요약이 표시됩니다.
- **PDF 보고서**: "최근 주요 뉴스" 섹션으로 포함됩니다.

---

## 분석 품질

기존에는 재무 수치만 Claude에 입력해 "영업이익률이 X%이며 수익성이 양호합니다" 수준의 결과를 얻었습니다.

뉴스 본문이 추가된 이후에는 실제 투자 보고서에서 볼 수 있는 수준의 내용이 포함됩니다.

**예시 (LG이노텍)**

기존 출력:
> 이 기업의 영업이익률은 3.0%로 다소 낮은 수준이나 순이익은 양호합니다.

뉴스 반영 후 출력:
> 이 기업의 영업이익률은 3.0%로 산업 평균 대비 낮은 수준이지만, 반도체 기판(SiP) 품귀 현상과 북미 고객사 증산에 힘입어 올해 영업이익 1조 원 달성이 가시권에 들어왔습니다. SK증권은 현재가 대비 43% 상향된 목표주가 100만 원을 제시하며, 수주 20조 원 규모의 전장 사업 확대가 중기 성장을 이끌 것으로 전망했습니다.

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
- 경영 성과·평가·시사점 3개 카드로 구분된 AI 분석문
- 최신 뉴스 기사 카드 (제목·날짜·요약, 원문 링크 포함)

### AI 어시스턴트 질문 탭
- **RAG 모드**: TF-IDF 코사인 유사도로 관련 재무 청크 검색 후 Claude 답변 생성
- **Text2SQL 모드**: 자연어 질문 → SQL 자동 생성 → SQLite 직접 조회
- **자동 모드**: 질문 키워드로 RAG / Text2SQL 자동 선택

### PDF 리포트
- 재무 데이터 표
- Claude AI 분석문
- 최근 주요 뉴스 (제목·날짜·요약)
- 연도별 재무 요약 (RAG 기반)

---

## 시연 시나리오

### Case 1 — LG이노텍 (재무 + 뉴스 통합)

검색창에 `LG이노텍` 입력 후 분석 시작

실행 흐름:
1. Data Agent: DART에서 5개년 재무 데이터 수집 (두 번째 실행부터는 캐시 사용)
2. News Agent: 최신 뉴스 최대 10개 수집 → 기사 본문 크롤링 → AI 채점 → 상위 2개 선별
3. Analysis Agent: 재무 수치 + 뉴스 본문 통합 → Claude 분석문 생성
4. Report Agent: PDF 자동 생성 (뉴스 섹션 포함)

확인 항목:
- 사이드바에서 Data / News / Analysis / Report Agent 순서대로 활성화
- Claude 분석 탭에 뉴스 카드 2개 표시
- PDF에 "최근 주요 뉴스" 섹션 포함

### Case 2 — 삼성전자

검색창에 `삼성전자` 입력

확인 항목:
- 삼성전자 관련 실적·전망 뉴스 2개 선별
- 분석문에 HBM, 파운드리 등 최신 이슈 반영 여부

### Case 3 — 카카오

검색창에 `카카오` 입력

확인 항목:
- 카카오 관련 뉴스 2개 선별
- 뉴스 없어도 재무 분석이 정상 진행되는지 확인 (Graceful 처리)

### Case 4 — AI 질문 (RAG)

AI 질문 탭 → `2023년 수익성 평가는?`

확인 항목:
- 참조 데이터 최대 3건 + Claude 답변 출력
- 답변 수치가 참조 청크와 일치

### Case 5 — AI 질문 (Text2SQL)

AI 질문 탭 → `5년 평균 매출액은?`

확인 항목:
- `SELECT AVG(...) AS 평균_매출액` SQL 표시
- 조회 결과 행 + 단위(억원) 표시

### Case 6 — 오류 처리

검색창에 `asdfasdf` 입력

확인 항목:
- "데이터를 찾을 수 없습니다." 안내 메시지 출력
- 시스템 종료 없이 정상 유지

---

## 보안 규칙

- **API 키**: `.env` 파일에만 저장, 코드에 직접 입력 금지
- **모델 고정**: `claude_client.py`만 통해 호출, 모델은 `claude-haiku-4-5` 고정
- **SQL 안전장치**: SELECT 전용, DDL/DML 키워드 차단, 쿼리 체이닝 방지, LIMIT 자동 추가
- **CI 검증**: `.github/workflows/model-check.yml` — push마다 모델명 자동 검사
