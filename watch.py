"""
여러 회사의 채용 사이트를 감시하다가 신규 공고가 올라오면 텔레그램으로 알린다.

회사마다 사이트 구조가 다 다르기 때문에, "그 회사 목록을 어떻게 가져올지"는
sources/*.py 에 회사(또는 그 회사가 쓰는 채용시스템)별로 따로 구현되어 있고,
이 파일은 그 결과(core.Posting)만 보고 신규 여부 판단 + 텔레그램 전송을 담당한다.

새 회사를 추가하는 방법은 README.md 참고.

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
from pathlib import Path

import requests

from core import Posting
from sources import ALL_SOURCES

STATE_PATH = Path(__file__).parent / "state.json"


def load_seen_state() -> dict[str, list[str]]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_seen_state(state: dict[str, list[str]]) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build_message(posting: Posting, detail_lines: list[str]) -> str:
    lines = [
        f"🆕 신규 채용공고 - {posting.company}",
        "",
        f"📌 {posting.title}",
    ]
    if posting.start_dt or posting.end_dt:
        lines.append(f"🗓 접수기간: {posting.start_dt} ~ {posting.end_dt}")

    for extra in detail_lines:
        lines.append("")
        lines.append(extra)

    lines.append("")
    lines.append(f"🔗 {posting.url}")
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

    for source in ALL_SOURCES:
        seen_ids = set(state.get(source.key, []))

        try:
            postings = source.fetch_postings()
        except Exception as exc:  # noqa: BLE001
            print(f"[{source.display_name}] 목록 조회 중 오류: {exc}", file=sys.stderr)
            had_error = True
            continue

        by_id = {p.id: p for p in postings}
        current_ids = set(by_id)
        new_ids = current_ids - seen_ids
        notified_ids: set[str] = set()

        if is_first_run:
            # 첫 실행에서는 기존 공고를 전부 "신규"로 알리지 않고 기준선만 저장한다.
            print(f"[{source.display_name}] 첫 실행: 기존 공고 {len(current_ids)}건을 기준으로 저장합니다.")
            notified_ids = new_ids
        elif new_ids:
            print(f"[{source.display_name}] 신규 공고 {len(new_ids)}건 발견")
            for posting_id in new_ids:
                posting = by_id[posting_id]
                try:
                    detail_lines = source.fetch_detail_lines(posting)
                except Exception as exc:  # noqa: BLE001
                    print(f"  상세 조회 실패(id={posting_id}): {exc}", file=sys.stderr)
                    detail_lines = []

                message = build_message(posting, detail_lines)
                try:
                    send_telegram_message(message)
                    notified_ids.add(posting_id)
                    time.sleep(1)  # 텔레그램 rate limit 여유
                except Exception as exc:  # noqa: BLE001
                    print(f"  텔레그램 전송 실패(id={posting_id}): {exc}", file=sys.stderr)
                    had_error = True
                    # 이 공고는 seen_ids에 넣지 않아 다음 실행에서 다시 시도한다.
        else:
            print(f"[{source.display_name}] 신규 공고 없음 (현재 {len(current_ids)}건)")

        # 알림을 못 보낸 신규 공고는 다음 실행에서 재시도하도록 seen 처리에서 제외한다.
        updated_seen = seen_ids | notified_ids | (current_ids - new_ids)
        if updated_seen != seen_ids:
            state[source.key] = sorted(updated_seen)
            state_changed = True

    if state_changed:
        save_seen_state(state)

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
