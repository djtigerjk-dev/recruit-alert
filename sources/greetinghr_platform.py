"""
"그리팅(Greeting)" 채용 플랫폼(career.greetinghr.com) 공용 어댑터.

라이나생명/라이나손해보험/AXA손해보험 등 여러 회사가 이 SaaS를 쓴다.
공고 카드가 data-testid="공고_아이템" 으로 마크업되어 있어(그리팅 자체 설계 시스템),
회사마다 CSS 클래스 해시가 달라도 이 속성 기준으로 안정적으로 찾을 수 있다.

회사별로 채용 목록이 걸려 있는 페이지 경로가 다르다(/home, /guide, /recrutingnow 등)
-> list_url에 그 회사의 실제 채용 목록 페이지를 넣어주면 된다.
"""

from __future__ import annotations

from core import Posting


class GreetingHrSource:
    def __init__(self, key: str, display_name: str, list_url: str):
        self.key = key
        self.display_name = display_name
        self.list_url = list_url

    def fetch_postings(self) -> list[Posting]:
        from playwright.sync_api import sync_playwright

        raw_items: list[dict] = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            try:
                page.goto(self.list_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                raw_items = page.eval_on_selector_all(
                    'a[data-testid="공고_아이템"]',
                    """
                    els => els.map(e => ({
                        href: e.href,
                        title: (e.querySelector('[data-variant="title-01"]') || {}).innerText || ''
                    }))
                    """,
                )
            finally:
                browser.close()

        postings: list[Posting] = []
        for item in raw_items:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            href = item["href"]
            job_id = href.rstrip("/").rsplit("/", 1)[-1]
            postings.append(
                Posting(
                    id=job_id,
                    company=self.display_name,
                    title=title,
                    url=href,
                )
            )

        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        return []
