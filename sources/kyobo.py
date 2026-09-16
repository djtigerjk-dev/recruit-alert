"""
교보생명 채용 사이트(career.kyobo.co.kr).

목록의 각 공고는 실제 URL이 아니라 `doAction('view','page',C_CD,RE_NO,NOTI_SEQ_NO,'',able_yn)`
로 숨은 폼을 POST 제출해서 상세를 연다(GET으로 열리는 개별 링크가 없음) - 메리츠화재/
삼성/동양생명과 같은 패턴이라, 링크는 목록 페이지로 건다. 공고 고유 ID로는 onclick 안의
RE_NO(두 번째 인자)를 쓴다.
"""

from __future__ import annotations

import re

from core import Posting

LIST_URL = "https://career.kyobo.co.kr/rem/apply/recruit/apply_list.jsp"

_RE_NO_RE = re.compile(r"doAction\('view',\s*'page',\s*'[^']*',\s*'([^']*)'")


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
                    "#listBodyall > li:not(.nodata) > a",
                    """
                    els => els.map(a => ({
                        onclick: a.getAttribute('onclick') || '',
                        title: (a.querySelector('.subject') || {}).innerText || '',
                        period: (a.querySelector('.period') || {}).innerText || '',
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

            m = _RE_NO_RE.search(item.get("onclick") or "")
            re_no = m.group(1) if m else title

            postings.append(
                Posting(
                    id=re_no,
                    company=self.display_name,
                    title=title,
                    url=LIST_URL,
                    start_dt=(item.get("period") or "").strip(),
                )
            )
        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        return []
