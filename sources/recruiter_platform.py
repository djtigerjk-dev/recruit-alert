"""
"recruiter.co.kr" 채용 플랫폼(리크루터) 공용 어댑터.

현대해상(hi.recruiter.co.kr), DB그룹(dbgroup.recruiter.co.kr) 등 여러 회사가 이
Next.js 기반 SaaS를 쓰는데, 목록 데이터가 클라이언트 JS가 별도 인증 토큰으로 호출하는
내부 API(api-recruiter.recruiter.co.kr)에서만 내려오고 초기 HTML(SSR)에는 없어서,
requests만으로는 목록을 가져올 수 없다. 그래서 실제 브라우저처럼 페이지를 렌더링하는
Playwright로 접근한다 — 이 방식은 사이트가 이후에 API 응답 포맷을 바꿔도, 화면에 보이는
구조(제목/기간/링크)만 유지되면 계속 동작한다.

한 회사 전용 사이트도 있고(현대해상), 그룹 계열사 공고를 한 페이지에 모아 보여주는
사이트도 있다(DB그룹). 후자는 title_prefix로 원하는 계열사만 걸러낸다.
"""

from __future__ import annotations

from core import Posting

_JOB_LINK_SELECTOR = 'a[href*="/career/jobs/"]'


class RecruiterPlatformSource:
    def __init__(
        self,
        key: str,
        display_name: str,
        list_url: str,
        title_prefix: str | None = None,
        max_pages: int = 10,
    ):
        self.key = key
        self.display_name = display_name
        self.list_url = list_url
        self.title_prefix = title_prefix
        self.max_pages = max_pages

    def fetch_postings(self) -> list[Posting]:
        # Playwright는 매 실행마다 새로 import/launch한다 (다른 소스가 필요 없으면
        # 무거운 브라우저 의존성을 안 건드리게 하기 위해 지연 import).
        from playwright.sync_api import sync_playwright

        _EXTRACT_JS = """
            els => els.map(e => ({
                href: e.href,
                // 제목 <p>와 그걸 감싸는 wrapper <div>가 둘 다 class에 "title"을
                // 포함해서, div 대신 반드시 p 태그를 짚어야 상태태그(접수중/마감)
                // 텍스트가 섞여 들어가지 않는다.
                title: (e.querySelector('p[class*=title]') || {}).innerText || '',
                dates: Array.from(e.querySelectorAll('[class*=date] p')).map(p => p.innerText)
            }))
        """

        raw_items: list[dict] = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            try:
                page.goto(self.list_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                raw_items.extend(page.eval_on_selector_all(_JOB_LINK_SELECTOR, _EXTRACT_JS))

                # 한 페이지에 다 안 들어가는 회사(그룹 통합 포탈 등)를 위해 숫자
                # 페이지네이션이 있으면 끝까지 눌러가며 모은다. 무한루프 방지로 상한을 둔다.
                for _ in range(self.max_pages - 1):
                    page_items = page.query_selector_all("ol[class*=Pagination] li")
                    if not page_items:
                        break
                    active_idx = next(
                        (i for i, el in enumerate(page_items) if "active" in (el.get_attribute("class") or "")),
                        None,
                    )
                    if active_idx is None or active_idx + 1 >= len(page_items):
                        break  # 마지막 페이지
                    page_items[active_idx + 1].click()
                    page.wait_for_timeout(1200)
                    raw_items.extend(page.eval_on_selector_all(_JOB_LINK_SELECTOR, _EXTRACT_JS))
            finally:
                browser.close()

        postings: list[Posting] = []
        seen_hrefs: set[str] = set()
        for item in raw_items:
            href = item["href"]
            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)

            title = (item.get("title") or "").strip()
            if not title:
                continue
            if self.title_prefix and not title.startswith(self.title_prefix):
                continue

            job_id = href.rstrip("/").rsplit("/", 1)[-1]
            dates = item.get("dates") or []
            date_text = " ".join(d.strip() for d in dates if d.strip())

            postings.append(
                Posting(
                    id=job_id,
                    company=self.display_name,
                    title=title,
                    url=href,
                    start_dt=date_text,
                )
            )

        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        # 상세 페이지도 Playwright 렌더링이 필요해 비용이 크다. 지금은 목록에 보이는
        # 제목/기간 정도로 충분하다고 보고 상세 조회는 생략한다.
        return []
