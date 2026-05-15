import os
import sys
import sqlite3

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from claude_client import ask

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financials.db")


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


def answer(query: str, company: str) -> dict:
    """RAG: 유사 청크 검색 후 Claude 답변 생성"""
    results = search(query, company)
    if not results:
        return {
            "results": [],
            "answer": "재무 데이터가 없습니다. 먼저 기업 분석을 실행해주세요.",
        }

    context = "\n".join(r["text"] for r in results)
    prompt = (
        f"다음 재무 데이터를 참고하여 질문에 한국어로 답해줘.\n\n"
        f"[데이터]\n{context}\n\n"
        f"[질문] {query}\n\n"
        f"간결하고 명확하게 답해줘."
    )
    claude_answer = ask(prompt, max_tokens=400)
    return {"results": results, "answer": claude_answer}
