import os
import sys
import sqlite3

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from claude_client import ask
from db import DB_PATH, save_news_chunks, load_news_chunks


def _load_chunks(company: str) -> list:
    """SQLite 재무 데이터를 텍스트 청크 리스트로 변환"""
    if not os.path.exists(DB_PATH):
        return []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT year, 매출액, 영업이익, 순이익 FROM financials WHERE company=? ORDER BY year",
                (company,),
            ).fetchall()
    except Exception:
        return []

    chunks = []
    for year, rev, op, net in rows:
        rev = rev or 0
        op = op or 0
        net = net or 0
        margin = round(op / rev * 100, 1) if rev else 0
        text = (
            f"{company} {year}년 재무: "
            f"매출액 {rev:,}억원, 영업이익 {op:,}억원, 순이익 {net:,}억원, "
            f"영업이익률 {margin}%"
        )
        chunks.append({"year": int(year), "text": text})
    return chunks


def search(query: str, company: str, top_k: int = 3) -> list:
    """TF-IDF 코사인 유사도로 상위 top_k 청크 반환"""
    chunks = _load_chunks(company)
    if not chunks:
        return []

    texts = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(texts + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1])[0]

    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)[:top_k]
    return [{"score": round(float(s), 4), "year": c["year"], "text": c["text"]} for s, c in ranked]


def _load_news_chunks(company: str) -> list:
    """DB에서 뉴스 청크를 TF-IDF용 텍스트 리스트로 변환"""
    rows = load_news_chunks(company)
    chunks = []
    for row in rows:
        text = (
            f"{company} 뉴스 ({row['published']}): "
            f"{row['title']} | {(row['body'] or '')[:300]}"
        )
        chunks.append({"type": "news", "title": row["title"], "published": row["published"], "text": text})
    return chunks


def has_data(company: str) -> bool:
    """DB에 해당 기업 재무 RAG 청크가 존재하는지 확인"""
    return len(_load_chunks(company)) > 0


def has_news(company: str) -> bool:
    """DB에 해당 기업 뉴스 청크가 존재하는지 확인"""
    return len(_load_news_chunks(company)) > 0


def save_news_to_rag(company: str, news_list: list) -> None:
    """뉴스 목록을 news_chunks 테이블에 저장"""
    save_news_chunks(company, news_list)


def search_news(query: str, company: str, top_k: int = 3) -> list:
    """뉴스 청크만 대상으로 TF-IDF 코사인 유사도 검색"""
    chunks = _load_news_chunks(company)
    if not chunks:
        return []
    texts = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(texts + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1])[0]
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)[:top_k]
    return [{"score": round(float(s), 4), **c} for s, c in ranked]


def search_all(query: str, company: str, top_k: int = 3) -> list:
    """재무 + 뉴스 청크를 통합하여 TF-IDF 코사인 유사도 검색"""
    finance_chunks = _load_chunks(company)
    news_chunks = _load_news_chunks(company)
    all_chunks = finance_chunks + news_chunks
    if not all_chunks:
        return []
    texts = [c["text"] for c in all_chunks]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(texts + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1])[0]
    ranked = sorted(zip(scores, all_chunks), key=lambda x: x[0], reverse=True)[:top_k]
    return [{"score": round(float(s), 4), **c} for s, c in ranked]


def answer(query: str, company: str) -> dict:
    """RAG: 재무+뉴스 통합 검색 후 Claude 답변 생성"""
    results = search_all(query, company)
    if not results:
        return {
            "results": [],
            "answer": "재무 데이터가 없습니다. 먼저 기업 분석을 실행해주세요.",
        }

    finance_ctx = "\n".join(r["text"] for r in results if r.get("type") != "news")
    news_ctx = "\n".join(r["text"] for r in results if r.get("type") == "news")

    context_parts = []
    if finance_ctx:
        context_parts.append(f"[재무 데이터]\n{finance_ctx}")
    if news_ctx:
        context_parts.append(f"[최신 뉴스]\n{news_ctx}")
    context = "\n\n".join(context_parts) if context_parts else "\n".join(r["text"] for r in results)

    prompt = (
        f"다음 데이터를 참고하여 질문에 한국어로 답해줘.\n\n"
        f"[단위] 모든 금액 수치는 억원 단위이며, 비율은 % 단위입니다.\n\n"
        f"{context}\n\n"
        f"[질문] {query}\n\n"
        f"조건:\n"
        f"- 금액은 반드시 'X,XXX억원' 형식으로 표기\n"
        f"- 비율은 'X.X%' 형식으로 표기\n"
        f"- 간결하고 전문적인 한국어로 답할 것"
    )
    claude_answer = ask(prompt, max_tokens=400)
    return {"results": results, "answer": claude_answer}


def chat_answer(query: str, company: str, analysis: str = "", financials: dict = None) -> dict:
    """AI 애널리스트 채팅: 초기 분석 컨텍스트 + 재무/뉴스 통합 검색 기반 답변"""
    results = search_all(query, company, top_k=4)

    finance_ctx = "\n".join(r["text"] for r in results if r.get("type") != "news")
    news_ctx    = "\n".join(r["text"] for r in results if r.get("type") == "news")

    context_parts = []
    if finance_ctx:
        context_parts.append(f"[재무 데이터]\n{finance_ctx}")
    if news_ctx:
        context_parts.append(f"[최신 뉴스]\n{news_ctx}")
    rag_context = "\n\n".join(context_parts)

    analysis_summary = (analysis[:600] + "...") if len(analysis) > 600 else (analysis or "")

    prompt_parts = [
        f"당신은 {company}을(를) 전담하는 AI 재무 애널리스트입니다. "
        f"아래 정보를 근거로 질문에 한국어로 전문적으로 답해주세요.\n",
    ]
    if analysis_summary:
        prompt_parts.append(f"[기업 분석 요약]\n{analysis_summary}\n")
    if rag_context:
        prompt_parts.append(f"[검색된 관련 데이터]\n{rag_context}\n")
    prompt_parts.extend([
        f"[질문] {query}\n",
        "조건:\n- 금액은 'X,XXX억원' 형식\n- 비율은 'X.X%' 형식\n"
        "- 전문적이고 간결한 한국어\n- 데이터에 없는 내용은 솔직히 밝힐 것",
    ])

    answer_text = ask("\n".join(prompt_parts), max_tokens=600)
    return {"results": results, "answer": answer_text}
