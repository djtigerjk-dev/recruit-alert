"""
한화그룹 통합 채용 사이트 한화인(hanwhain.com).

화면 HTML이 아니라 내부 JSON API(hwadm.hanwhain.com)에서 목록을 받아온다.
계열사는 sdSeq 코드로 구분되며, search-sbsd API로 전체 매핑을 다시 확인할 수 있다
(README.md 참고). 같은 포탈을 쓰는 계열사는 sdSeq만 바꿔서 여러 개 등록하면 된다.
"""

from __future__ import annotations

import requests

from core import Posting

API_BASE = "https://hwadm.hanwhain.com/new-backend/portal/api/rcRecruit"
LIST_URL = f"{API_BASE}/search-rcrt"
DETAIL_URL = f"{API_BASE}/get-rcrt"
DETAIL_PAGE_URL = "https://www.hanwhain.com/portal/apply/recruit/detail?rtSeq={rt_seq}"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.hanwhain.com",
    "Referer": "https://www.hanwhain.com/portal/apply/recruit",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


class HanwhaSource:
    def __init__(self, sd_seq: int, display_name: str):
        self.sd_seq = sd_seq
        self.display_name = display_name
        self.key = f"hanwha:{sd_seq}"

    def fetch_postings(self) -> list[Posting]:
        postings: list[Posting] = []
        page = 0
        while True:
            body = {
                "langCd": "ko",
                "searchText": "",
                "sdSeqList": [self.sd_seq],
                "rtNrcrtYn": "",
                "rtCarrYn": "",
                "rtIntnYn": "",
                "rtPermanentWorkYn": "",
                "rtTempWorkYn": "",
                "djSeqList": None,
                "rjSeqList": None,
                "page": page,
                "size": 50,
            }
            resp = requests.post(LIST_URL, json=body, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            if not payload.get("success"):
                raise RuntimeError(f"목록 조회 실패: {payload}")

            data = payload["data"]
            for item in data["list"]:
                postings.append(
                    Posting(
                        id=str(item["rtSeq"]),
                        company=item["sdNm"],
                        title=item["rtNm"].strip(),
                        url=DETAIL_PAGE_URL.format(rt_seq=item["rtSeq"]),
                        start_dt=item["rtAcptStrtDttm"],
                        end_dt=item["rtAcptEndDttm"],
                    )
                )

            if not data.get("hasNext"):
                break
            page += 1

        return postings

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        """지원자격 / 근무지 같은 상세 정보를 텔레그램 메시지용 텍스트 줄로 만든다."""
        try:
            body = {"rtSeq": int(posting.id), "hidnKey": None, "langCd": "ko"}
            resp = requests.post(DETAIL_URL, json=body, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            if not payload.get("success"):
                return []
            item = payload["data"]["item"]
        except Exception:  # noqa: BLE001
            return []

        lines: list[str] = []
        quals = (item.get("rtExmQlf") or "").strip()
        if quals:
            if len(quals) > 400:
                quals = quals[:400] + "…"
            lines.append(f"✅ 지원자격\n{quals}")

        for unit in (item.get("unitDt") or [])[:3]:
            workpl = unit.get("ruWorkpl")
            if workpl:
                lines.append(f"📍 근무지({unit.get('ruNm', '')}): {workpl}")

        return lines
