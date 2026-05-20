# SDIC AI Team 3 - 기업 재무·뉴스 통합 분석 에이전트

**배포 URL**: https://sdic-ai-team3.streamlit.app/

DART 공시 재무 데이터와 최신 뉴스를 함께 수집하고, LangGraph 멀티 에이전트 파이프라인으로 AI 기업 분석 및 PDF 보고서를 자동 생성하는 Streamlit 웹 애플리케이션입니다.

단순히 숫자를 읽어주는 수준이 아니라, 최신 뉴스 기사 본문까지 Claude에 입력해 실제 투자 보고서에 가까운 분석을 만들고, 분석 이후에도 AI 애널리스트와 대화를 이어갈 수 있습니다.

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
| AI 파이프라인 | LangGraph (Supervisor 패턴, 멀티 에이전트) |
| LLM | Claude Haiku (`claude-haiku-4-5`) via Anthropic API |
| 재무 데이터 수집 | DART-FSS API (공시 재무제표) |
| 뉴스 수집 | Google News RSS + 네이버 뉴스 본문 크롤링 |
| 검색 (RAG) | TF-IDF + 코사인 유사도 (scikit-learn) |
| 통합 RAG | 재무 데이터 + 뉴스 데이터 동시 검색 (`search_all`) |
| 자연어 SQL | Text2SQL (Claude가 SQL 생성, SQLite 직접 조회) |
| 데이터 저장 | SQLite (`data/sdic.db`, 재무 + 뉴스 청크 테이블) |
| 시각화 | Plotly, Streamlit |
| PDF 생성 | fpdf2 + NanumGothic 한글 폰트 |
| UI | Streamlit (탭 UI, 채팅 UI) |

---

## 폴더 구조

```
sdic-ai-team3/
├── app.py                  # Streamlit UI (KPI 카드, 차트, 뉴스 카드, 채팅)
├── graph.py                # LangGraph 멀티 에이전트 파이프라인 정의
├── rag.py                  # TF-IDF RAG (재무 + 뉴스 통합 검색, 채팅 답변)
├── text2sql.py             # 자연어 → SQL 변환 + 안전 실행
├── data.py                 # DART-FSS API 수집 로직
├── db.py                   # SQLite CRUD (재무 + 뉴스 청크 테이블)
├── claude_client.py        # Claude API 래퍼 (모델 고정: claude-haiku-4-5)
├── report.py               # 보고서 유틸리티
├── agents/
│   ├── supervisor_agent.py # 파이프라인 시작 노드
│   ├── data_agent.py       # DART 수집 + DB 캐시 노드
│   ├── news_agent.py       # 뉴스 수집, 본문 크롤링, 관련성 필터링, RAG 저장
│   ├── analysis_agent.py   # 재무 + 뉴스 통합 Claude 분석 노드
│   ├── report_agent.py     # fpdf2 PDF 생성 노드 (뉴스 섹션 포함)
│   └── no_data_agent.py    # 데이터 없음 종료 노드
├── data/
│   └── sdic.db             # SQLite 데이터베이스 (재무, 뉴스 청크)
├── output/                 # 생성된 PDF 저장 경로
├── fonts/
│   └── NanumGothic.ttf     # 한글 PDF 폰트
├── .env                    # API 키 (git 제외)
└── requirements.txt
```

---

## 시스템 구조

에이전트 4개가 순서대로 실행됩니다. 각 에이전트는 자기 역할만 수행하며, 결과를 다음 에이전트에게 넘깁니다.

```
기업명 입력 (app.py)
  |
  v
Supervisor Agent      요청을 받아 파이프라인 시작
  |
  v
Data Agent            DART API에서 재무 데이터 수집 (DB 캐시 활용)
  |
  v
News Agent            뉴스 수집 -> 기사 본문 크롤링 -> AI 관련성 필터링 -> 상위 2개 선별
                      -> 선별된 뉴스를 SQLite news_chunks 테이블에 RAG 저장
  |
  |-- (재무 데이터 없음) --> No Data Agent : 안내 메시지 출력 후 종료
  |
  v
Analysis Agent        재무 수치 + 뉴스 본문을 Claude에 함께 입력 -> 통합 분석문 생성
  |
  v
Report Agent          PDF 자동 생성 (재무 표 + 분석 + 뉴스 + RAG 요약)
  |
  v
결과 출력 (app.py)
  |-- 재무 데이터 탭      KPI 카드, 재무 테이블, Plotly 차트, YoY 성장률
  |-- Claude 분석 탭      경영 성과, 평가, 시사점 카드 + 최근 뉴스 카드
  |-- AI 질문 탭          RAG 문서 검색 또는 Text2SQL 데이터 조회
  |
  v
AI 애널리스트 채팅 (탭 아래 섹션)
      분석 결과 + 재무 + 뉴스를 모두 참고해 추가 질문에 답변
      st.chat_input / st.chat_message 기반 대화형 UI
```

---

## 에이전트 역할

| 에이전트 | 하는 일 |
|---|---|
| Data Agent | 기업 재무 데이터(매출, 영업이익, 순이익)를 DART 공시에서 가져옵니다. 이전에 조회한 기업이면 DB에서 바로 불러옵니다. |
| News Agent | 기업명으로 최신 뉴스를 수집하고 기사 본문을 직접 읽어 투자 관련성이 높은 기사 2개를 추립니다. 선별된 뉴스는 RAG DB에도 저장됩니다. |
| Analysis Agent | 재무 수치와 뉴스 기사 내용을 함께 Claude에 전달해 통합 분석문을 작성합니다. |
| Report Agent | 재무 데이터, AI 분석, 주요 뉴스를 하나의 PDF 파일로 만들어 저장합니다. |

---

## RAG 검색 시스템

RAG(Retrieval-Augmented Generation)란 사용자 질문과 가장 관련 있는 데이터를 먼저 찾은 뒤, 그 데이터를 Claude에 전달해 답변을 생성하는 방식입니다. 원하는 내용을 정확히 찾아 답변하므로, 아무 맥락 없이 질문하는 것보다 훨씬 구체적인 답변이 나옵니다.

### 저장 구조

`data/sdic.db` 파일 하나에 두 종류의 데이터가 저장됩니다.

| 테이블 | 내용 |
|---|---|
| `financials` | 연도별 매출액, 영업이익, 순이익 |
| `news_chunks` | 선별된 뉴스 기사 (제목, 본문, 날짜, URL) |

### 검색 방식

| 함수 | 설명 |
|---|---|
| `search(query, company)` | 재무 데이터만 검색 (PDF 생성에 사용) |
| `search_news(query, company)` | 뉴스 데이터만 검색 |
| `search_all(query, company)` | 재무 + 뉴스 통합 검색 (AI 질문, AI 채팅에 사용) |

질문 하나에 재무 숫자와 뉴스 기사를 함께 검색해 Claude에 전달하므로, 단순 수치 질문뿐 아니라 "최근 AI 관련 이슈"처럼 뉴스 기반 질문도 답할 수 있습니다.

---

## AI 애널리스트 채팅

분석이 끝나면 탭 아래에 채팅 섹션이 나타납니다. 한 번 분석하고 끝나는 것이 아니라, 결과를 보며 궁금한 점을 바로 물어볼 수 있습니다.

### 동작 방식

1. 사용자가 질문을 입력합니다.
2. `search_all()`로 재무 데이터와 뉴스를 동시에 검색합니다.
3. 검색 결과와 최초 분석 요약을 Claude 컨텍스트로 전달합니다.
4. Claude가 세 가지 정보(최초 분석, 재무 데이터, 뉴스)를 참고해 답변을 생성합니다.

### 예시 질문

```
왜 영업이익률이 감소했어?
최근 AI 관련 뉴스만 요약해줘
반도체 업황이 어떤 영향을 주고 있어?
경쟁사와 비교하면 어때?
최근 수주 관련 뉴스 알려줘
```

### 기능 상세

- 채팅이 비어있을 때 예시 질문 힌트를 표시합니다.
- `st.session_state` 기반으로 대화 기록을 유지합니다.
- 다른 기업으로 분석을 새로 실행하면 대화 기록이 자동으로 초기화됩니다.
- "대화 초기화" 버튼으로 언제든 새 대화를 시작할 수 있습니다.

---

## 뉴스 수집 및 필터링

### 수집 과정

1. **뉴스 수집**: 기업명에 "실적 전망 수주" 키워드를 붙여 Google News RSS에서 최근 기사 최대 10개를 가져옵니다.

2. **기사 본문 크롤링**: 각 기사 제목으로 네이버 뉴스를 검색해 실제 기사 페이지를 찾고, 본문 텍스트를 읽습니다 (최대 400자). 제목만 사용하는 것이 아니라 실제 기사 내용을 활용합니다.

3. **AI 관련성 필터링**: 수집한 기사 전체를 Claude에 보내 투자 분석에 얼마나 유용한지 0~10점으로 채점합니다.

   높은 점수: 실적 발표, 수주 계약, 목표주가 변경, AI/반도체 모멘텀, 산업 전망

   낮은 점수 (제외): 행사 참가, 봉사활동, 홍보성 보도, 사건/사고

4. **Top-K 선별 + RAG 저장**: 점수 기준으로 상위 2개 기사를 선택합니다. 선별된 뉴스는 SQLite `news_chunks` 테이블에 저장되어 이후 AI 채팅에서도 검색됩니다.

### 활용처

선별된 뉴스 2개는 다음 세 곳에 반영됩니다.

- **Claude 분석 프롬프트**: 재무 수치와 기사 본문이 함께 입력되어 뉴스 팩트가 분석문에 반영됩니다.
- **Streamlit UI**: Claude 분석 탭 하단에 뉴스 카드 형태로 제목, 날짜, 요약이 표시됩니다.
- **PDF 보고서**: "최근 주요 뉴스" 섹션으로 포함됩니다.
- **AI 애널리스트 채팅**: RAG DB에 저장되어 이후 대화에서 검색 및 활용됩니다.

---

## 분석 품질 비교

기존에는 재무 수치만 Claude에 입력했습니다.

기존 출력:
> 이 기업의 영업이익률은 3.0%로 다소 낮은 수준이나 순이익은 양호합니다.

뉴스 본문이 추가된 이후 출력:
> 이 기업의 영업이익률은 3.0%로 산업 평균 대비 낮은 수준이지만, 반도체 기판(SiP) 품귀 현상과 북미 고객사 증산에 힘입어 올해 영업이익 1조 원 달성이 가시권에 들어왔습니다. SK증권은 현재가 대비 43% 상향된 목표주가 100만 원을 제시하며, 수주 20조 원 규모의 전장 사업 확대가 중기 성장을 이끌 것으로 전망했습니다.

재무 수치에 뉴스 팩트가 더해지면서 투자 보고서에 가까운 형태가 됩니다.

---

## 주요 기능

### 재무 데이터 탭

- 핵심 지표 KPI 카드 4장 (매출액, 영업이익, 순이익, 영업이익률, 전년 대비 증감률)
- 5개년 재무 현황 테이블
- 매출액 / 영업이익 / 순이익 추이 라인 차트
- 영업이익률 추이 라인 차트
- YoY 성장률 테이블

### Claude 분석 탭

- 경영 성과, 평가, 시사점 3개 카드로 구분된 AI 분석문
- 최신 뉴스 기사 카드 (제목, 날짜, 요약, 원문 링크)

### AI 질문 탭

- **RAG 모드**: TF-IDF 코사인 유사도로 재무 + 뉴스 통합 검색 후 Claude 답변 생성
- **Text2SQL 모드**: 자연어 질문을 SQL로 변환해 SQLite 직접 조회
- **자동 모드**: 질문 키워드를 보고 RAG / Text2SQL 자동 선택

### AI 애널리스트 채팅 (탭 아래 섹션)

- 분석 완료 후 자유롭게 추가 질문 가능
- 재무 데이터, 뉴스, 최초 분석 요약을 동시에 참고해 답변
- 대화 기록 유지 (session_state 기반)
- 기업 변경 시 자동 초기화

### PDF 리포트

- 재무 데이터 표
- Claude AI 분석문
- 최근 주요 뉴스 (제목, 날짜, 요약)
- 연도별 재무 요약 (RAG 기반)

---

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만듭니다.

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

## 시연 시나리오

### Case 1 - LG이노텍 (전체 파이프라인 확인)

검색창에 `LG이노텍` 입력 후 분석 시작

실행 흐름:
1. Data Agent: DART에서 5개년 재무 데이터 수집 (두 번째 실행부터는 캐시 사용)
2. News Agent: 최신 뉴스 최대 10개 수집 -> 기사 본문 크롤링 -> AI 채점 -> 상위 2개 선별 -> RAG 저장
3. Analysis Agent: 재무 수치 + 뉴스 본문 통합 -> Claude 분석문 생성
4. Report Agent: PDF 자동 생성 (뉴스 섹션 포함)

확인 항목:
- 사이드바에서 Data / News / Analysis / Report Agent 순서대로 활성화
- Claude 분석 탭에 뉴스 카드 2개 표시
- PDF에 "최근 주요 뉴스" 섹션 포함

### Case 2 - AI 애널리스트 채팅 확인

LG이노텍 분석 완료 후 탭 아래 채팅 섹션에서 질문

```
왜 영업이익률이 감소했어?
```

확인 항목:
- 재무 데이터와 뉴스 기사를 함께 참고한 답변 생성
- 대화 기록이 유지되는지 확인 (연속 질문 가능)

### Case 3 - 삼성전자

검색창에 `삼성전자` 입력

확인 항목:
- 삼성전자 관련 실적, 전망 뉴스 2개 선별
- 분석문에 HBM, 파운드리 등 최신 이슈 반영 여부

### Case 4 - AI 질문 (RAG)

AI 질문 탭에서 `2023년 수익성 평가는?` 입력

확인 항목:
- 참조 데이터 최대 3건 + Claude 답변 출력
- 답변 수치가 참조 청크와 일치

### Case 5 - AI 질문 (Text2SQL)

AI 질문 탭에서 `5년 평균 매출액은?` 입력

확인 항목:
- `SELECT AVG(...) AS 평균_매출액` SQL 표시
- 조회 결과 행 + 단위(억원) 표시

### Case 6 - Graceful 처리

검색창에 `asdfasdf` 입력

확인 항목:
- "데이터를 찾을 수 없습니다." 안내 메시지 출력
- 시스템 종료 없이 정상 유지

---

## 보안 규칙

- **API 키**: `.env` 파일에만 저장, 코드에 직접 입력 금지
- **모델 고정**: `claude_client.py`만 통해 호출, 모델은 `claude-haiku-4-5` 고정
- **SQL 안전장치**: SELECT 전용, DDL/DML 키워드 차단, 쿼리 체이닝 방지, LIMIT 자동 추가
- **CI 검증**: `.github/workflows/model-check.yml` - push마다 모델명 자동 검사
