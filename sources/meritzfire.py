"""
메리츠화재 채용 사이트(recruit.meritzfire.com).

목록이 서버에서 이미 렌더링된 HTML로 내려온다(SSR) -> requests + BeautifulSoup로 충분.
개별 공고는 GET으로 열리는 URL이 없고 `noticeView('ID')`가 숨은 폼을 POST 제출하는
방식이라 안정적인 딥링크가 없어서, 링크는 목록 페이지로 건다.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from core import Posting

LIST_URL = "https://recruit.meritzfire.com/new/job/noticeList.do"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

_ID_RE = re.compile(r"noticeView\('([^']+)'\)")


class MeritzFireSource:
    key = "meritzfire"
    display_name = "메리츠화재"

    def fetch_postings(self) -> list[Posting]:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        postings: list[Posting] = []
        for a in soup.select("li a[onclick^='noticeView']"):
            m = _ID_RE.search(a.get("onclick", ""))
            if not m:
                continue
            title_el = a.select_one(".jobList__content-tit")
            period_el = a.select_one(".jobList__content-info-period")
            if not title_el:
                continue

            postings.append(
                Posting(
                    id=m.group(1),
                    company=self.display_name,
                    title=title_el.get_text(strip=True),
                    url=LIST_URL,
                    start_dt=period_el.get_text(strip=True) if period_el else "",
                )
            )
        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        return []
