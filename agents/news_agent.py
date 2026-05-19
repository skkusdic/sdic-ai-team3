import sys
import os
import re
import json
import html
import urllib.parse
from email.utils import parsedate_to_datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_client import ask

try:
    import requests
    from bs4 import BeautifulSoup
    import feedparser
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    print(f"[news_agent] 필수 패키지 미설치({_e}) — 뉴스 수집 비활성화")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}
_MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def _parse_date(published_str: str) -> str:
    try:
        dt = parsedate_to_datetime(published_str)
        return dt.strftime("%Y.%m.%d")
    except Exception:
        return published_str or ""


def _fetch_naver_article_body(title: str) -> str:
    """
    제목으로 네이버 모바일 뉴스 검색 → 첫 번째 Naver News URL 획득
    → #dic_area 본문 크롤링 → 최대 400자 반환
    """
    try:
        query = urllib.parse.quote(title[:50])
        search_url = (
            f"https://m.search.naver.com/search.naver"
            f"?where=m_news&query={query}&start=1"
        )
        r = requests.get(search_url, headers=_MOBILE_HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")

        # 네이버 뉴스 직접 링크 우선, 없으면 외부 링크
        naver_links = [
            a["href"] for a in soup.find_all("a", href=True)
            if "n.news.naver.com/article" in a["href"]
               or "news.naver.com/article" in a["href"]
        ]
        if not naver_links:
            return ""

        article_url = naver_links[0]
        ar = requests.get(
            article_url,
            headers={**_HEADERS, "Referer": "https://news.naver.com"},
            timeout=8,
        )
        article_soup = BeautifulSoup(ar.text, "html.parser")

        # 네이버 뉴스 본문 셀렉터 (우선순위 순)
        for sel in ["#dic_area", "#articleBodyContents", ".go_trans._article_content"]:
            body_el = article_soup.select_one(sel)
            if body_el:
                text = body_el.get_text(separator=" ", strip=True)
                # 광고·사진설명 패턴 제거
                text = re.sub(r"\[.*?\]|\(.*?기자.*?\)|▶.*", "", text)
                text = re.sub(r"\s{2,}", " ", text).strip()
                return text[:400]

    except Exception as e:
        pass  # graceful — 본문 없어도 진행
    return ""


def _fetch_google_news(company: str, max_results: int = 10) -> list:
    """Google News RSS로 기업 관련 최신 뉴스 수집 후 Naver 본문 보강"""
    if not _AVAILABLE:
        return []

    query = f"{company} 실적 전망 수주"
    encoded = urllib.parse.quote(query)
    rss_url = (
        f"https://news.google.com/rss/search"
        f"?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
    )

    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            return []

        articles = []
        for entry in feed.entries[:max_results]:
            title_raw = entry.get("title", "").strip()
            if not title_raw:
                continue

            # 제목 끝 " - 언론사명" 제거
            title = re.sub(r"\s*-\s*[^-]{2,20}$", "", title_raw).strip()
            link = entry.get("link", "")
            published = _parse_date(entry.get("published", ""))
            source = entry.get("source", {}).get("title", "")

            # ① 네이버 기사 본문 크롤링 시도
            body = _fetch_naver_article_body(title)

            # ② 본문이 없으면 RSS summary 텍스트 사용 (fallback)
            if not body:
                raw_summary = entry.get("summary", "")
                body = html.unescape(re.sub(r"<[^>]+>", "", raw_summary)).strip()
                body = re.sub(r"\s{2,}.*$", "", body).strip()

            articles.append({
                "title": title,
                "body": body,                  # 실제 기사 본문 (최대 400자)
                "summary": body[:150],         # PDF·UI 표시용 요약 (150자)
                "url": link,
                "published": published,
                "source": source,
            })

        return articles

    except Exception as e:
        print(f"[news_agent] 뉴스 수집 오류: {e}")
        return []


def _score_and_filter(company: str, articles: list, top_k: int = 2) -> list:
    """Claude로 투자 관련성 점수를 매기고 상위 top_k 반환"""
    if not articles:
        return []

    articles_text = "\n\n".join(
        f"[{i + 1}] 제목: {a['title']}\n본문: {a['body']}"
        for i, a in enumerate(articles)
    )

    prompt = f"""다음은 {company}에 관한 뉴스 기사 목록입니다.
각 기사에 대해 투자 분석 관련성 점수를 0~10으로 매겨주세요.

높은 점수 기준:
- 실적, 매출, 영업이익, 순이익
- 성장성, 수주, 공급 계약
- AI/반도체 모멘텀, 신사업
- 투자 리스크, 산업 전망

낮은 점수 기준:
- 단순 행사, 봉사활동
- 일반 홍보성 기사
- 연예/사건성 기사

{articles_text}

반드시 아래 JSON 배열 형식으로만 응답하세요 (다른 텍스트 없이):
[{{"index": 1, "score": 8}}, {{"index": 2, "score": 3}}, ...]"""

    try:
        response = ask(prompt, max_tokens=400)
        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if not match:
            return articles[:top_k]

        scores = json.loads(match.group())
        scored = [
            (s["index"] - 1, s["score"])
            for s in scores
            if isinstance(s, dict) and "index" in s and "score" in s
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        result = []
        for idx, score in scored:
            if 0 <= idx < len(articles) and score >= 4:
                result.append(articles[idx])
            if len(result) >= top_k:
                break

        return result if result else articles[:top_k]

    except Exception as e:
        print(f"[news_agent] 관련성 필터링 오류: {e}")
        return articles[:top_k]


def run_news_agent(state: dict) -> dict:
    company = state.get("company", "")
    if not company:
        return {**state, "news": []}

    print(f"[news_agent] {company} 최신 뉴스 수집 시작")
    raw_articles = _fetch_google_news(company, max_results=10)

    if not raw_articles:
        print(f"[news_agent] 수집된 뉴스 없음 — 빈 목록으로 계속 진행")
        return {**state, "news": []}

    print(f"[news_agent] {len(raw_articles)}개 수집 → Claude 관련성 필터링")
    top_news = _score_and_filter(company, raw_articles, top_k=2)

    print(f"[news_agent] 최종 {len(top_news)}개 선정 완료")
    return {**state, "news": top_news}


if __name__ == "__main__":
    import json as _json
    sys.stdout.reconfigure(encoding="utf-8")
    for test_company in ["LG이노텍", "삼성전자", "카카오"]:
        print(f"\n=== {test_company} 뉴스 테스트 ===")
        result = run_news_agent({"company": test_company})
        for n in result.get("news", []):
            print(f"  [{n['published']}] {n['title']}")
            print(f"  본문: {n['body'][:120]}...")
            print()
