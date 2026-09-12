# 한화 채용공고 감시 -> 텔레그램 알림

한화그룹 통합 채용 사이트 [한화인](https://www.hanwhain.com)은 화면 HTML이 아니라
내부 JSON API(`hwadm.hanwhain.com`)로 채용공고 목록을 받아온다. 이 스크립트는 그 API를
직접 호출해서, 지정한 계열사(기본값: **한화손해보험**)에 신규 공고가 올라오면 그 즉시
텔레그램으로 제목/접수기간/지원자격/URL을 알려준다.

HTML 구조를 긁는 방식이 아니라 사이트가 실제로 쓰는 API를 호출하기 때문에, 사이트
디자인이 바뀌어도(= HTML 클래스명이 바뀌어도) 잘 깨지지 않는다.

## 동작 방식

1. `search-rcrt` API에 계열사 코드(`sdSeq`)를 넣어 호출 → 현재 올라온 공고 목록(고유 ID `rtSeq` 포함)을 받는다.
2. 직전 실행 때 저장해 둔 `state.json`과 비교해서 새로 생긴 `rtSeq`를 찾는다.
3. 새 공고가 있으면 `get-rcrt` API로 상세 내용(지원자격, 근무지 등)을 가져와 텔레그램 메시지로 보낸다.
4. 이번에 확인한 `rtSeq` 전체를 `state.json`에 다시 저장한다.

**첫 실행**에서는 이미 올라와 있던 공고를 전부 "신규"로 알리지 않는다. 기준선만 저장하고,
그 다음 실행부터 새로 올라오는 공고만 알린다.

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
```

Windows(PowerShell)에서:

```powershell
$env:TELEGRAM_BOT_TOKEN = "받은 봇 토큰"
$env:TELEGRAM_CHAT_ID = "받은 chat id"
python watch.py
```

첫 실행은 알림 없이 `state.json`만 채워진다. 강제로 신규 공고 알림을 테스트해보고 싶으면
`state.json`을 열어 아무 `rtSeq` 하나를 지운 뒤 다시 실행하면 된다.

## 3. GitHub Actions로 자동 실행 (깃허브 연동)

이 폴더를 GitHub 저장소에 올리면 `.github/workflows/watch.yml`이 **15분마다 자동 실행**되며,
새 공고를 텔레그램으로 보내고 `state.json`을 커밋해 다음 실행에서도 기억한다.

1. GitHub에 새 저장소를 만들고 이 폴더 내용을 push한다.
2. 저장소 **Settings → Secrets and variables → Actions**에서 Repository secret 2개를 등록한다.
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. **Actions** 탭에서 워크플로우가 스케줄대로 도는지 확인한다. 바로 테스트하고 싶으면
   `workflow_dispatch`로 수동 실행(Run workflow 버튼)도 가능하다.

> GitHub Actions의 `schedule` cron은 트래픽이 몰리면 몇 분 정도 밀릴 수 있다(공식적으로 보장된
> 정확한 주기가 아님). 더 촘촘한 주기가 필요하면 `cron` 값을 조절하거나, 항상 켜져 있는 서버/PC의
> 작업 스케줄러로 `python watch.py`를 주기 실행해도 된다.

## 4. 다른 계열사 추가하기

`watch.py` 상단의 `WATCHED_COMPANIES` 딕셔너리에 `"표시 이름": sdSeq` 를 추가하면 된다.
`sdSeq`는 한화인 사이트의 계열사 코드로, 현재 확인된 값은 다음과 같다:

| 계열사 | sdSeq |
|---|---|
| 한화손해보험 (한화손보) | 202 |
| 한화생명 | 201 |
| 한화솔루션/케미칼 | 197 |
| 한화솔루션/큐셀 | 198 |
| 한화에어로스페이스 | 365 |
| 한화시스템/방산 | 328 |
| 한화투자증권 | 208 |
| 한화자산운용 | 207 |
| (주)한화 건설부문 | 182 |

전체 목록이 필요하면 `search-sbsd` API를 한 번 호출해 `sdNm`/`sdSeq` 매핑을 다시 확인하면 된다.

```bash
curl -s -X POST https://hwadm.hanwhain.com/new-backend/portal/api/rcRecruit/search-sbsd \
  -H "Content-Type: application/json" \
  -H "Origin: https://www.hanwhain.com" \
  -H "Referer: https://www.hanwhain.com/portal/apply/recruit" \
  -d '{"langCd":"ko"}'
```
