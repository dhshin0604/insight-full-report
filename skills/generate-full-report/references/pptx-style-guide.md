# PPTX 스타일 가이드 (Style Guide)

## 슬라이드 규격

| 항목 | 값 |
|------|-----|
| 슬라이드 크기 | 9144000 × 5143500 EMU (와이드스크린 16:9) |
| 1 inch | 914400 EMU |
| 전체 슬라이드 수 | 14~18장 (표지 + INDEX + 챕터구분 + 본문 + 맺음말) |

---

## 4-Zone 본문 슬라이드 구조 (반드시 준수)

모든 본문 슬라이드는 아래 5개 Zone을 반드시 포함해야 합니다.

```
Zone 1 (y=264100,  h=220800) : 섹션 헤더 — 좌: 챕터명(bold), 우: 세부번호
Zone 2 (y=641800,  h=669300) : KEY MESSAGE — 완결 분석 문장
Zone 3 (y=1455150, h=280000) : 소주제 배너 (네이비 #1A3A6B 배경, 흰 텍스트)
Zone 4 (y=1790000, h=2860000): 본문 (2단 텍스트 or 표 or 막대차트)
Zone 5 (y=4715475, h=130000) : Source 출처 (회색 소자)
```

### Zone별 X좌표 (본문 기준)
- Zone 1 좌측: x=162800, cx=5100900
- Zone 1 우측: x=4039250, cx=4941900
- Zone 2: x=162725, cx=8818500
- Zone 3: x=162800, cx=8818500
- Zone 4 단일: x=162800, cx=8818500
- Zone 4 2단 좌: x=162800, cx=4300000
- Zone 4 2단 우: x=4680000, cx=4300000
- Zone 5: x=104375, cx=8938800

---

## KEY MESSAGE 원칙 (Zone 2)

**반드시 완결 분석 문장**으로 작성. 키워드 나열 절대 금지.

```
✅ 올바름:
"로보틱스 AI는 Sim-to-Real Gap 극복을 통해 물리 세계 범용화의 임계점에 도달하고 있음."
"확산 정책 모델이 전통 모방 학습 대비 성공률 32% 향상을 달성하며 조작 AI의 새 표준으로 부상 중임."

❌ 잘못됨 (키워드 나열):
"Sim-to-Real, Domain Randomization, Navigation"
"VLA 모델 / Diffusion Policy / SLAM 비교"
```

어미 규칙:
- 소스 확인 사실 → "~임." / "~음."
- 합리적 추론 → "~기반으로 볼 때 ~임."

---

## 표지 슬라이드 구조

```
[제목]      큰 텍스트, 중앙 정렬
[부제목]    중간 크기, 중앙 정렬
[날짜]      소자, 중앙 정렬
[작성자]    "DH Shin (신동형)" / "Dong Hyung Shin"
[해시태그]  소자 이탤릭, KR본=한국어, EN본=영어
```

---

## INDEX 슬라이드 구조

```
[헤더]  "INDEX" (Malgun Gothic, bold)
[목차]  로마 숫자 (I. II. III. IV.) + 챕터명 (bold, sz=1800)
        서브 항목 (▸ 기호, sz=1500, 들여쓰기)
```

---

## 챕터 구분 슬라이드

본문 슬라이드가 시작되기 전 챕터 구분 슬라이드 삽입:
- 챕터 번호 + 챕터 제목만 표시
- Zone 1 헤더만 사용 (Zone 2~5 없음)
- 배경: 템플릿 기본 배경 유지

---

## 맺음말 슬라이드 (고정, 내용 수정 금지)

### 한국어
```
"감사합니다."  (중앙, sz=3000)

● 이 자료는 지속적으로 업데이트되어 공개될 예정입니다.
● 사례 연구나 협업에 관심 있는 기업 및 기관의 연락을 환영합니다.
● 보고서, 출판, 강연 문의는 편하게 연락 주세요.

신동형
010-2202-8761
donghyung.shin@gmail.com
```

### 영어
```
"Thank You."  (중앙, sz=3000)

● This material will be continuously updated and made publicly available.
● Companies or organizations interested in case studies or collaboration are welcome.
● For inquiries regarding reports, book publications, or speaking engagements, please feel free to reach out.

Dong Hyung Shin
+82-10-2202-8761
donghyung.shin@gmail.com
```

---

## 시각화 우선순위 (Zone 4)

1. **표(Table)**: 비교/현황 데이터 → `make_table()` 사용
2. **막대차트**: 수치 비교 → `make_hbars()` 또는 `make_grouped_bars()` 사용
3. **2단 텍스트**: 불릿+설명 (기본, 시각화 데이터 없을 때)

---

## 텍스트 크기 기준

| 요소 | sz (1/100 pt) |
|------|--------------|
| Zone 1 좌 (챕터) | 1800 bold |
| Zone 1 우 (번호) | 1700 |
| Zone 2 (KEY MESSAGE) | 1500 |
| Zone 3 (소주제) | 1500 bold, 흰색 |
| Zone 4 본문 소제목 | 1400~1500 bold |
| Zone 4 본문 일반 | 1100~1300 |
| Zone 4 불릿 | 1100~1200 |
| Zone 5 (Source) | 800 회색 |
| 표 헤더 | 1000 bold |
| 표 데이터 | 920 |

---

## 색상 팔레트

| 용도 | 색상 코드 |
|------|----------|
| 네이비 (Zone 3 배경, 강조) | #1A3A6B |
| 흰색 (Zone 3 텍스트) | #FFFFFF |
| 진한 텍스트 | #1A1A2E, #333333 |
| 소스 텍스트 | #888888 |
| 표 헤더 배경 | #1A3A6B |
| 표 홀수행 | #F0F4FA |
| 표 짝수행 | #FFFFFF |
| 표 테두리 | #C8D0DC |
| 바차트 기본 | #1A5276 |
| 바차트 보조 | #AEB6BF |
| 바차트 배경 | #E8EDF3 |

---

## 파일명 규칙

```
한국어: {주제코드}_KR_Presentation_{YYYYMMDD}.pptx
영어:   {주제코드}_EN_Presentation_{YYYYMMDD}.pptx
```
