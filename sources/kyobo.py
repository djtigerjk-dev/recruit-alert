"""
교보생명 채용 사이트(career.kyobo.co.kr).

주의: 이 파일을 작성하는 시점에 교보생명은 진행 중인 공고가 0건이라("등록된 내용이
없습니다"), 실제 공고가 있을 때의 목록 HTML 구조를 직접 확인하지 못한 채 만들었다.
`#listBodyall` 안에 `.nodata`가 아닌 `<li>`가 생기면 그 안의 첫 번째 링크를 공고로
간주하는 방식으로 최대한 유연하게 짰지만, 실제 공고가 올라온 뒤 한 번은 확인이 필요하다.
"""

from __future__ import annotations

from core import Posting

LIST_URL = "https://career.kyobo.co.kr/rem/apply/recruit/apply_list.jsp"


class KyoboSource:
    key = "kyobo"
    display_name = "교보생명"

    def fetch_postings(self) -> list[Posting]:
        from playwright.sync_api import sync_playwright

        raw_items: list[dict] = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            try:
                page.goto(LIST_URL, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                raw_items = page.eval_on_selector_all(
                    "#listBodyall > li:not(.nodata)",
                    """
                    els => els.map(li => {
                        const a = li.querySelector('a');
                        return {
                            href: a ? a.href : '',
                            text: li.innerText.trim(),
                        };
                    })
                    """,
                )
            finally:
                browser.close()

        postings: list[Posting] = []
        for idx, item in enumerate(raw_items):
            text = (item.get("text") or "").strip()
            if not text:
                continue
            title = text.splitlines()[0].strip()
            href = item.get("href") or LIST_URL
            postings.append(
                Posting(
                    id=href if href != LIST_URL else f"kyobo-{idx}-{title}",
                    company=self.display_name,
                    title=title,
                    url=href,
                )
            )
        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        return []
