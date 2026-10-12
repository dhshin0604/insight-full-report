---
name: image-deck
description: |
  확정된 원고(MD)를 1920×1080 5-Zone 이미지 슬라이드 덱(image deck)으로 만들 때 사용하며, 수치 타일, 표, 가로 막대, 타임라인, 2×2, 계층, 비주얼 요약, 시사점 3축 표 컴포넌트로 PNG 를 렌더하고 자동 QA 를 거쳐 PDF, PPTX(쪽마다 그림 한 장), PNG zip 으로 묶음. 글자를 고칠 수 있는 편집용 PPTX 가 필요하면 이 스킬 대신 generate-full-report 를 씀.
---

# 이미지 덱 (image-deck)

> 결과물 : ① 쪽마다 PNG(1920×1080) ② `{이름}_slides.pdf`(13.333×7.5in) ③ `{이름}_slides.pptx`(16:9, 쪽마다 전면 그림 한 장, 편집용 아님) ④ `{이름}_PNG.zip`(안의 이름 `{이름}_NN.png`) ⑤ `qa_report.json`
> 순서 : 원고 확인 → 쪽 설계 → `spec.py` → `render_all`(자동 QA) → PNG 한 장씩 육안 확인 → `bundle` → 전달
> 경로 : `<SKILL_DIR>` = `${CLAUDE_SKILL_DIR}` (Claude Code, Cowork 는 실제 경로로 바꿔 보여 줌. 그대로 보이면 이 SKILL.md 가 있는 폴더). 코드는 `<SKILL_DIR>/references/`

| 파일 | 내용 |
|---|---|
| `references/deck_core.py` | 렌더러, 쪽 함수, 컴포넌트, 자동 QA, 팔레트 검사 |
| `references/bundle.py` | PNG → PDF / PPTX / zip |
| `references/components.md` | 컴포넌트 카탈로그(시그니처, 규칙, 예시) |
| `references/deck-rules.md` | 5-Zone 측정값, 문장 규칙, 색 의미, QA 점검표, 겪은 문제 |
| `references/profile.json` | 작성자 프로필 템플릿(값은 비어 있음) |
| `references/examples/demo_deck.py` | 가상 내용 15쪽 데모(모든 컴포넌트 사용, 묶기까지) |

## GATE 0 : 멈출 일

아래 중 하나라도 해당하면 멈추고 해당 절을 다시 읽음.

1. 편집 가능한 PPTX(글자를 고칠 수 있는 슬라이드)를 요청받음 → 이 스킬이 아님. `generate-full-report` 로 넘김
2. 숫자·이름·출처가 확정된 원고(MD)가 없음 → 원고부터 확정(사용자 확인)
3. 원고에 없는 숫자를 타일·막대·표에 넣으려 함 → 원고에 넣고 확인받은 뒤 씀
4. 5-Zone 쪽을 HTML 로 처음부터 짜려 함 → `deck_core.py` 의 쪽 함수와 컴포넌트를 씀
5. 프로필(`AUTHOR_KR`, `AUTHOR_EN`, `EMAIL`)이 비어 렌더가 종료코드 2 로 멈춤 → 사용자에게 묻고 작업 폴더 `./profile.json` 에 기록
6. `render_all` 오류가 남았는데 묶으려 함 → 오류 0 이 될 때까지 고침
7. PNG 를 열어 보지 않고 전달하려 함 → 한 장씩 Read 로 확인

## 1. 원칙

| 규칙 | 기준 | 확인 |
|---|---|---|
| 산문 금지 | 본문은 컴포넌트로만. 160자 넘는 글 덩어리 금지 | QA 경고 |
| 컴포넌트 다양성 | 한 섹션(파트) 안에 3종 이상 | QA 경고 |
| 표 연속 금지 | 표만 있는 쪽 3장 연속 금지 | QA 경고 |
| 표 크기 | 8행 이하 | QA 경고 |
| 글자 크기 | 본문 안 19px 이상. `chart_img` 그림 안 글자도 19px 이상 | QA 오류(그림 안 글자는 육안 확인) |
| ☞ 정리 줄 | 본문 쪽 절반 이상에 한 줄 | QA 경고 |
| 헤드라인 | 명사형 종결 1~2문장, 90~130자, 2줄 이내, 숫자 2개 이상 | 3줄이면 QA 오류 |
| 색 의미 고정 | 관내(범위 안, 주 대상) #A31D1D, 관외(범위 밖, 비교 대상) #1A3A6B, 미확인 #8A8A8A, 핵심 변화 #C00000, 보조 #843C0C | 사람 확인 + 팔레트 검사 |
| 숫자 | 원고 값 그대로. 계산한 값은 `note()` 에 계산식 | 사람 확인 |
| 표기 | 날짜 `2026.10.12`, 줄표(U+2014) 금지 | QA 경고 |

문장 규칙과 측정값은 `references/deck-rules.md` 1~4절.

## 2. 절차

### 2-1. 원고 확인
- 원고 MD 에서 숫자, 고유 이름, 출처, 날짜를 확정본으로 씀. 덱에서 새 숫자를 만들지 않음
- 프로필 확인 : `python3 <SKILL_DIR>/references/deck_core.py --which-profile` (찾는 순서 : 환경변수 `PROFILE` → 작업 폴더 `./profile.json` → `<SKILL_DIR>/references/profile.json` → `<SKILL_DIR>/../generate-full-report/references/profile.json`)

### 2-2. 쪽 설계 (코드 전에 표로)

| 쪽 | 종류 | 섹션 | 헤드라인 요지 | 컴포넌트 | 출처 |
|---|---|---|---|---|---|
| 1 | cover | | | | |
| 2 | agenda | | | | |
| 3 | content | 1. 현황 | 무엇이 어디에 몇 개 | stats + cards + callout | 원고 §1 |

- 표지 → 목차 → (간지 → 세부 목차 → 본문 쪽들) × 파트 → 비주얼 요약 → 시사점 → 감사 순이 기본
- 내용 유형별 컴포넌트는 `references/components.md` 1절 표를 따름

### 2-3. spec.py

```python
# spec.py : 작업 폴더에 둠. IMAGE_DECK_REF = <SKILL_DIR>/references
import os, sys
REF = os.environ.get("IMAGE_DECK_REF") or (sys.argv[1] if len(sys.argv) > 1 else "")
if not os.path.isfile(os.path.join(REF, "deck_core.py")):
    sys.exit("IMAGE_DECK_REF 에 image-deck 의 references 폴더 경로를 넣음")
sys.path.insert(0, REF)
from deck_core import *
from bundle import bundle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
pages = [
    cover_html("가상의 A사<br>창고 자동화 전환", subtitle="물류센터 3곳의 현황과 시사점", date="2026.10.12"),
    agenda_html([("1부", "현황"), ("2부", "비교"), ("3부", "시사점")], no=2),
    slide_html(3, "1. 현황", "① 규모",
               "가상의 A사는 물류센터 3곳에서 하루 4만 2천 상자를 처리함. 자동화 비중은 18%에서 61%까지 벌어져 있음.",
               stats([("3곳", "물류센터"), ("4.2만", "하루 처리 상자"), ("18~61%", "자동화 비중", "", "navy")])
               + callout("차이는 설비 대수보다 일을 나누는 방식에서 생김"),
               source="가상의 A사 운영 자료(예시)"),
    thanks_html(no=4),
]
paths = render_all(pages, OUT)            # 오류가 있으면 paths.ok == False
if paths.ok:
    bundle(paths, "예시덱", OUT)           # PDF, PPTX, zip
```

- 큰 덱은 파트마다 `part_N.py` 가 쪽 HTML 목록을 돌려주게 나누고, 파트 담당은 `render_all(part_pages, "out_partN", prefix="p")` 로 따로 QA 한 뒤 `spec.py` 가 전체를 이어 다시 렌더함. 쪽 번호(`no`)는 최종 순서로 매김
- 모든 예시는 가상 내용. 실제 덱에서는 원고 값을 그대로 씀

### 2-4. 렌더와 자동 QA
- `python3 spec.py` → 콘솔 표(쪽, 종류, 섹션, 컴포넌트, 판정)와 `out/qa_report.json`
- 오류(!)는 모두 고침. 경고(?)는 읽고 고치거나 남길 이유를 적음. 고친 뒤 다시 렌더
- 끝까지 엄격하게 막으려면 `render_all(..., strict=True)` (오류가 있으면 종료코드 1)

### 2-5. 육안 확인
- PNG 를 한 장씩 Read 로 열어 겹침, 잘림, 넘침, 어색한 빈 공간, 숫자 오기를 봄
- 자동 QA 는 상자 모양의 겹침까지 다 잡지 못하므로 이 단계를 건너뛰지 않음

### 2-6. 묶기
- 파이썬 : `bundle(paths, "예시덱", OUT, formats=("pdf", "pptx", "zip"))`
- 명령행 : `python3 <SKILL_DIR>/references/bundle.py --in out/ --name 예시덱 --formats pdf,pptx,zip`
- `bundle` 이 PDF·PPTX·zip 의 쪽 수를 PNG 수와 대조하고 다르면 오류

### 2-7. 전달
- PDF, PPTX, PNG zip 을 사용자에게 전달. 사용자가 PNG 만 원하면 PNG 또는 zip 만
- 작업 공간이 초기화될 수 있으므로 `spec.py` 도 함께 전달해 두면 다시 만들 수 있음

## 3. 컴포넌트 요약

| 함수 | 쓰임 | 핵심 인자 |
|---|---|---|
| `stats` | 수치 타일 3~5개 | (값, 라벨, 보조, color_key) |
| `cards` | 항목별 특징 | (제목, [줄] 또는 HTML, color_key), cols |
| `mini_table` | 속성 비교 8행 이하 | headers, rows, widths, num_cols, em_rows, row_height |
| `hbars` | 수량 비교 | (라벨, 값[, color_key[, 표시 글]]), unit, max_value, height |
| `timeline` | 연대기 2~8개 | (날짜, 제목, 설명[, 강조]), phases |
| `quadrant` | 2축 포지셔닝 | x_label, y_label, (이름, x, y[, 색[, 위치]]), 칸 이름 4개 |
| `layers` | 계층·생태계 | (층 이름, [요소], color_key[, 메모]), height |
| `flow` | 단계·절차 | (제목, 설명), active |
| `chip` | 관내·관외·미확인 꼬리표 | kind = red · navy · grey · hollow · key · aux |
| `callout` / `note` | ☞ 정리 줄 / 회색 단서 | 문자열 |
| `chart_img` | 외부 그림 | 경로, height, caption |
| `two_panel` / `fill` / `panel_title` | 배치 | ratio, gap, align |

시그니처, 규칙, 예시 코드는 `references/components.md`.

## 4. 비주얼 요약 · 시사점 쪽

### 비주얼 요약 (`visual_summary_html`, kind="visual")
- 쓰임 : 장이나 덱의 끝에서 「무엇이 무엇으로 바뀌는가」를 한 장으로 보여 줌
- 구성 : 대형 제목(빨강) → 왼쪽 As-Is / 오른쪽 To-Be 도해(flow · list · hub) → 판정 한 줄 `A < B` → 열마다 설명 3줄 이하 → 전폭 결론 띠(빨강 바탕, 흰 글씨)
- 제목은 이동을 이름으로 잡음 : 「자동화의 기준 : 「설비 대수」에서 「흐름 관리」로」
- 판정은 짧은 명사 둘과 부호 : `("설비 대수", "<", "흐름 관리")`
- 결론 띠만 「~합니다」 존댓말을 씀. 헤드라인 문단·Source 줄·☞ 줄 없음
- 색 : As-Is 와 기존 요소 회색, To-Be 와 핵심 변화 빨강 #C00000(`"key"`), 보조 강조 적갈색 #843C0C(`"aux"`)

### 시사점 3축 표 (`implication_html`, kind="implication")
- 제목 「N. {주제} 시사점」 빨강 굵게, 오른쪽 라벨 「① 개요」 회색
- 헤드라인 검정 2문장 : 1문장은 비교 대상을 밝힘(「~는 ~와 다르게 ~임」), 2문장은 관리 기준이 「A」에서 「B」로 옮겨 감을 씀
- 열 제목 「관점」 / 「{주제}로 바뀔 때 함께 오는 변화」 / 「요구 사항」(`col_titles` 로 바꿈)
- 행 3개. 가운데·오른쪽 칸 모두 굵은 리드를 「A → B」 이동으로 씀. 불릿 2개 이하(1단 ●, 2단 ○, 적갈색)
- 하단 ☞ 줄·※ 단서 줄·Source 줄 없음

예시 코드는 `references/components.md` 4절, 실제 모양은 데모 13·14쪽.

## 5. QA · 팔레트

- `render_all` 이 쪽마다 검사 : 본문·도해 넘침, 헤드라인 3줄, 출처 3줄, 이미지 로드 실패, 19px 미만 글자, 쪽 밖 글자, 출처·본문 겹침, 프로필 플레이스홀더 잔존(이상 오류) / 글자 자동 축소, 사분면 이름 겹침, 표 9행 이상, 빈 공간, 줄표, 하이픈 날짜, 금지어(이상 경고)
- 덱 전체 검사 : 표만 3장 연속, 섹션 컴포넌트 3종 미만, ☞ 쪽 절반 미만, 한글 글꼴 없음(경고), 팔레트 대비 미달(오류)
- 팔레트 : `python3 <SKILL_DIR>/references/deck_core.py --palette [--theme 덮어쓸.json]` → WCAG 대비(24px 미만 4.5, 24px 이상 굵게 3.0), 의미색 ΔE 20, 적록색약 모사 ΔE 10
- 색을 바꿀 때 : `make_theme({"inside": "#9C1C1C"})` 뒤 같은 검사가 렌더 시작 때 자동으로 돎
- 금지어 : 형제 스킬의 `lexicon.json` 을 찾으면 경고로 알림. 현황 덱은 `render_all(..., mode="status")` 로 평가어까지 경고
- 기준과 판정 수준 전체는 `references/deck-rules.md` 5~7절

## 6. 환경 준비

| 항목 | 명령·조건 |
|---|---|
| Python | 3.9 이상 |
| 패키지 | `python3 -m pip install playwright img2pdf python-pptx Pillow` |
| 브라우저 | `python3 -m playwright install chromium` (Linux 에서 라이브러리 부족 오류가 나면 `python3 -m playwright install --with-deps chromium`) |
| 한글 글꼴 | 글꼴 스택 : Noto Sans CJK KR → Noto Sans KR → NanumGothic → Malgun Gothic → Apple SD Gothic Neo. Linux 는 `fonts-noto-cjk` 등 설치, Windows·macOS 는 기본 글꼴로 동작 |
| 프로필 | 작업 폴더 `profile.json` 에 `AUTHOR_KR`, `AUTHOR_EN`, `EMAIL`(필수), `PHONE_KR`(비면 감사 쪽에서 생략), `BRAND`(표지 라벨, 기본 Insight Report) |
| 시험 | `python3 <SKILL_DIR>/references/examples/demo_deck.py --out <빈 폴더> --example-profile` → QA 오류 0, PDF·PPTX·zip 15쪽 |

- 패키지가 없으면 쓰는 시점에 설치 안내를 출력하고 종료코드 3. 프로필이 비면 종료코드 2. strict 모드 QA 오류는 종료코드 1
- zip 묶기는 표준 라이브러리만으로 동작함

## 7. 겪은 문제와 대응

| 문제 | 대응 |
|---|---|
| 한글이 네모로 나옴 | 한글 글꼴 설치. QA 머리줄 「글꼴」 항목으로 확인 |
| 출처가 2줄이 되며 본문과 겹침 | 렌더가 본문 높이를 자동으로 줄임. 그래도 넘치면 본문 내용을 줄임 |
| 사분면 점 이름 겹침 | 자동 재배치. 경고가 남으면 이름을 줄이거나 높이를 키움 |
| 도해 상자 글자 넘침 | 19px 까지 자동 축소 + 경고. 오류가 나면 글을 줄임 |
| 쪽 아래가 비어 보임 | `fill()`, `mini_table(row_height=)`, `hbars(height=)`, `layers(height=)` |
| 예전 PNG 가 섞여 묶임 | `render_all` 이 같은 접두어의 예전 파일을 지우고 다시 씀 |
| 작업 공간 초기화로 파일 사라짐 | 단계마다 PNG 묶음과 `spec.py` 를 전달해 둠 |

전체 목록은 `references/deck-rules.md` 8절.

## 최종 점검표

- [ ] 원고(MD)의 숫자·이름·출처만 썼음
- [ ] 쪽 설계 표를 먼저 만들었음
- [ ] `render_all` 오류 0, 경고는 모두 읽고 처리했음
- [ ] PNG 를 한 장씩 열어 보았음(겹침, 잘림, 넘침, 빈 공간)
- [ ] 섹션마다 컴포넌트 3종 이상, 표만 3장 연속 없음, ☞ 줄이 본문 쪽 절반 이상
- [ ] 비주얼 요약·시사점 쪽에 헤드라인 문단(비주얼 요약), ☞ 줄, Source 줄이 없음
- [ ] 표지·감사 쪽 작성자 정보가 프로필과 같음
- [ ] PDF·PPTX·zip 쪽 수가 PNG 수와 같음
- [ ] 편집 가능한 PPTX 요청이었다면 generate-full-report 로 넘겼음
