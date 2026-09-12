"""
동양생명(수호천사) 채용 사이트(myangel.co.kr).

/api/adpStbl/selectListAdpStbl 가 인증 없이 열려 있는 POST JSON API라
requests만으로 충분하다. 개별 공고 페이지 URL이 따로 없어(사이트 자체가 안내하는
링크는 제휴 채용 플랫폼인 myangel.saramin.co.kr뿐), 회사 채용공고 페이지로 링크한다.
"""

from __future__ import annotations

import requests

from core import Posting

LIST_URL = "https://www.myangel.co.kr/api/adpStbl/selectListAdpStbl"
LIST_PAGE_URL = "https://www.myangel.co.kr/Company/Recruit/CoAdpLst"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": LIST_PAGE_URL,
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


class DongyangLifeSource:
    key = "dongyang"
    display_name = "동양생명"

    def fetch_postings(self) -> list[Posting]:
        body = {
            "header": {
                "svcType": "PC",
                "sndTime": "",
                "befoScrnId": "",
                "userTmunIdnfVal": "",
                "tempSndData1": "",
                "tempSndData2": "",
                "csPk": "",
                "bizRstCod": "",
                "bizRstMsg": "",
                "ipAddr": "0.0.0.0",
            },
            "payload": {
                "inpAdpProgCode": "",
                "inpAdpSecd": "",
                "inqExsYn": "0",
                "totCnt": "",
                "pageNo": 1,
                "pageSize": 100,
            },
        }
        resp = requests.post(LIST_URL, json=body, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("header", {}).get("prcsRstCod") != "S":
            raise RuntimeError(f"목록 조회 실패: {payload}")

        postings: list[Posting] = []
        for item in payload["payload"].get("adpStblList", []):
            postings.append(
                Posting(
                    id=item["adpInfPk"],
                    company=self.display_name,
                    title=(item.get("adpInfTitl") or "").strip(),
                    url=LIST_PAGE_URL,
                    start_dt=item.get("adpRecpStrymd", ""),
                    end_dt=item.get("adpRecpNdymd", ""),
                )
            )
        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        return []
