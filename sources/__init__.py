"""
회사별 채용공고 소스 모음.

각 소스는 core.Source 인터페이스(고유 key, fetch_postings())를 구현한다.
새 회사를 추가할 때는:
  1) sources/ 밑에 그 회사(또는 그 회사가 쓰는 채용시스템)를 위한 모듈을 만들고
  2) 이 파일의 ALL_SOURCES 리스트에 인스턴스를 추가한다.
"""

from __future__ import annotations

from core import Source

from .dongyang import DongyangLifeSource
from .greetinghr_platform import GreetingHrSource
from .hanwha import HanwhaSource
from .kbfg import KbfgSource
from .kyobo import KyoboSource
from .meritzfire import MeritzFireSource
from .metlife import MetLifeSource
from .recruiter_platform import RecruiterPlatformSource
from .samsung import SamsungSource

ALL_SOURCES: list[Source] = [
    SamsungSource(company_code="E21", display_name="삼성화재"),
    SamsungSource(company_code="E11", display_name="삼성생명"),
    KbfgSource(affcom_code="KBINSURE", display_name="KB손해보험"),
    MeritzFireSource(),
    DongyangLifeSource(),
    MetLifeSource(),
    KyoboSource(),
    HanwhaSource(sd_seq=202, display_name="한화손해보험"),
    HanwhaSource(sd_seq=201, display_name="한화생명"),
    HanwhaSource(sd_seq=507, display_name="한화생명금융서비스"),
    RecruiterPlatformSource(
        key="recruiter:hi",
        display_name="현대해상",
        list_url="https://hi.recruiter.co.kr/career/recruit",
    ),
    RecruiterPlatformSource(
        key="recruiter:dbgroup:db손해보험",
        display_name="DB손해보험",
        list_url="https://dbgroup.recruiter.co.kr/career/home",
        title_prefix="[DB손해보험]",
    ),
    RecruiterPlatformSource(
        key="recruiter:lotteins",
        display_name="롯데손해보험",
        list_url="https://lotteins.recruiter.co.kr/career/main",
    ),
    RecruiterPlatformSource(
        key="recruiter:shinhan-life",
        display_name="신한라이프",
        list_url="https://shinhan-life.recruiter.co.kr/career/home",
    ),
    RecruiterPlatformSource(
        key="recruiter:taekwang:흥국생명",
        display_name="흥국생명",
        list_url="https://taekwang.recruiter.co.kr/career/recruit",
        title_prefix="[흥국생명]",
    ),
    RecruiterPlatformSource(
        key="recruiter:taekwang:흥국화재",
        display_name="흥국화재",
        list_url="https://taekwang.recruiter.co.kr/career/recruit",
        title_prefix="[흥국화재]",
    ),
    GreetingHrSource(
        key="greeting:linakorea",
        display_name="라이나생명",
        list_url="https://linakorea.career.greetinghr.com/ko/recrutingnow",
    ),
    GreetingHrSource(
        key="greeting:lina-insurance",
        display_name="라이나손해보험",
        list_url="https://lina-insurance.career.greetinghr.com/ko/guide",
    ),
    GreetingHrSource(
        key="greeting:axa",
        display_name="악사손해보험",
        list_url="https://axa.career.greetinghr.com/ko/home",
    ),
    GreetingHrSource(
        key="greeting:kakaopayins",
        display_name="카카오페이손해보험",
        list_url="https://career.kakaopayinscorp.co.kr/ko/apply",
    ),
]
