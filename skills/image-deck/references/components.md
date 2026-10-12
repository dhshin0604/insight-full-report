# 컴포넌트 카탈로그 (image-deck)

> `deck_core.py` 의 함수 목록과 쓰는 법. 본문(.body)에 넣는 조각은 문자열로 이어 붙여 `slide_html(..., body=...)` 에 넘김
> 문자열 인자는 HTML 로 해석됨(`<b>`, `<br>` 사용 가능). 「<」「&」를 글자 그대로 쓰려면 `esc()` 로 감쌈
> 모든 예시는 가상 내용임

## 0. 불러오기

```python
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "<image-deck 스킬 폴더>", "references"))   # 설치 위치 기준 상대 경로
from deck_core import *          # 쪽 함수, 컴포넌트, render_all, load_profile, make_theme
from bundle import bundle
```

## 1. 내용 유형 → 컴포넌트

| 내용 유형 | 1순위 | 2순위 | 피할 것 |
|---|---|---|---|
| 핵심 수치 3~5개 | `stats` | `cards` | 수치를 문장에 묻기 |
| 항목별 특징(3~6개) | `cards` | `mini_table` | 산문 단락 |
| 여러 속성 비교(행 8개 이하) | `mini_table` | `cards` | 9행 이상 표 |
| 수량 비교·순위 | `hbars` | `stats` | 숫자만 나열한 표 |
| 단계·절차·인과 | `flow` | `layers` | 번호 붙인 문장 |
| 사건 연대기 | `timeline` | `mini_table` | 날짜 열만 있는 표 |
| 포지셔닝(2축) | `quadrant` | `cards` | 2축을 문장으로 설명 |
| 계층·생태계 구조 | `layers` | `cards` | 들여쓰기 목록 |
| 관내·관외·미확인 표시 | `chip` | 색 글자 | 범례 없는 색 |
| 결론 한 줄 | `callout` | | 헤드라인 반복 |
| 계산식·조사 범위 단서 | `note` | | 본문 크기 단서 |
| 외부 그림(PNG·SVG) | `chart_img` | | 19px 미만 글자가 든 그림 |
| 장 정리(As-Is → To-Be) | `visual_summary_html` 쪽 | | 표 한 장으로 정리 |
| 장 결론(3축 시사점) | `implication_html` 쪽 | | 불릿 나열 쪽 |

배치용(컴포넌트 종류 셈에 들어가지 않음) : `two_panel`, `fill`, `panel_title`

## 2. 쪽 함수

| 함수 | 쓰임 | 주요 인자 |
|---|---|---|
| `slide_html(no, sec_title, sec_sub, headline, body, source=None, kind="content", part=None)` | 5-Zone 본문 쪽 | `part` 를 생략하면 `sec_title` 이 덱 QA 의 섹션 묶음 이름 |
| `cover_html(title, subtitle="", series="", date="", note="", logo=None, hero=None, author=None)` | 표지 | 좌상단 `[ {BRAND} ]`, 작성자 = 프로필 `AUTHOR_KR`, `hero=False` 면 오른쪽 장식 없음 |
| `agenda_html(rows, active=None, title="목차", no=None)` | 목차·간지 | `rows=[("1부","제목"),...]` 1~7행, `active=i` 면 i 행만 강조(간지) |
| `sublist_html(items, title, no=None)` | 세부 목차 | 6개 이하 한 열(가운데), 7개 이상 두 열, 최대 24개 |
| `visual_summary_html(no, title, asis, tobe, verdict, conclusion, sub=None, part="", arrow=True)` | 비주얼 요약 | 4절 참고 |
| `implication_html(no, title, headline, rows, sub="① 개요", topic=None, col_titles=None, part=None)` | 시사점 3축 표 | 4절 참고 |
| `thanks_html(no=None, title="감사합니다.", lines=None)` | 감사 쪽 | 프로필 `AUTHOR_KR`, `PHONE_KR`(비면 줄 생략), `EMAIL` |
| `plain_html(no, inner, footer=True, part="")` | 자유 배치(전면 이미지 등) | 크레딧·쪽 번호는 유지 |

전면 이미지 한 장 예 :
```python
plain_html(2, '<img src="%s" style="position:absolute;left:0;top:0;width:1920px;height:1000px;object-fit:contain">'
           % Path("author.png").resolve().as_uri())
```

## 3. 본문 컴포넌트

색 인자(`color_key`, `kind`)는 `inside`(=`red`, `관내`) · `outside`(=`navy`, `관외`) · `unknown`(=`grey`, `미확인`) · `key` · `aux` · `asis` 또는 `#RRGGBB`.

### stats : 수치 타일
```python
stats([("3곳", "물류센터", "모두 예시 도시 B시 안", "inside"),
       ("18~61%", "자동화 설비 비중", "센터별 하한과 상한", "outside"),
       ("미확인", "외부 위탁 물량", "이번 자료 범위에서 문서 미발견", "grey")], cols=None)
```
- 항목 = (값, 라벨, 보조, color_key). 보조·color_key 생략 가능. 3~5개 권장. 값은 원고 숫자 그대로

### cards : 카드 격자
```python
cards([("북부센터 (2019년 개장)", ["하루 1만 3천 상자", "자동화 설비 비중 18%"], "outside"),
       ("칩 묶음", chip("관내") + chip("관외", "navy"))], cols=3)
```
- 본문이 목록이면 줄마다 네모 불릿, 문자열이면 불릿 없이 그대로(칩·막대를 카드 안에 넣을 때)
- 카드 하나에 3줄 이하 권장

### mini_table : 표
```python
mini_table(["센터", "피킹 대기(분)", "자동화 비중"],
           [["북부센터", "14", "18%"], ["중앙센터", "7", "61%"]],
           widths=["40%", "30%", "30%"], num_cols=(1, 2), em_rows=(1,), row_height=None)
```
- 8행 이하(넘으면 QA 경고). `num_cols` 오른쪽 정렬, `em_rows` 옅은 빨강 행
- `row_height=58` 처럼 칸 높이를 키우면 행이 적은 표가 쪽을 채움(글자 크기는 그대로)
- 칸 안에 `chip()` 을 넣어 관내·관외·미확인을 표시

### hbars : CSS 가로 막대
```python
hbars([("중앙센터", 146), ("업계 평균(가상)", 110, "navy"), ("남부센터", 91), ("나", 567, None, "567(추정)")],
      unit="상자", max_value=None, color_key="inside", label_width=None, bar_height=None, title=None, height=None)
```
- 항목 = (라벨, 값[, color_key[, 표시 글]]). 값이 문자열 「1,234」면 그대로 표시, 쉼표를 뺀 수로 길이 계산
- `max_value` 로 두 묶음의 눈금을 맞춤. 음수는 받지 않음(오류). 10개 이하 권장
- `height` 를 주면 그 높이 안에 막대를 고르게 벌림(옆 칸과 높이 맞출 때)

### timeline : 가로 타임라인
```python
timeline([("2019.03", "북부센터 개장", "수작업 중심"), ("2025.09", "통합 관제 시범", "중앙센터 1곳", True)],
         color_key="inside", alternate=None,
         phases=[(0, 0, "설비를 더한 시기", "outside"), (1, 1, "흐름을 묶는 시기", "key")])
```
- 사건 2~8개. 6개 이하는 날짜가 선 위·카드가 선 아래 한 줄, 7개 이상은 위·아래 번갈아(`alternate=True` 로 강제)
- 넷째 값 `True` 는 핵심 사건(빨강 #C00000 점·카드). 날짜는 「2026.10」「2026.10.12」 형식
- `phases` : (첫 사건 번호, 끝 사건 번호, 이름, color_key) 로 카드 아래 시기 띠. 번호는 0부터

### quadrant : 2×2 포지셔닝
```python
quadrant("자동화 설비 비중", "데이터 연결 수준",
         [("북부센터", 0.18, 0.22), ("가상 경쟁사 C", 0.80, 0.80, "navy"), ("업계 평균(가상)", 0.47, 0.57, "grey", "l")],
         ("연결 먼저", "통합 운영", "수작업 중심", "설비 먼저"),
         x_ends=("낮음", "높음"), y_ends=("낮음", "높음"), height=600, hot=1)
```
- 점 = (이름, x, y[, color_key[, 이름 위치 r·l·t·b]]), x·y 는 0~1(밖이면 오류)
- 칸 이름 순서 = (왼쪽 위, 오른쪽 위, 왼쪽 아래, 오른쪽 아래). `hot` 칸은 옅은 빨강(없애려면 `None`)
- 이름이 겹치면 렌더 때 다른 자리로 옮김. 끝내 못 피하면 QA 경고 「사분면 점 이름 겹침」

### layers : 적층 박스
```python
layers([("관제 계층", ["통합 관제 화면", ("작업 배분 자동화", True)], "inside", "중앙센터 1곳만 시범 운영"),
        ("데이터 계층", ["재고 기록", "설비 상태 기록"], "navy", "센터마다 따로 저장")],
       label_width=280, note_width=250, height=None)
```
- 위 행이 위층. 요소 `("글", True)` 는 빨강 테두리 강조. 넷째 값은 오른쪽 회색 메모
- `height` 를 주면 층들이 그 높이를 똑같이 나눔

### flow : 단계 화살표
```python
flow([("입고", "트럭 하차와 검수"), ("피킹", "주문별로 꺼내 모음"), ("출고", "하루 4회 마감")], active=1)
```
- 3~6단계 권장. `active` 는 강조 단계 번호(0부터) 또는 번호 목록

### chip · callout · note · chart_img
```python
chip("B시 안", "red"); chip("B시 밖", "navy"); chip("미확인", "grey"); chip("빈 칩", "hollow")
callout("세 센터의 차이는 설비 대수보다 「일을 나누는 방식」에서 생김")   # ☞ 정리 줄
note("1인 하루 처리량 = 하루 처리량 ÷ 현장 작업자 수")                 # 19px 회색 단서
chart_img("fig_wait.svg", height=400, caption="단계별 대기 시간 (분, 가상)") # 경로는 절대 URI 로 바뀜
```
- `chart_img` 그림 안의 글자도 19px 이상(쪽에 들어간 크기 기준). 자동 QA 는 그림 안 글자를 읽지 못하므로 육안으로 확인. 그림 파일이 없으면 QA 오류

### 배치 : two_panel · fill · panel_title
```python
two_panel(left_html, right_html, ratio="1.12fr 1fr", gap=36, align="start")   # align : start|center|end|stretch
fill(group1, group2, group3, align="evenly")   # 본문 남는 높이를 묶음 사이에 고르게 나눔
panel_title("하루 처리량 (상자)")              # 칸 위 작은 제목 + 밑줄
```
- `fill` 은 본문 바로 아래 단계, 또는 `two_panel(align="stretch")` 의 한쪽 칸 안에서 씀
- 내용이 짧아 쪽 아래가 비면(QA 경고 「본문 아래 빈 공간」) `fill` 로 묶음 사이를 벌리거나 컴포넌트를 키움

## 4. 비주얼 요약 · 시사점 쪽

### visual_summary_html
```python
visual_summary_html(
    13, "자동화의 기준 : 「설비 대수」에서 「흐름 관리」로",
    asis={"tag": "As-Is", "title": "센터마다 따로 도는 설비", "mode": "flow",
          "items": [("주문 접수", "센터별 시스템 3개"), ("작업자 배정", "관리자가 경험으로 배정")],
          "desc": ["센터 3곳이 각자 시스템과 기록을 가짐", "작업 배분은 관리자의 경험에 기댐"]},
    tobe={"tag": "To-Be", "title": "하나의 관제로 묶인 흐름", "mode": "hub",
          "center": ("통합 관제", "작업 배분 자동화"),
          "items": ["북부센터", "중앙센터", ("수요 예측", "aux")],
          "desc": ["3곳의 기록을 한곳에 모아 배분을 자동화"]},
    verdict=("설비 대수", "<", "흐름 관리"),
    conclusion="다음 투자의 첫 순서는 설비 추가가 아니라 흐름을 하나로 묶는 관제입니다",
    sub="3. 비주얼 요약")
```

| 열 키 | 뜻 |
|---|---|
| `mode="flow"` | 단계 상자 + 화살표. 3개 이하는 가로, 4~5개는 세로(`direction="h"\|"v"` 로 지정 가능). 세로일 때 보조 글은 상자 오른쪽 설명으로 |
| `mode="list"` | 요소 상자 격자(1~9개) |
| `mode="hub"` | 가운데 상자 `center` + 주변 1~6개를 고정 자리에 배치하고 선으로 이음 |
| `html` | 직접 그린 도해(748×330 칸 안) |
| `items` 요소 | `"글"` · `("글", "보조 글")` · `("글", "key"\|"aux"\|True)` · `("글", "보조 글", 강조)` |
| `desc` | 열 아래 설명 3줄 이하(넘으면 오류) |

- 색 : As-Is 열과 기존 요소는 회색, To-Be 열과 핵심 변화(`"key"`)는 빨강 #C00000, 보조 강조(`"aux"`)는 적갈색 #843C0C
- `verdict` 가 3칸 튜플이면 왼쪽 값 · 부호 · 오른쪽 값을 열에 맞춰 놓음. 문자열이면 한 줄 가운데
- 헤드라인 문단·Source 줄 없음. 크레딧과 쪽 번호는 유지. 결론 띠 문장은 「~합니다」 존댓말 허용
- 제목·판정·결론 띠·도해 상자는 넘치면 글자를 줄여 맞추고 QA 경고 「글자 자동 축소」를 냄. 줄여도 넘치면 오류

### implication_html
```python
implication_html(
    14, "4. 통합 관제 시사점",
    "통합 관제는 설비를 늘리는 투자와 다르게 센터 사이의 흐름을 바꾸는 일임. 관리의 기준이 「센터별 처리량」에서 「전체 대기 시간」으로 옮겨 갈 것임.",
    [("일을 나누는 주체",
      ("관리자의 경험 → 관제 규칙", ["주문이 들어오면 규칙이 작업자와 설비를 함께 배정", ("관리자는 예외 처리를 맡음", 2)]),
      ("배분 기준을 「문서」로 남기는 일이 먼저", ["센터마다 다른 배정 기준을 하나로 맞춤"])),
     ("일의 형태", (...), (...)),
     ("관리", (...), (...))],
    sub="① 개요", topic="통합 관제")
```
- 제목 「N. {주제} 시사점」 빨강 #C00000 굵게, 오른쪽 라벨 회색 #595959, 헤드라인 검정 2문장
- 열 제목 기본값 : 「관점」 / 「{topic}(으)로 바뀔 때 함께 오는 변화」 / 「요구 사항」. `col_titles=(a, b, c)` 로 바꿈
- 행 3개 권장(1~4). 칸 = (굵은 리드, [불릿]). 리드는 「A → B」 이동 형식 권장
- 불릿은 칸마다 2개 이하(넘으면 QA 경고). `("글", 2)` 는 2단 ○ 불릿. 불릿 색 적갈색 #843C0C
- 하단 ☞ 줄·※ 단서 줄·Source 줄 없음(넣으면 QA 경고)

## 5. 렌더·묶기

```python
paths = render_all(pages, out_dir, prefix="s", strict=False, palette=True, lexicon="auto", mode="analysis")
# paths : PNG 경로 list. paths.ok / paths.errors / paths.warnings / paths.report / paths.report_path
outs = bundle(paths, "예시덱", out_dir, formats=("pdf", "pptx", "zip"), title=None, author=None, alt_texts=None)
# outs : {"pdf": ..., "pptx": ..., "zip": ...}
```

| 함수 | 반환 | 메모 |
|---|---|---|
| `render_all(htmls, out_dir, prefix="s", strict=False, palette=True, lexicon="auto", mode="analysis", timeout_ms=4000)` | `RenderResult`(list) | `{prefix}NN.html/.png` + `qa_report.json`. 같은 접두어의 예전 PNG·HTML 은 지움. `strict=True` 면 오류 때 종료코드 1 |
| `check_palette(theme=None, verbose=True)` | dict | `fail`(대비 미달 수), `warn`(의미색 구분 경고 수) |
| `load_profile(required=("AUTHOR_KR","AUTHOR_EN","EMAIL"), exit_on_missing=True, quiet=False)` | dict | 비면 종료코드 2 |
| `set_profile(values)` | dict | 파일 없이 직접 넣기(시험·다른 스킬) |
| `make_theme(overrides, activate=True)` | dict | 토큰 이름이 틀리거나 #RRGGBB 가 아니면 오류 |
| `bundle(png_paths, base_name, out_dir, formats=("pdf","pptx","zip"), title=None, author=None, alt_texts=None)` | dict | 산출물 쪽 수를 PNG 수와 대조, 다르면 오류 |
