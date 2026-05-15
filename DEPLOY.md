# Streamlit Cloud 배포 가이드

## 배포 순서

### 1. GitHub push
```bash
git pull --rebase origin main
git add app.py rag.py text2sql.py requirements.txt .gitignore .streamlit/secrets.toml.example DEPLOY.md
git commit -m "week6: Streamlit Cloud 배포 준비"
git push origin main
```

### 2. Streamlit Cloud 연결
1. [share.streamlit.io](https://share.streamlit.io) 접속 후 GitHub 로그인
2. **New app** 클릭
3. Repository: `skkusdic/sdic-ai-team3`
4. Branch: `main`
5. Main file path: `app.py`
6. **Deploy!** 클릭

### 3. Secrets 등록 (필수)
배포 후 앱 설정에서 **Secrets** 탭을 열고 아래 내용 입력:

```toml
DART_API_KEY = "실제_DART_API_키"
ANTHROPIC_API_KEY = "실제_Anthropic_API_키"
```

> `.streamlit/secrets.toml.example` 파일을 참고하세요.
> 실제 `secrets.toml`은 절대 GitHub에 올리지 마세요.

### 4. 확인
- 공개 URL에서 기업명 입력 → 분석 시작
- AI 질문 탭에서 RAG·Text2SQL 동작 확인
- README.md에 공개 URL 기재 후 push

## 주의사항
- `data/` 폴더와 `.streamlit/secrets.toml`은 `.gitignore`에 등록됨 — GitHub에 절대 올라가지 않음
- `financials.db`도 `.gitignore` 처리됨 — Cloud에서는 첫 실행 시 DART API로 데이터 수집
- 폰트 파일(`fonts/NanumGothic.ttf`)이 필요한 경우 Cloud 환경용 폴백 처리 필요
