"""
메트라이프생명 채용(글로벌 채용 플랫폼 metlifecareers.com, 대한민국으로 필터링).

이 플랫폼은 목록 데이터가 클라이언트 렌더링이라 Playwright로 접근한다. 페이지네이션은
1페이지(최신순으로 가정, 기본 6건)만 본다 — 새 공고는 항상 1페이지에 먼저 나타나므로
신규 감지 목적에는 충분하다.
"""

from __future__ import annotations

from core import Posting

LIST_URL = "https://www.metlifecareers.com/ko_KR/ml/SearchJobs?12310=116497&listFilterMode=1"


class MetLifeSource:
    key = "metlife"
    display_name = "메트라이프생명"

    def fetch_postings(self) -> list[Posting]:
        from playwright.sync_api import sync_playwright

        raw_items: list[dict] = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            try:
                page.goto(LIST_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2500)
                raw_items = page.eval_on_selector_all(
                    'a[href*="/JobDetail/"]',
                    """
                    els => {
                        const seen = new Set();
                        const out = [];
                        for (const e of els) {
                            if (seen.has(e.href)) continue;
                            seen.add(e.href);
                            out.push({href: e.href, title: e.innerText.trim()});
                        }
                        return out;
                    }
                    """,
                )
            finally:
                browser.close()

        postings: list[Posting] = []
        for item in raw_items:
            title = item.get("title") or ""
            if not title or title == "지원하기":
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
