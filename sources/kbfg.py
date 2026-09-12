"""
KB금융그룹 통합 채용 사이트(careers.kbfg.com).

/api/career/recruites 가 인증 없이 열려 있는 JSON API라 requests만으로 충분하다.
계열사는 affcomCd로 구분되고(예: KB손해보험=KBINSURE), 개별 공고의 enggLink는
실제로는 각 계열사가 쓰는 그리팅(greetinghr.com) 채용 페이지를 직접 가리킨다.
"""

from __future__ import annotations

import requests

from core import Posting

LIST_URL = "https://careers.kbfg.com/api/career/recruites"

HEADERS = {
    "Accept": "application/json",
    "Referer": "https://careers.kbfg.com/apply/apply",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


class KbfgSource:
    def __init__(self, affcom_code: str, display_name: str):
        self.affcom_code = affcom_code
        self.display_name = display_name
        self.key = f"kbfg:{affcom_code}"

    def fetch_postings(self) -> list[Posting]:
        params = {
            "affcomNm": "",
            "enggCate": "",
            "enggTitl": "",
            "enggLink": "",
            "enggStdt": "",
            "enggEddt": "",
            "useYn": "",
            "pageSize": 200,
            "totalCount": 0,
        }
        resp = requests.get(LIST_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("resultCode") != 200:
            raise RuntimeError(f"목록 조회 실패: {payload}")

        postings: list[Posting] = []
        for item in payload["result"]["recruties"]:
            if item.get("affcomCd") != self.affcom_code:
                continue
            postings.append(
                Posting(
                    id=str(item["enggId"]),
                    company=item.get("affcomNm", self.display_name),
                    title=(item.get("enggTitl") or "").strip(),
                    url=item.get("enggLink") or "https://careers.kbfg.com/apply/apply",
                    start_dt=item.get("enggStdt", ""),
                    end_dt=item.get("enggEddt", ""),
                )
            )
        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        return []
