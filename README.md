# 보험사 채용공고 감시 -> 텔레그램 알림

여러 보험/금융사의 채용 사이트를 감시하다가 신규 공고가 올라오면 그 즉시 텔레그램으로
제목/기간/URL을 알려준다. 회사마다 채용 사이트 구조가 다 다르기 때문에, 가능한 경우
그 사이트가 실제로 쓰는 내부 API를 직접 호출하고, API를 찾기 어려운 곳은 Playwright로
실제 브라우저처럼 페이지를 렌더링해서 읽는다 — 단순 HTML 요청만으로는 안 되는(=예전에
"회사마다 잘 안 되던") 사이트가 대부분 이 두 방식 중 하나로 해결된다.

## 동작 방식

1. 회사별 어댑터(`sources/*.py`)가 각자의 방식으로 현재 목록을 가져온다.
2. 직전 실행 때 저장해 둔 `state.json`과 비교해서 새로 생긴 공고 ID를 찾는다.
3. 새 공고가 있으면 텔레그램 메시지로 보낸다 (실패하면 다음 실행에서 재시도).
4. 이번에 확인한 공고 ID를 `state.json`에 다시 저장한다.

**첫 실행**에서는 이미 올라와 있던 공고를 전부 "신규"로 알리지 않는다. 기준선만 저장하고,
그 다음 실행부터 새로 올라오는 공고만 알린다.

## 현재 감시 중인 회사 (20개)

| 회사 | 방식 | 비고 |
|---|---|---|
| 한화손해보험 / 한화생명 / 한화생명금융서비스 | 공식 JSON API (hanwhain.com) | 한화그룹 통합 포탈 |
| 삼성화재 / 삼성생명 | 공식 폼 API (samsungcareers.com) | 삼성 통합 포탈. 개별 링크가 없어 회사 채용 페이지로 연결 |
| KB손해보험 | 공식 JSON API (careers.kbfg.com) | KB금융그룹 통합 포탈 |
| 현대해상 | Playwright (recruiter.co.kr) | |
| DB손해보험 | Playwright (recruiter.co.kr) | DB그룹 통합 포탈, 제목 접두어로 필터링 |
| 롯데손해보험 | Playwright (recruiter.co.kr) | |
| 신한라이프 | Playwright (recruiter.co.kr) | |
| 흥국생명 / 흥국화재 | Playwright (recruiter.co.kr) | 태광그룹 통합 포탈, 제목 접두어로 필터링 |
| 라이나생명 / 라이나손해보험 | Playwright (그리팅 greetinghr.com) | |
| 악사손해보험 | Playwright (그리팅 greetinghr.com) | |
| 카카오페이손해보험 | Playwright (그리팅, 자체 도메인) | |
| 메리츠화재 | requests + BeautifulSoup (SSR HTML) | 개별 링크가 없어 목록 페이지로 연결 |
| 동양생명 | 공식 JSON API (myangel.co.kr) | 개별 링크가 없어 목록 페이지로 연결 |
| 메트라이프생명 | Playwright (metlifecareers.com) | 1페이지(최신)만 확인 |
| 교보생명 | Playwright (career.kyobo.co.kr) | ⚠️ 작성 시점에 진행 중 공고가 0건이라 실제 공고 발생 시 구조 재확인 필요 |

**처브손해보험 / 처브라이프생명보험**은 조사했지만 국내용 채용 사이트를 찾지 못해
아직 포함하지 않았다. 실제 URL을 알아내면 `sources/`에 같은 패턴으로 추가하면 된다.

## 1. 텔레그램 봇 준비

1. 텔레그램에서 [@BotFather](https://t.me/BotFather)와 대화를 시작해 `/newbot`으로 봇을 만들고
   **봇 토큰**(`123456:ABC-DEF...` 형태)을 받는다.
2. 알림을 받을 대화(개인 DM이든, 봇을 초대한 그룹이든)에서 아무 메시지나 하나 보낸다.
3. 아래 주소를 브라우저로 열어 `chat.id` 값을 확인한다 (그룹이면 보통 `-`로 시작하는 음수).

   ```
   https://api.telegram.org/bot<봇토큰>/getUpdates
   ```

## 2. 로컬에서 테스트

```bash
cd hanwha-recruit-alert
pip install -r requirements.txt
python -m playwright install chromium
```

Windows(PowerShell)에서:

```powershell
$env:TELEGRAM_BOT_TOKEN = "받은 봇 토큰"
$env:TELEGRAM_CHAT_ID = "받은 chat id"
python watch.py
```

첫 실행은 알림 없이 `state.json`만 채워진다(회사가 20개라 1~2분 정도 걸린다).
강제로 신규 공고 알림을 테스트해보고 싶으면 `state.json`을 열어 특정 회사 키의 값
하나를 지운 뒤 다시 실행하면 된다.

## 3. GitHub Actions로 자동 실행 (깃허브 연동)

이 폴더를 GitHub 저장소에 올리면 `.github/workflows/watch.yml`이 **30분마다 자동 실행**되며,
새 공고를 텔레그램으로 보내고 `state.json`을 커밋해 다음 실행에서도 기억한다.

1. GitHub에 새 저장소를 만들고 이 폴더 내용을 push한다.
2. 저장소 **Settings → Secrets and variables → Actions**에서 Repository secret 2개를 등록한다.
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. **Actions** 탭에서 워크플로우가 스케줄대로 도는지 확인한다. 바로 테스트하고 싶으면
   `workflow_dispatch`로 수동 실행(Run workflow 버튼)도 가능하다.

> **실행 시간 / 사용량 참고**: 회사 절반 이상이 Playwright로 브라우저를 띄워 페이지를
> 읽기 때문에 1회 실행에 1~2분 정도 걸린다. GitHub Actions는 **public 저장소는 무제한**,
> **private 저장소는 월 2000분 무료**다. 30분 간격이면 한 달에 대략 40~90시간 정도
> 사용량이 나올 수 있어 private로 오래 돌릴 계획이면 저장소를 public으로 전환하거나
> (state.json에 개인정보가 없으니 공개해도 무방), cron 간격을 늘리는 것을 권장한다.

## 4. 회사 추가/수정하기

`sources/__init__.py`의 `ALL_SOURCES` 리스트에 항목을 추가하면 된다. 이미 만들어진
공용 어댑터가 있으니, 새 회사가 아래 플랫폼 중 하나를 쓴다면 설정만 추가하면 된다:

- **한화인(hanwhain.com) 포탈 계열사** -> `HanwhaSource(sd_seq=..., display_name=...)`
  (sd_seq 값은 `sources/hanwha.py` 주석의 `search-sbsd` API로 확인)
- **recruiter.co.kr 플랫폼** -> `RecruiterPlatformSource(key=..., display_name=..., list_url=...)`
  (그룹 통합 포탈이면 `title_prefix="[회사명]"` 추가)
- **그리팅(greetinghr.com) 플랫폼** -> `GreetingHrSource(key=..., display_name=..., list_url=...)`

완전히 새로운 사이트라면 `sources/` 밑에 새 모듈을 만들어 `core.Source` 인터페이스
(`key`, `display_name`, `fetch_postings()`, `fetch_detail_lines()`)를 구현하면 된다.
이미 만들어진 어댑터들(`samsung.py`, `kbfg.py`, `meritzfire.py`, `dongyang.py` 등)이
"공식 API 찾기 -> 안 되면 Playwright로 렌더링" 순서로 시도한 예시라 참고하기 좋다.
