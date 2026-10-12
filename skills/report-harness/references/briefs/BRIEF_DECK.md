# {대상} {단계} 이미지 덱 : 파트 담당 브리프 (P1~Pn)

> 이 파일은 뼈대임. 사용자가 MD 토의본을 확인한 뒤 오케스트레이터가 `{ }` 를 채워 작업 폴더에 `BRIEF_DECK.md` 로 둠
> 파트 담당에게는 「`BRIEF_DECK.md` 와 image-deck 스킬의 SKILL.md 를 처음부터 끝까지 읽고 그대로 따를 것. 담당은 P{n}」 한 줄만 줌
> 렌더러는 image-deck 스킬(`{image-deck}/references/deck_core.py`)을 씀. 이 브리프는 파트 나눔과 원고 규칙만 정함

## 0. 맡는 것과 파일

| 파트 | 담당 | 쪽 범위 | 원고(MD 절) | 파일 |
|---|---|---|---|---|
| P1 | {에이전트} | {예) 본문 1장, 약 8쪽} | {§1} | `deck/part1.py` → `PAGES_P1` |
| P2 | {에이전트} | {예) 본문 2장, 약 8쪽} | {§2} | `deck/part2.py` → `PAGES_P2` |
| P{n} | {에이전트} | {앞부분 : 표지, 요약, 목차 / 뒷부분 : 관찰, 맺음말, 감사} | {§0, 맺음말} | `deck/part{n}.py` |

- 각 파트 파일은 HTML 문자열 목록(`PAGES_P{n}`)만 만듦. 쪽 번호는 오케스트레이터가 `spec.py` 에서 이을 때 정하므로 `no` 인자는 오케스트레이터가 준 시작 번호부터 셈
- 그림이 필요한 쪽은 그림 담당의 완료 표시(`figs/_DONE`)가 생긴 뒤에 렌더함. 그 전에는 다른 쪽부터 만듦

## 1. 쪽 규칙 (image-deck 원칙 요약, 자세한 것은 그 스킬의 deck-rules.md)

- 헤드라인 : 명사형 종결 1~2문장, 90~130자, 2줄 이내, 숫자 2개 이상. 첫 문장 = 사실과 구조, 둘째 문장 = {현황 단계 : 보완 사실 / 분석 이후 : 판정이나 재정의}
- 본문 : 컴포넌트로만(산문 단락 없음). 글자 19px 이상, 표 8행 이하
- 파트 안에서 컴포넌트 3종 이상, 표만 있는 쪽 3장 연속 금지
- 쪽 절반 이상에 「☞」 정리 줄(`callout`)
- 출처 줄 2줄 이내. 날짜는 `2026.10.12` 형식(하이픈 금지)
- 색 의미 고정 : {예) 안 = 진빨강, 밖 = 네이비, 미확인 = 회색}. 파트마다 바꾸지 않음
- 숫자는 MD 토의본의 채택값 그대로. 렌더 전에 그 숫자가 MD 에 있는지 확인함

## 2. 쓸 함수 (image-deck)

| 내용 | 함수 |
|---|---|
| 수량 비교 | `hbars`, `stats` |
| 순서, 단계 | `flow`, `timeline` |
| 위치 잡기 | `quadrant` |
| 계층, 구조 | `layers`, `cards` |
| 대조 | `two_panel`, `mini_table` |
| 바뀌기 전과 뒤 | `visual_summary_html` (전면 도해 쪽) |
| 시사점 3축 | `implication_html` (분석 이후 단계) |
| 그림 담당 PNG | `chart_img` |

## 3. 렌더와 자체 QA

```python
import os, sys
sys.path.insert(0, "{image-deck}/references")
from deck_core import *
from part{n} import PAGES_P{n}
res = render_all(PAGES_P{n}, "deck/out_p{n}", prefix="p{n}_", strict=True, mode="{status|analysis}")
```

- `render_all` QA 오류 0 (본문 넘침, 헤드라인 3줄, 출처 줄 초과, 이미지 로드 실패, 19px 미만 글자)
- PNG 를 한 장씩 Read 로 열어 겹침, 잘림, 빈 공간을 눈으로 확인함
- 금지어 확인 : `render_all` 의 lexicon 경고 0건. 줄표(U+2014) 0건

## 4. 최종 메시지

- 파트 파일 경로, 쪽 수, `qa_report.json` 경로와 오류·경고 수
- 눈으로 본 결과 한 줄(고친 쪽 번호)
- MD 와 다르게 쓴 곳(있으면 이유)

## 5. 조립과 묶기 (오케스트레이터)

- `spec.py` 가 표지 → 요약 → 목차 → 파트들 → 맺음말 → 감사 순으로 잇고 `render_all` → `bundle.py --in deck/out --name {파일 기본 이름} --formats pdf,pptx,zip`
- 묶은 뒤 PDF 쪽 수와 PPTX 쪽 수가 PNG 수와 같은지 확인함
