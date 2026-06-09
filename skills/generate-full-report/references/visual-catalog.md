# visual-catalog.md — 시각화 카탈로그 (권장 가이드) v0.9

> 목적: 표지 플로우차트 1개에 머물던 시각화를 **본문 전반**으로 확장한다.
> 이 문서는 **권장 가이드**다(의무 게이트 아님). 단, "내용 유형 → 시각요소" 매핑이
> 명백한데 줄글로만 쓰는 것은 피한다. 직관성이 목적이며 장식이 아니다.

---

## 1. 내용 유형 → 시각요소 매핑 (이 표를 기본 판단 기준으로)

| 내용 유형 | 1순위 시각요소 | 구현 (KR/EN 공통) |
|---|---|---|
| 프로세스·인과·구조 흐름 | **플로우차트** (박스+화살표) | Pillow PNG → DOCX 본문 / PPTX Zone4 |
| 항목 간 비교 (3개 이상 축) | **표** | DOCX `makeTable()` / PPTX `make_table()` |
| 수량 비교·점유율 | **가로 막대차트** | PPTX `make_hbars()` / DOCX Pillow PNG |
| 시계열 추이 | 막대(연도별) 또는 라인 | Pillow PNG |
| 경쟁 포지셔닝 | **2×2 매트릭스** | Pillow PNG (축 라벨 + 로고/사명 텍스트) |
| 사건 연대기 | **타임라인** (가로선 + 마일스톤) | Pillow PNG |
| 계층·생태계 구조 | 레이어 다이어그램 (적층 박스) | Pillow PNG |
| 찬반·시나리오 분기 | 분기 트리 (1→2~3 갈래) | Pillow PNG |

권장 밀도: **챕터마다 시각요소 1개 이상** (표 포함). 동일 차트의 KR/EN 두 벌 생성.
같은 데이터에 차트와 표를 중복으로 쓰지 않는다 — 정밀 수치는 표, 패턴 인식은 차트.

---

## 2. 공통 스타일 (신동형 정본 팔레트)

```
주색    #1A3A6B  (네이비 — 제목·헤더·강조 박스 테두리)
보조    #2E6DA4  (밝은 네이비 — 두 번째 시리즈)
강조    #C0504D  (적색 — 경고·하락·Devil's Advocate)
중립    #7F7F7F  (회색 — 보조선·캡션)
배경    #FFFFFF  고정, 옅은 채움 #EAF0F8
폰트    KR=NanumGothic(+Bold), EN=DejaVu Sans / Arial
```

- 캔버스: 2000px 폭 기준 (DOCX 본문 폭 630pt에 비율 축소 삽입)
- 선 두께 3~4px, 박스 모서리 radius 12px, 화살표 머리 삼각형
- 텍스트는 박스 중앙 정렬, 줄당 ≤14자(KR)/≤28자(EN) — overflow 금지

## 3. Pillow 공통 레시피 (박스+화살표 helper)

```python
from PIL import Image, ImageDraw, ImageFont
F  = ImageFont.truetype('/root/.fonts/NanumGothic.ttf', 40)        # KR
FB = ImageFont.truetype('/root/.fonts/NanumGothicBold.ttf', 46)

def box(d, x, y, w, h, text, fill='#EAF0F8', edge='#1A3A6B', font=F, color='#1A3A6B'):
    d.rounded_rectangle([x, y, x+w, y+h], radius=12, fill=fill, outline=edge, width=4)
    lines = text.split('\n')
    th = sum(font.getbbox(l)[3] for l in lines) + (len(lines)-1)*8
    cy = y + (h-th)//2
    for l in lines:
        tw = font.getbbox(l)[2]
        d.text((x+(w-tw)//2, cy), l, font=font, fill=color); cy += font.getbbox(l)[3]+8

def arrow(d, x1, y1, x2, y2, color='#1A3A6B'):
    d.line([x1, y1, x2, y2], fill=color, width=4)
    import math
    a = math.atan2(y2-y1, x2-x1)
    for s in (0.5, -0.5):
        d.line([x2, y2, x2-22*math.cos(a-s), y2-22*math.sin(a-s)], fill=color, width=4)
```

타임라인·2×2·레이어도 같은 helper 조합으로 그린다 (가로선+눈금, 십자축+사분면 라벨,
세로 적층 박스). SVG/cairosvg 사용 시 `&` → `&amp;` escape, 한글 missing glyph 주의.

## 4. 삽입 규격

### DOCX
```python
from PIL import Image
img = Image.open('fig_ch3_kr.png')
h = int(630 * img.size[1] / img.size[0])   # width 630 고정, height 비율 계산
# build_kr.js: transformation { width: 630, height: h }
```
그림 직후 캡션 1줄(회색, 작은 글자): `[그림 N] 제목 (출처)`.

### PPTX (Zone4)
- Zone4 영역(y=1850000~4715475)에 맞춰 세로 최대 약 2.8M EMU. 이미지가 클 경우
  좌측 60% 이미지 + 우측 40% 해설 2~3줄 구성 권장.
- 표는 `make_table()`, 막대는 `make_hbars()` (pptx-chart-helpers.md) 우선 —
  XML 네이티브가 이미지보다 선명하고 가볍다.
- 표 overflow 방지: 열 5개 이하, 셀 텍스트 KR ≤12자. 넘치면 행을 나누거나 2개 표로.

## 5. 표지 플로우차트 (기존 규격 유지)

docx-chart-design.md 의 표지 차트 규격(2000×~1025px KR / ~1440px EN)을 그대로 따른다.
본 카탈로그는 표지 외 **본문 시각화**를 위한 확장 가이드다.

## 6. 자기 점검 (권장)

- [ ] 챕터별 시각요소 계획표를 Phase 2에서 만들었다 (유형 매핑 표 근거)
- [ ] 프로세스 설명을 줄글로만 쓴 챕터가 없다
- [ ] 모든 차트·그림에 출처/캡션이 있다
- [ ] KR/EN 두 벌 모두 생성했고 폰트가 올바르다 (KR=NanumGothic)
