# 플로우 차트 설계 (Flow Chart Design for Word)

## 공통 스펙

| 항목 | 값 |
|------|-----|
| 캔버스 크기 | 900 × 1020 px |
| 배경색 | #F0F4FA |
| 렌더링 | cairosvg → PNG |
| 한국어 폰트 | NanumGothic (fontconfig 등록 필요) |
| 영어 폰트 | Arial, Helvetica, sans-serif |
| DOCX 이미지 삽입 크기 | width=540, height=612 pt |

---

## NanumGothic 폰트 설치 (한국어 차트용, 최초 1회)

```bash
pip install cairosvg --break-system-packages 2>/dev/null
mkdir -p ~/.fonts
# NanumGothic.ttf가 없으면:
# wget -q -O ~/.fonts/NanumGothic.ttf "https://github.com/naver/nanumfont/raw/master/NanumGothic.ttf"
fc-cache -f ~/.fonts/ 2>/dev/null
```

SVG CSS에서:
```xml
<style>text { font-family: NanumGothic, Arial, sans-serif; }</style>
```

---

## SVG 레이아웃 (900×1020)

```
Y=0~62    : 타이틀 바 (#1A1A2E)
Y=62      : 구분선 (#4A90D9, 2px)
Y=72~94   : 핵심 메시지 헤더 (#1A3A6B)
Y=100~180 : 핵심 메시지 3 박스 (나란히, 각 272×80)
Y=180~202 : 점선 연결 화살표
Y=204~224 : 플로우 헤더 (#37474F)
Y=228~290 : Layer 0 — 핵심 모델/경제 (중앙 520×62, #0055B3)
Y=290~310 : 연결 화살표
Y=314~394 : Layer 1 — 기술 A (좌 396×80) + 기술 B (우 396×80) (#003F8A)
Y=344~360 : 중간 연결 박스 (~200×16, #0A2A5E)
Y=394~414 : 연결 화살표
Y=418~494 : Layer 2 — SW A (좌 396×76) + SW B (우 396×76) (#1A4D1A)
Y=494~518 : 연결 화살표
Y=518~590 : Layer 3 — 확장 3분할 (각 270×72, #4A1A4A)
Y=590~614 : 연결 화살표
Y=614~682 : Layer 4 — 인프라 A (좌 396×68) + B (우 396×68) (#3A2A00)
Y=682~706 : 연결 화살표
Y=706~764 : 결론 박스 (80~820, 740×58, #B71C1C)
Y=776~832 : Devil's Advocate (#FFFDE7, 테두리 #F9A825)
Y=840~860 : 5관점 헤더 (#2C3E6B)
Y=866~926 : 5관점 박스 (각 162×60)
Y=936~1002: 하단 노트 (#ECEFF1)
```

---

## 레이어별 색상 코드

| 레이어 | 용도 | 배경 | 헤더 |
|--------|------|------|------|
| Layer 0 | 핵심 모델/경제 | #0055B3 | #1565C0 |
| Layer 1 | 하드웨어/기술 | #003F8A | #0066CC |
| Layer 2 | 소프트웨어/플랫폼 | #1A4D1A | #2E7D32 |
| Layer 3 | 물리적 확장/응용 | #4A1A4A | #6A1B9A |
| Layer 4 | 인프라/생태계 | #3A2A00 | #E65100 |
| 결론 | 최종 성과 | #B71C1C | #C62828 |

---

## 핵심 메시지 박스 색상

| 메시지 | 배경 | 텍스트 |
|--------|------|--------|
| ① | #0055B3 | #C8DFFF |
| ② | #1B5E20 | #C8FFC8 |
| ③ | #4A1A4A | #E8C8FF |

---

## 5관점 박스 색상

| 관점 | 배경 | 테두리 |
|------|------|--------|
| 개인/Individual | #E3F2FD | #1565C0 |
| 조직/Organization | #E8F5E9 | #2E7D32 |
| 사회/Society | #FFF3E0 | #E65100 |
| 국가/Nation | #F3E5F5 | #6A1B9A |
| 글로벌/Global | #FCE4EC | #C62828 |

---

## 화살표 마커 정의

```xml
<defs>
  <marker id="arr" markerWidth="8" markerHeight="7" refX="6" refY="3.5" orient="auto">
    <path d="M0,0 L0,7 L8,3.5 z" fill="#444"/>
  </marker>
  <marker id="arr_d" markerWidth="8" markerHeight="7" refX="6" refY="3.5" orient="auto">
    <path d="M0,0 L0,7 L8,3.5 z" fill="#888"/>
  </marker>
</defs>
<!-- 실선: marker-end="url(#arr)" -->
<!-- 점선: stroke-dasharray="4,2" marker-end="url(#arr_d)" -->
```

---

## 렌더링 코드

```python
import cairosvg

# 한국어 (bytestring 방식 — NanumGothic 폰트 적용)
cairosvg.svg2png(
    bytestring=kr_svg.encode('utf-8'),
    write_to='workflow_chart_kr.png',
    output_width=900, output_height=1020
)

# 영어 (파일 저장 후 URL 방식)
with open('workflow_chart_en.svg', 'w') as f:
    f.write(en_svg)
cairosvg.svg2png(
    url='workflow_chart_en.svg',
    write_to='workflow_chart_en.png',
    output_width=900, output_height=1020
)
```

---

## 소스 주제별 레이어 명칭 가이드

| 소스 주제 | Layer 0 | Layer 1 | Layer 2 | Layer 3 | Layer 4 |
|-----------|---------|---------|---------|---------|---------|
| AI/기술 | 경제 모델 | 하드웨어 | 소프트웨어 | 물리적 AI | 인프라 |
| 비즈니스/전략 | 핵심 전략 | 제품/서비스 | 플랫폼 | 파트너십 | 생태계 |
| 정책/사회 | 핵심 이슈 | 현황 분석 | 정책 방향 | 이해관계자 | 글로벌 흐름 |
| 과학/연구 | 핵심 발견 | 방법론 | 실험 결과 | 응용 분야 | 향후 과제 |

레이어가 소스 내용에 맞지 않으면 필요한 레이어만 사용.
