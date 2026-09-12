"""
회사마다 채용 사이트 구조가 다 다르기 때문에, 회사별로 "어떻게 목록을 가져올지"는
sources/*.py 에서 각자 구현하고, watch.py는 공통 인터페이스(Source/Posting)만 보고
신규 여부 판단 + 텔레그램 알림을 처리한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Posting:
    id: str            # 이 소스 안에서 고유한 공고 ID (사이트의 게시글 번호 등)
    company: str        # 화면에 표시할 회사명
    title: str
    url: str
    start_dt: str = ""
    end_dt: str = ""
    detail_lines: list[str] = field(default_factory=list)  # 텔레그램 메시지에 추가로 넣을 줄들


class Source(Protocol):
    key: str             # state.json에 쓰이는 고유 키. 회사가 겹치지 않게 "사이트:식별자" 형태 권장
    display_name: str    # 로그에 찍을 이름

    def fetch_postings(self) -> list[Posting]:
        """현재 사이트에 올라와 있는 채용공고 전체 목록을 가져온다 (상세 조회 없이 가볍게)."""
        ...

    def fetch_detail_lines(self, posting: Posting) -> list[str]:
        """신규로 확인된 공고 하나에 대해서만 호출되는 상세 정보(지원자격/근무지 등).

        회사가 많아질수록 매 실행마다 모든 공고의 상세를 다 조회하면 비효율적이라,
        watch.py는 이 메서드를 "새로 발견된" 공고에 대해서만 호출한다.
        상세가 없거나 실패해도 빈 리스트를 반환하면 된다 (알림 자체는 계속 보내짐).
        """
        ...
