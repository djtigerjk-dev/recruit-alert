"""
삼성 통합 채용 사이트(samsungcareers.com).

관계사 필터를 걸면 /hr/list.data 에 폼 POST로 그 관계사 공고만 담은 HTML 조각을
돌려준다(별도 인증 불필요, Playwright 없이 requests만으로 충분). 개별 공고가
클릭하면 페이지 이동 없이 자바스크립트 모달로만 열려서 안정적인 개별 URL이 없어,
링크는 해당 관계사 채용 페이지로 건다.

계열사 코드는 https://www.samsungcareers.com/subsid/detail/{code} 형태로 확인된다
(예: 삼성화재=E21, 삼성생명=E11).
"""

from __future__ import annotations

import re

import requests

from core import Posting

LIST_URL = "https://www.samsungcareers.com/hr/list.data"
COMPANY_PAGE_URL = "https://www.samsungcareers.com/subsid/detail/{code}"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    "Referer": "https://www.samsungcareers.com/hr/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

_ITEM_RE = re.compile(
    r'data-value="(?P<id>[\d,]+)">\s*'
    r'<p class="company">\s*(?P<company>.*?)\s*</p>\s*'
    r'<h3 class="title">\s*(?P<title>.*?)\s*</h3>\s*'
    r'<p class="info">\s*<span>\s*(?P<work_type>.*?)\s*</span>\s*'
    r'<span class="period">\s*(?P<period>.*?)\s*</span>',
    re.DOTALL,
)


class SamsungSource:
    def __init__(self, company_code: str, display_name: str):
        self.company_code = company_code
        self.display_name = display_name
        self.key = f"samsung:{company_code}"
        self.company_url = COMPANY_PAGE_URL.format(code=company_code)

    def fetch_postings(self) -> list[Posting]:
        body = (
            "currentPageNo=1&intNo=0&strVal=&strTxt=&strKey="
            f"&strCompany={self.company_code}%2C{self.company_code}"
            "&strType=&strOrderBy=&strEntity="
        )
        resp = requests.post(LIST_URL, headers=HEADERS, data=body.encode(), timeout=15)
        resp.raise_for_status()

        postings: list[Posting] = []
        for m in _ITEM_RE.finditer(resp.text):
            postings.append(
                Posting(
                    id=m.group("id"),
                    company=m.group("company").strip(),
                    title=m.group("title").strip(),
                    url=self.company_url,
                    start_dt=m.group("period").strip(),
                )
            )
        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        return []
