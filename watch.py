"""
한화인(hanwhain.com) 채용공고 신규 등록 감시 -> 텔레그램 알림

한화그룹 통합 채용 사이트인 한화인은 화면에 보이는 HTML이 아니라
내부 JSON API(hwadm.hanwhain.com)에서 채용공고 목록을 받아와 그린다.
그 API를 그대로 호출해서 계열사(예: 한화손보)별 신규 공고를 감지한다.

사용법:
    python watch.py

환경변수:
    TELEGRAM_BOT_TOKEN  - 텔레그램 봇 토큰 (필수)
    TELEGRAM_CHAT_ID    - 알림 받을 채팅 ID (필수)
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import requests

# 감시할 한화 계열사. sdSeq는 www.hanwhain.com 이 내부적으로 쓰는 계열사 코드.
# (search-sbsd API 응답에서 확인함: "한화손보" -> 202)
# 다른 계열사를 추가하고 싶으면 이 dict에 "표시할 이름": sdSeq 만 추가하면 된다.
WATCHED_COMPANIES: dict[str, int] = {
    "한화손해보험": 202,
}

API_BASE = "https://hwadm.hanwhain.com/new-backend/portal/api/rcRecruit"
LIST_URL = f"{API_BASE}/search-rcrt"
DETAIL_URL = f"{API_BASE}/get-rcrt"
DETAIL_PAGE_URL = "https://www.hanwhain.com/portal/apply/recruit/detail?rtSeq={rt_seq}"

STATE_PATH = Path(__file__).parent / "state.json"

COMMON_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.hanwhain.com",
    "Referer": "https://www.hanwhain.com/portal/apply/recruit",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


@dataclass
class JobPosting:
    rt_seq: int
    title: str
    company: str
    start_dt: str
    end_dt: str

    @property
    def url(self) -> str:
        return DETAIL_PAGE_URL.format(rt_seq=self.rt_seq)


def fetch_postings(sd_seq: int) -> list[JobPosting]:
    """지정한 계열사(sdSeq)의 채용공고 목록 전체를 가져온다."""
    postings: list[JobPosting] = []
    page = 0
    while True:
        body = {
            "langCd": "ko",
            "searchText": "",
            "sdSeqList": [sd_seq],
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
        resp = requests.post(LIST_URL, json=body, headers=COMMON_HEADERS, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success"):
            raise RuntimeError(f"목록 조회 실패: {payload}")

        data = payload["data"]
        for item in data["list"]:
            postings.append(
                JobPosting(
                    rt_seq=item["rtSeq"],
                    title=item["rtNm"].strip(),
                    company=item["sdNm"],
                    start_dt=item["rtAcptStrtDttm"],
                    end_dt=item["rtAcptEndDttm"],
                )
            )

        if not data.get("hasNext"):
            break
        page += 1

    return postings


def fetch_detail(rt_seq: int) -> dict:
    """공고 상세 내용을 가져온다 (근무지, 자격요건 등)."""
    body = {"rtSeq": rt_seq, "hidnKey": None, "langCd": "ko"}
    resp = requests.post(DETAIL_URL, json=body, headers=COMMON_HEADERS, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"상세 조회 실패: {payload}")
    return payload["data"]["item"]


def load_seen_state() -> dict[str, list[int]]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_seen_state(state: dict[str, list[int]]) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build_message(posting: JobPosting, detail: dict) -> str:
    lines = [
        f"🆕 신규 채용공고 - {posting.company}",
        f"",
        f"📌 {posting.title}",
        f"🗓 접수기간: {posting.start_dt} ~ {posting.end_dt}",
    ]

    quals = (detail.get("rtExmQlf") or "").strip()
    if quals:
        if len(quals) > 400:
            quals = quals[:400] + "…"
        lines.append(f"\n✅ 지원자격\n{quals}")

    units = detail.get("unitDt") or []
    for unit in units[:3]:  # 직무가 많으면 앞의 몇 개만
        workpl = unit.get("ruWorkpl")
        if workpl:
            lines.append(f"\n📍 근무지({unit.get('ruNm', '')}): {workpl}")

    lines.append(f"\n🔗 {posting.url}")
    return "\n".join(lines)


def send_telegram_message(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 환경변수가 설정되어 있지 않습니다."
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"텔레그램 전송 실패: {resp.status_code} {resp.text}")


def main() -> int:
    state = load_seen_state()
    is_first_run = not state
    state_changed = False
    had_error = False

    for company_name, sd_seq in WATCHED_COMPANIES.items():
        key = str(sd_seq)
        seen_ids = set(state.get(key, []))

        try:
            postings = fetch_postings(sd_seq)
        except Exception as exc:  # noqa: BLE001
            print(f"[{company_name}] 목록 조회 중 오류: {exc}", file=sys.stderr)
            had_error = True
            continue

        current_ids = {p.rt_seq for p in postings}
        new_ids = current_ids - seen_ids
        notified_ids: set[int] = set()

        if is_first_run:
            # 첫 실행에서는 기존 공고를 전부 "신규"로 알리지 않고 기준선만 저장한다.
            print(f"[{company_name}] 첫 실행: 기존 공고 {len(current_ids)}건을 기준으로 저장합니다.")
            notified_ids = new_ids
        elif new_ids:
            print(f"[{company_name}] 신규 공고 {len(new_ids)}건 발견")
            for posting in postings:
                if posting.rt_seq not in new_ids:
                    continue
                try:
                    detail = fetch_detail(posting.rt_seq)
                    message = build_message(posting, detail)
                except Exception as exc:  # noqa: BLE001
                    print(f"  상세 조회 실패(rtSeq={posting.rt_seq}): {exc}", file=sys.stderr)
                    message = (
                        f"🆕 신규 채용공고 - {posting.company}\n\n"
                        f"📌 {posting.title}\n"
                        f"🗓 접수기간: {posting.start_dt} ~ {posting.end_dt}\n\n"
                        f"🔗 {posting.url}"
                    )
                try:
                    send_telegram_message(message)
                    notified_ids.add(posting.rt_seq)
                    time.sleep(1)  # 텔레그램 rate limit 여유
                except Exception as exc:  # noqa: BLE001
                    print(f"  텔레그램 전송 실패(rtSeq={posting.rt_seq}): {exc}", file=sys.stderr)
                    had_error = True
                    # 이 rtSeq는 seen_ids에 넣지 않아 다음 실행에서 다시 시도한다.
        else:
            print(f"[{company_name}] 신규 공고 없음 (현재 {len(current_ids)}건)")

        # 알림을 못 보낸 신규 공고는 다음 실행에서 재시도하도록 seen 처리에서 제외한다.
        updated_seen = seen_ids | notified_ids | (current_ids - new_ids)
        if updated_seen != seen_ids:
            state[key] = sorted(updated_seen)
            state_changed = True

    if state_changed:
        save_seen_state(state)

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
