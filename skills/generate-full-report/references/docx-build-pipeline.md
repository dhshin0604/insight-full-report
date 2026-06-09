# DOCX 빌드 파이프라인 v0.2 (Build Pipeline)

이 파일의 모든 코드 패턴은 실제 EmbodiedAI 보고서 생성에서 검증된 것입니다.

---

## 환경 요구사항

| 항목 | 버전/경로 |
|------|-----------|
| Node.js | v18+ |
| docx npm 패키지 | NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules |
| Python | 3.8+ |
| PIL/Pillow | pip install Pillow --break-system-packages |
| cairosvg | pip install cairosvg --break-system-packages |
| NanumGothic.ttf | ~/.fonts/ (fontconfig 등록) |

```bash
# 환경 확인
NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules node -e "require('docx'); console.log('docx OK')"
python3 -c "import cairosvg; print('cairosvg OK')"
fc-match "NanumGothic"
```

---

## 빌드 파일 구조

```
/sessions/{session-id}/
├── workflow_chart_kr.png          # Phase 3에서 생성 (900×1020px)
├── workflow_chart_en.png          # Phase 3에서 생성 (900×1020px)
├── workflow_chart_kr_cropped.png  # PIL 크롭 후 (하단 여백 제거)
├── workflow_chart_en_cropped.png  # PIL 크롭 후
├── build_kr.js                    # 한국어 DOCX 빌드
└── build_en.js                    # 영어 DOCX 빌드
```

---

## build_kr.js / build_en.js 공통 구조 (★ 검증된 패턴)

```javascript
'use strict';
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  ImageRun, Table, TableRow, TableCell, WidthType,
  BorderStyle, AlignmentType, VerticalAlign,
  ShadingType, UnderlineType, PageBreak, ExternalHyperlink,
  Footer, PageNumber,
} = require('docx');
const fs   = require('fs');
const path = require('path');

// ── 폰트 정의 ──
const KR = { ascii: 'Malgun Gothic', eastAsia: 'Malgun Gothic', hAnsi: 'Malgun Gothic' };
const EN = { ascii: 'Arial', eastAsia: 'Arial', hAnsi: 'Arial' };
const F  = KR;  // 한국어본: F = KR, 영어본: F = EN

// ── 텍스트 런 헬퍼 ──
const B  = (t, sz, c) => new TextRun({ text: t, bold: true,  size: sz||22, font: F, color: c||'000000' });
const N  = (t, sz, c) => new TextRun({ text: t, bold: false, size: sz||22, font: F, color: c||'000000' });
const P  = (...runs)  => new Paragraph({ children: runs, spacing: { before: 0, after: 200 } });
const BK = ()         => new Paragraph({ children: [], spacing: { before: 0, after: 80 } });
const PB = ()         => new Paragraph({ children: [new PageBreak()] });

// ── 제목 헬퍼 ──
const H1 = (t) => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 28, font: F, color: '1A3A6B' })],
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 160 },
});
const H2 = (t) => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 24, font: F, color: '333333' })],
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 120 },
});

// ── SL 헬퍼 (Executive Summary 서브섹션 레이블) ──
// Executive Summary 통합 textBox 안에서 ■ Key Message / ■ 배경 / ■ 핵심 구조 흐름 / ■ 전망 표시
const SL = (label) => new Paragraph({
  children: [new TextRun({ text: label, bold: true, size: 22, font: F, color: '1A3A6B' })],
  spacing: { before: 120, after: 60 },
});

// ── textBox 헬퍼 ──
// title=null이면 제목 없이 본문만 (Executive Summary 통합 박스에 사용)
function textBox(title, children) {
  const titleRow = title ? [new Paragraph({
    children: [new TextRun({ text: title, bold: true, size: 24, font: F, color: '1A3A6B' })],
    spacing: { before: 0, after: 120 },
  })] : [];
  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: [9026],
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 8, color: '1A3A6B' },
      bottom: { style: BorderStyle.SINGLE, size: 3, color: 'CCCCCC' },
      left:   { style: BorderStyle.NONE },
      right:  { style: BorderStyle.NONE },
      insideH:{ style: BorderStyle.NONE },
      insideV:{ style: BorderStyle.NONE },
    },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: 9026, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: 'F0F4FA' },  // ⚠️ CLEAR, NOT SOLID
      margins: { top: 250, right: 500, bottom: 250, left: 500 },
      verticalAlign: VerticalAlign.TOP,
      children: [...titleRow, ...children],
    })] })],
  });
}

// ── makeTable 헬퍼 (비교표) ──
function makeTable(headers, rows) {
  const colWidths = headers.map(() => Math.floor(9026 / headers.length));
  const headerCells = headers.map((h, i) => new TableCell({
    width: { size: colWidths[i], type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: '1A3A6B' },
    margins: { top: 100, right: 200, bottom: 100, left: 200 },
    children: [new Paragraph({
      children: [new TextRun({ text: h, bold: true, size: 19, font: F, color: 'FFFFFF' })],
    })],
  }));
  const dataRows = rows.map(cells => new TableRow({
    children: cells.map((c, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: 'FFFFFF' },
      margins: { top: 80, right: 200, bottom: 80, left: 200 },
      children: [new Paragraph({
        children: [new TextRun({ text: c, size: 19, font: F, color: '333333' })],
      })],
    })),
  }));
  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: colWidths,
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      left:   { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      right:  { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      insideH:{ style: BorderStyle.SINGLE, size: 2, color: 'DDDDDD' },
      insideV:{ style: BorderStyle.SINGLE, size: 2, color: 'DDDDDD' },
    },
    rows: [new TableRow({ children: headerCells }), ...dataRows],
  });
}

// ── 이미지 로드 (크롭된 파일 사용) ──
const imgData = fs.readFileSync(path.join(__dirname, 'workflow_chart_kr_cropped.png'));
// 영어본: workflow_chart_en_cropped.png

// ── Document 생성 ──
const doc = new Document({
  styles: {
    default: {
      heading1: {
        run: { font: F, size: 28, bold: true, color: '1A3A6B' },
        paragraph: { spacing: { before: 360, after: 160 } },
      },
      heading2: {
        run: { font: F, size: 24, bold: true, color: '333333' },
        paragraph: { spacing: { before: 280, after: 120 } },
      },
    },
  },
  sections: [{
    properties: {
      titlePage: true,
      page: {
        size: { width: 11906, height: 16838 },  // A4
        margin: { top: 1701, right: 1440, bottom: 1440, left: 1440 },
        pageNumbers: { start: 0 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: F, color: '888888' }),
            new TextRun({ text: ' / ', size: 18, font: F, color: '888888' }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: F, color: '888888' }),
          ],
          spacing: { before: 120, after: 120 },
        })],
      }),
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
    },
    children: [
      // ── PAGE 0: 표지 + 플로우차트 (동일 페이지, PB 없음) ──
      // (아래 "표지 구성" 섹션 참조)

      // ── PAGE 1+: 본문 ──
      // (아래 각 섹션 참조)
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const OUTPUT = path.join(__dirname, '{주제}_KR_Report_{날짜}.docx');
  fs.writeFileSync(OUTPUT, buf);
  console.log('DOCX written:', OUTPUT, `(${Math.round(buf.length/1024)} KB)`);
});
```

---

## ★ 표지 구성 (v0.2 — 최신 기준)

```javascript
// 제목 라인 1 (「제목:」 형식 또는 주제 첫 줄)
new Paragraph({
  children: [new TextRun({
    text: '「{제목 첫 줄}:',
    bold: true, size: 44, font: KR, color: '1A3A6B',
  })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 600, after: 0 },
}),
// 제목 라인 2 (부제목 + 닫는 괄호)
new Paragraph({
  children: [new TextRun({
    text: '{부제목}」',
    bold: true, size: 44, font: KR, color: '1A3A6B',
  })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 200 },
}),
// 날짜 + 작성자
new Paragraph({
  children: [new TextRun({
    text: '{YYYY.MM.DD}  |  작성: DH Shin (신동형)',
    size: 18, font: KR, color: '555555',
  })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 280 },
}),
// 플로우차트 이미지 (⚠️ PB 없이 바로 삽입)
new Paragraph({
  children: [new ImageRun({
    data: imgData,
    transformation: { width: 450, height: 437 },  // 크롭 후 실제 높이 기준
    type: 'png',
  })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 160 },
}),
PB(),  // ← 표지+차트 페이지 끝 (PB는 여기 1개만)
```

**⚠️ 주의사항:**
- 제목과 차트 사이에 PB() 없음 (표지와 차트가 같은 페이지에 있어야 함)
- Source 라인, 해시태그 없음
- 영어본: `「」` 제거, 제목은 그대로. 예: `'Embodied AI Report 2025:'` (sz=44)

---

## ★ Executive Summary (v0.2 — 통합 textBox)

```javascript
H1('Executive Summary'),  // 또는 한국어: H1('Executive Summary')
textBox(null, [
  SL('■ Key Message'),
  P(N('소스 전체를 관통하는 핵심 명제. 1~2문장. 구체적 수치 포함.')),

  SL('■ 배경'),
  P(N('왜 지금 이 주제인가? 거시적 맥락, 기관 정의, 주요 수치.')),

  SL('■ 핵심 구조 흐름'),
  P(B('① 첫번째 축: ', 22), N('설명 내러티브.')),
  P(B('② 두번째 축: ', 22), N('설명 내러티브.')),
  P(B('③ 세번째 축: ', 22), N('설명 내러티브.')),
  P(B('④ 네번째 축: ', 22), N('설명 내러티브.')),

  SL('■ 전망'),
  P(N('단기: ... 중기: ... 장기: ...')),
]),
BK(), PB(),
```

**v0.1 대비 변경**: 3개의 별도 textBox → 통합 1개 textBox + SL() 서브섹션

---

## ★ 챕터별 본문 (v0.2 — 내러티브 산문체)

```javascript
PB(),
H1('Chapter I. {챕터 제목}'),
H2('1.1 {소주제}'),
textBox('KEY MESSAGE', [
  P(N('완결 분석 문장. ~입니다 어미. 40~100자. 비유나 수치 포함.')),
]),
BK(),
// 내러티브 단락 3~4개 (불릿 절대 금지)
P(N('첫 번째 단락: 맥락 설명 + 구체적 사례. 한 문단에 2~4문장. 입니다/합니다 체.')),
P(N('두 번째 단락: 심층 분석 + 수치. 비유 사용 가능 ("도서관 vs 직접 배달"처럼).')),
P(N('세 번째 단락: 함의·시사점. 왜 중요한가.')),
BK(),

// 비교 데이터가 있으면 makeTable 삽입
makeTable(
  ['구분', '방식', '대표 사례', '강점', '약점'],
  [
    ['유형 A', '설명', '사례', '장점', '단점'],
    ['유형 B', '설명', '사례', '장점', '단점'],
  ]
),
BK(),
```

---

## ★ Q&A 섹션 (v0.2)

```javascript
H1('핵심 질문과 답변'),
textBox(null, [
  P(B('Q1. 질문 내용?', 22, '1A3A6B')),
  P(N('A. 답변 내러티브. 단순 나열 금지, 흐름 있는 완결 문장. 비유/수치 포함. 입니다체.')),
  BK(),
  P(B('Q2. 질문 내용?', 22, '1A3A6B')),
  P(N('A. ...')),
  // Q1~Q6 반복
]),
BK(), PB(),
```

---

## ★ Devil's Advocate (v0.2)

```javascript
PB(),
H1("Devil's Advocate — 비판적 검토"),
// 5개 관점, 각각 별도 textBox
textBox('① {비판 포인트 제목}', [
  P(N('비판적 관점 내러티브. 단순 반박이 아닌 구조적 약점 분석. 입니다체.')),
]),
BK(),
textBox('② {비판 포인트 제목}', [...]),
// ...
```

---

## ★ 참고문헌 (하이퍼링크 삽입)

```javascript
PB(),
H1('참고문헌'),
new Paragraph({
  children: [
    new TextRun({ text: '• ', font: F, size: 21 }),
    new ExternalHyperlink({
      link: 'https://소스URL',
      children: [new TextRun({
        text: '소스 제목 (기관, 날짜)',
        font: EN, size: 21, color: '0563C1',
        underline: { type: UnderlineType.SINGLE, color: '0563C1' },
      })],
    }),
  ],
}),
```

---

## ★ JS 따옴표 충돌 방지 (⚠️ 반드시 준수)

한국어 텍스트에서 인용부호 `'단어'` 형태는 JS 싱글쿼트 string delimiter와 충돌하여
SyntaxError를 일으킵니다.

```javascript
// ❌ 위험 — SyntaxError 발생
P(N('텍스트를 생성하는 '두뇌'만 있었습니다')),

// ✅ 안전 — 한국식 꺽쇠 사용
P(N('텍스트를 생성하는 「두뇌」만 있었습니다')),
```

build_kr.js 작성 시 한국어 인용부호가 필요한 경우 `「」` 사용을 원칙으로 합니다.
작성 후 반드시 `node --check build_kr.js` 로 문법 검증합니다.

---

## CRITICAL BUG FIX: ShadingType.CLEAR

```javascript
// ✅ 올바름 (F0F4FA 연한 파랑 배경)
shading: { type: ShadingType.CLEAR, fill: 'F0F4FA' }

// ❌ 절대 사용 금지 (검은 배경 버그)
shading: { type: ShadingType.SOLID, fill: 'F0F4FA' }
```

---

## 문서 섹션 간격 설정

| 요소 | spacing.after |
|------|--------------|
| P() 내러티브 단락 | 200 |
| BK() 빈 줄 | 80 |
| textBox 후 BK() | 80 |
| SL() 서브섹션 레이블 | 60 (before: 120) |
| H1 | 160 (before: 360) |
| H2 | 120 (before: 280) |

---

## 파일명 규칙

```
한국어: {주제코드}_KR_Report_{YYYYMMDD}.docx
영어:   {주제코드}_EN_Report_{YYYYMMDD}.docx
```

출력 경로 — 워크스페이스 폴더 동적 탐색:

```bash
WORKSPACE=$(find /sessions -maxdepth 4 -type d -name "ClaudeCoworkFile" 2>/dev/null | head -1)
echo "WORKSPACE=$WORKSPACE"
# 예: /sessions/funny-jolly-euler/mnt/ClaudeCoworkFile
```

---

## 챕터 자동 번호 헬퍼 — H1C / H2C (v0.9.1 필수)

본문 챕터 헤딩은 **반드시 H1C/H2C 헬퍼**로 작성한다. 번호가 코드 카운터에서 자동
증가하므로, 내용 치환 시 `1. / 1.1` 번호가 누락되는 드리프트가 구조적으로 불가능하다.

```js
let _ch = 0, _sec = 0;
const H1C = (t) => { _ch += 1; _sec = 0; return H1(`${_ch}. ${t}`); };   // "1. 제목"
const H2C = (t) => { _sec += 1; return H2(`${_ch}.${_sec} ${t}`); };      // "1.1 소제목"
```

사용 규칙:

| 섹션 | 헬퍼 | 결과 |
|---|---|---|
| 본문 챕터 (Devil's Advocate 포함) | `H1C('제목')` | `1. 제목`, `2. 제목` … |
| 챕터 내 소제목 | `H2C('소제목')` | `1.1`, `1.2`, `2.1` … |
| Executive Summary / 핵심 질문과 답변 / 맺음말 / 참고 자료 / 핵심 키워드 | `H1()`/`H2()` (번호 없음) | 그대로 |

- 챕터 순서를 바꾸거나 추가/삭제해도 번호는 자동 재배열된다 — 텍스트에 번호를 직접 쓰지 말 것.
- `verify_content.py` 의 **HEADNUM 게이트(ERROR)** 가 검사한다: 번호 없는 챕터 H1,
  챕터-소제목 번호 불일치(예: 2장 아래 `1.3`), 번호 순서 오류(1..N 연속 위반).
- PPTX TOC(로마숫자 I~VII)와 Word 번호(1~7)는 표기만 다르고 챕터 구성은 동일해야 한다.
