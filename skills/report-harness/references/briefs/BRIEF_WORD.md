# {대상} {단계} Word 보고서 : 원고 담당 브리프 (W1~Wn)

> 이 파일은 뼈대임. 사용자가 MD 토의본을 확인한 뒤 오케스트레이터가 `{ }` 를 채워 작업 폴더에 `BRIEF_WORD.md` 로 둠
> 원고 담당에게는 「`BRIEF_WORD.md` 를 처음부터 끝까지 읽고 그대로 따를 것. 담당은 W{n}」 한 줄만 줌
> 원고의 정본은 확인된 MD 토의본(`{MD 파일 이름}`)임. MD 에 없는 사실, 수치, 판정을 새로 넣지 않음

## 0. 맡는 것과 파일

| 담당 | 파일 | 담는 변수 | 장 |
|---|---|---|---|
| W1 | `content_front.py` | META, ES, QA (+ CLAIMS) | 표지, Executive Summary, 핵심 질문과 답변 |
| W2 | `content_ch1.py` | CHAPTERS, CLAIMS | {1장 제목} |
| W3 | `content_ch2.py` | CHAPTERS, CLAIMS | {2장 제목} |
| W{n} | `content_ch{n}.py` | CHAPTERS, DEVILS, CLOSING, REFERENCES, CLAIMS | {마지막 장}, 반론 점검, 맺음말, 참고 자료 |

- 모듈 첫 줄은 `from wb import *`. 헬퍼 : `P`, `FIG`, `TBL`, `BOX`, `QUOTE`, `NOTE`, `W`, `chapter`, `sec`, `claim` (`{스킬}/references/wb.py`)
- 형식 : `{스킬}/references/content-schema.md`. 예시 : `{스킬}/references/examples/content_ch1.py`
- DEVILS, CLOSING 은 한 모듈에만 둠. REFERENCES 는 여러 모듈에 나눠도 됨

## 1. 문체 (Word)

- analyst 합니다체 산문. 단락은 2~4문장, 350~600자 안팎
- 절마다 KEY MESSAGE 1~2문장(60~120자). 그 절 사실의 종합이고, 현황 단계에서는 판정을 넣지 않음
- bullet 없음. 가운뎃점(U+00B7)도 쓰지 않음(쉼표, 「와/과」 로 이음). 나열이 길면 표로 옮김
- 날짜는 「2026년 10월 12일」 형식(en : October 12, 2026). 2026-10-12, 2026.10.12 는 오류
- 출처는 문장 안 주어 앞에 둠 : 「가상의 B시 교통정보센터 2026년 2월 10일 자료에 따르면」
- 장과 장을 잇는 가리킴(「다음 장에서」 「앞 장에서」 「§」), 필자 자기 해설, 줄표, 작은따옴표를 쓰지 않음
- 한자, 가나는 한글로 쓰고 원문은 괄호 바로 안에만 둠 : 인공지능(人工知能)
- 금지어 사전 : `{스킬}/references/lexicon.json` (hype, eval_terms, ai_tone, pointer, self_commentary, user_banned)

## 2. 번호는 쓰지 않음

빌드가 붙임. 원고에 쓰면 번호가 둘이 되고 selfcheck `auto_number` 오류가 남.

| 빌드가 붙이는 것 | 원고에 쓰는 것 |
|---|---|
| `1. 이용 규모와 시간대` | `chapter("이용 규모와 시간대", ...)` |
| `1.1 연간 대여 건수와 등록 회원` | `sec("연간 대여 건수와 등록 회원", ...)` |
| `[표 1] 연도별 대여 건수` | `TBL("연도별 대여 건수", ...)` |
| `[그림 1] 시간대별 대여 비중` | `FIG("figs/fig1.png", "시간대별 대여 비중")` |
| `Q1.` `A.` | `{"q": "...", "a": "..."}` |
| `①` (ES 흐름, 반론 항목) | 라벨만 |

## 3. 표와 그림

- 표 : 열 5개 이하, 행 14개 이하, 셀 60자 이하, 폭은 `W(비율...)` 로(합 9026). 더 크면 표를 나눔
- 그림 : 그림 담당이 만든 PNG 만 씀(`figs/_DONE` 이 생긴 뒤). 경로는 `figs/파일이름.png`. 그림 안 숫자는 원고 숫자와 같아야 함
- 캡션 끝에 자료 성격을 괄호로 적음 : 「(2025년, 예시 자료)」. 출처는 `source=` 로

## 4. claims (원고와 함께 등록)

- 본문에 나온 수치는 모두 같은 모듈의 `CLAIMS` 에 등록함. 연도 단독과 12 이하 정수는 등록하지 않아도 됨. 소수, %, 12 를 넘는 수, 표준 번호는 등록함
- `claim(id, text, kind, value, source, url, status, method, note)`
  - id : 담당별 범위를 씀(W1 = C0xx, W2 = C1xx, W3 = C2xx ...). Z 로 시작하는 id 는 쓰지 않음(빌드 메타용)
  - value 나 text 에 그 수를 그대로 적음. 한 claim 에 여러 수 : `"412 / 3,150"`
  - status : `verified`(원문 확인), `estimate`(계산·외삽, 본문 그 수 앞뒤 30자 안에 「추정」), `removed`(검증 실패, 본문에 남기지 않음)
  - estimate 의 text 에는 추정값 말고 다른 수를 넣지 않음
- 「(계산)」 값은 식을 note 에 적음 : `"note": "1,284,300 ÷ 3,150 ÷ 365"`

## 5. 끝내기 전에 (전 항목 0)

```bash
cd {작업 폴더}
python3 {스킬}/references/selfcheck.py content_ch{n} --mode {status|analysis}
# 모듈 하나만 볼 때 ES, QA 의 수치가 다른 모듈에 등록돼 있으면 함께 넣어 점검함
python3 {스킬}/references/selfcheck.py content_front content_ch1 content_ch2 --mode {status|analysis}
```

- 마지막 줄이 `PASS` 일 때만 끝냄. `FIX n` 이면 `!!` 줄을 고치고 다시 돌림. `~~`(경고)는 고칠 수 있으면 고침
- 최종 메시지 : 모듈 경로, 장·절·표·그림 수, claims 수(verified, estimate, removed), selfcheck 마지막 줄, MD 와 다르게 쓴 곳(있으면 이유)
