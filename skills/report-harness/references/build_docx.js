#!/usr/bin/env node
'use strict';
/*
 * build_docx.js : content.json → .docx (report-harness)
 *
 * 사용
 *   NODE_PATH="$(npm root -g)" node build_docx.js content.json out.docx
 *
 * 준비
 *   Node 18 이상, npm 패키지 docx (npm install -g docx). require('docx') 가 실패하면
 *   `npm root -g` 폴더를 한 번 더 찾아보고, 그래도 없으면 설치 안내를 내고 종료코드 3.
 *
 * 입력 스키마 : content-schema.md (assemble.py 가 만든 content.json)
 * 작성자 : profile.json 의 AUTHOR_KR, AUTHOR_EN (표지 줄). 찾는 순서
 *   환경변수 PROFILE → 작업 폴더 ./profile.json → 이 파일 옆 profile.json
 *   → 형제 스킬 ../../generate-full-report/references/profile.json
 *   두 값이 모두 찬 첫 파일을 씀. 환경변수 PROFILE_AUTHOR_KR, PROFILE_AUTHOR_EN 이 있으면 그 값이 우선.
 *
 * 문서 순서
 *   표지(제목 줄, 날짜와 작성자 줄, 표지 그림이 한 쪽) → Executive Summary 박스 → 핵심 질문과 답변 박스
 *   → 장마다 새 쪽 「1. 제목」(Heading1) → 절 「1.1 제목」(Heading2) + KEY MESSAGE 박스 + 블록
 *   → (반론 장 : 번호 장) → 맺음말(핵심 문장, 단락, 관점별, 핵심 키워드, 참고 자료)
 *   번호(장, 절, 그림, 표, 질문, 참고 자료)는 이 파일이 붙임. assemble.py 의 메타 claim(Z002~Z004)과 같은 규칙.
 *   헤딩은 generate-full-report/references/verify_content.py 의 HEADNUM 규칙을 따름.
 *
 * 종료코드 : 0 성공 / 1 입력 오류(content.json, 그림) / 2 프로필 값 없음 또는 자리표시 잔존 / 3 docx 패키지 없음
 */
const fs = require('fs');
const path = require('path');

const EXIT_INPUT = 1, EXIT_PROFILE = 2, EXIT_DEP = 3;
const TABLE_WIDTH = 9026;              // A4 본문 폭(twip)
const FIG_WIDTH = 630;                 // 그림 폭(px, 96dpi 기준)
const FIG_MAX_HEIGHT = 820;            // 한 쪽에 들어가는 그림 높이 상한(px)
const PAGE_CONTENT_HEIGHT = 913;       // A4 본문 높이(px) : 16838 - 1701 - 1440 twip
const PLACEHOLDER_RE = /\{(AUTHOR_KR|AUTHOR_EN|PHONE_KR|PHONE_EN|EMAIL|BRAND)\}/g;
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December'];

function die(code, msg) {
  console.error(msg);
  process.exit(code);
}

// ─── 인자 ────────────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const USAGE = '사용 : NODE_PATH="$(npm root -g)" node build_docx.js content.json out.docx';
if (argv.includes('-h') || argv.includes('--help')) { console.log(USAGE); process.exit(0); }
if (argv.length < 2) die(EXIT_INPUT, USAGE);
const CONTENT_PATH = path.resolve(argv[0]);
const OUT_PATH = path.resolve(argv[1]);
if (!/\.docx$/i.test(OUT_PATH)) die(EXIT_INPUT, '[오류] 출력 파일은 .docx 로 끝나야 함 : ' + OUT_PATH);

// ─── docx 패키지 ─────────────────────────────────────────────────────────────
function loadDocx() {
  try { return require('docx'); } catch (e) { /* 아래에서 전역 폴더를 찾음 */ }
  try {
    const root = require('child_process').execSync('npm root -g',
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000 }).trim();
    if (root) return require(path.join(root, 'docx'));
  } catch (e) { /* 설치 안내로 */ }
  die(EXIT_DEP, [
    '[오류] npm 패키지 docx 를 찾지 못함.',
    '  설치 : npm install -g docx',
    '  실행 : NODE_PATH="$(npm root -g)" node build_docx.js content.json out.docx',
    '  (전역 설치가 막혀 있으면 작업 폴더에서 npm install docx 후 같은 폴더에서 실행)',
  ].join('\n'));
}

// ─── 프로필 ──────────────────────────────────────────────────────────────────
const NEEDED = ['AUTHOR_KR', 'AUTHOR_EN'];

function cleanVal(v) {
  if (v === undefined || v === null) return '';
  const s = String(v).trim();
  return /^\{[A-Z_]+\}$/.test(s) ? '' : s;   // 자리표시가 그대로 들어 있으면 빈 값으로 봄
}

function loadProfile() {
  const cands = [];
  if (process.env.PROFILE) {
    const p = path.resolve(process.env.PROFILE);
    if (!fs.existsSync(p)) die(EXIT_PROFILE, '[프로필] 환경변수 PROFILE 이 가리키는 파일이 없음 : ' + p);
    cands.push({ p, why: '환경변수 PROFILE' });
  }
  cands.push({ p: path.resolve('profile.json'), why: '작업 폴더' });
  cands.push({ p: path.join(__dirname, 'profile.json'), why: 'report-harness references' });
  cands.push({ p: path.join(__dirname, '..', '..', 'generate-full-report', 'references', 'profile.json'),
    why: '형제 스킬 generate-full-report' });
  const env = {};
  for (const k of NEEDED) env[k] = cleanVal(process.env['PROFILE_' + k]);
  const tried = [];
  for (const c of cands) {
    if (!fs.existsSync(c.p)) { tried.push(`  - ${c.p} (${c.why}) : 없음`); continue; }
    let d;
    try { d = JSON.parse(fs.readFileSync(c.p, 'utf8')); } catch (e) {
      die(EXIT_PROFILE, `[프로필] profile.json 을 읽지 못함 (${c.p}) : ${e.message}`);
    }
    const prof = {};
    for (const k of NEEDED) prof[k] = env[k] || cleanVal(d[k]);
    const empty = NEEDED.filter(k => !prof[k]);
    if (!empty.length) {
      const fromEnv = NEEDED.filter(k => env[k]);
      const from = fromEnv.length === NEEDED.length ? '환경변수 ' + fromEnv.map(k => 'PROFILE_' + k).join(', ')
        : fromEnv.length ? `${c.p} + 환경변수 ${fromEnv.map(k => 'PROFILE_' + k).join(', ')}` : c.p;
      if (tried.length && process.env.PROFILE && c.why !== '환경변수 PROFILE') {
        console.warn(`[프로필 경고] PROFILE 이 가리키는 파일에 값이 비어 있어 다음 파일을 씀 : ${c.p}`);
      }
      return { prof, from };
    }
    tried.push(`  - ${c.p} (${c.why}) : 빈 값 ${empty.join(', ')}`);
  }
  if (NEEDED.every(k => env[k])) return { prof: env, from: '환경변수 PROFILE_AUTHOR_KR, PROFILE_AUTHOR_EN' };
  die(EXIT_PROFILE, [
    '[프로필] 표지 작성자 줄에 쓸 값이 없음 : ' + NEEDED.join(', '),
    '찾아본 파일',
    ...tried,
    '해결 (하나만 하면 됨)',
    '  (a) 작업 폴더에 profile.json 을 만들고 AUTHOR_KR, AUTHOR_EN 을 채움 (형식은 references/profile.json 의 _examples 참고)',
    '  (b) PROFILE=/경로/profile.json 환경변수로 값이 찬 파일을 지정',
    '  (c) PROFILE_AUTHOR_KR=... PROFILE_AUTHOR_EN=... 환경변수로 값을 직접 줌',
  ].join('\n'));
}

// ─── 날짜 ────────────────────────────────────────────────────────────────────
function parseDate(s) {
  if (typeof s !== 'string') return null;
  let m = s.match(/^\s*(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*$/) ||
    s.match(/^\s*(\d{4})\s*[-./]\s*(\d{1,2})\s*[-./]\s*(\d{1,2})\s*\.?\s*$/);
  let y, mo, d;
  if (m) { y = +m[1]; mo = +m[2]; d = +m[3]; } else {
    m = s.match(/^\s*([A-Za-z]+)\.?\s+(\d{1,2}),\s*(\d{4})\s*$/);
    if (!m) return null;
    const key = m[1].toLowerCase();
    const idx = MONTHS.findIndex(n => n.toLowerCase() === key || (key.length >= 3 && n.toLowerCase().startsWith(key)));
    if (idx < 0) return null;
    y = +m[3]; mo = idx + 1; d = +m[2];
  }
  const dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return null;
  return [y, mo, d];
}
function formatDate(ymd, lang) {
  const [y, m, d] = ymd;
  return lang === 'en' ? `${MONTHS[m - 1]} ${d}, ${y}` : `${y}년 ${m}월 ${d}일`;
}

// ─── PNG 크기 (헤더에서 직접 읽음) ───────────────────────────────────────────
function pngSize(file) {
  const buf = Buffer.alloc(24);
  const fd = fs.openSync(file, 'r');
  try { fs.readSync(fd, buf, 0, 24, 0); } finally { fs.closeSync(fd); }
  const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  if (!buf.subarray(0, 8).equals(sig) || buf.toString('ascii', 12, 16) !== 'IHDR') {
    throw new Error('PNG 파일이 아님');
  }
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  if (!w || !h) throw new Error('PNG 크기가 0');
  return { w, h };
}
function fitBox(w, h, maxW, maxH) {
  let width = maxW, height = Math.round(maxW * h / w);
  if (height > maxH) { height = maxH; width = Math.max(1, Math.round(maxH * w / h)); }
  return { width, height };
}
// 제목 줄이 차지할 높이를 어림해 표지 그림 높이 상한을 정함 (표지와 그림이 한 쪽에 있도록)
function emWidth(s) {
  let em = 0;
  for (const ch of String(s)) em += /[\u1100-\u11ff\u3000-\u9fff\uac00-\ud7af\uff00-\uffef]/.test(ch) ? 1 : 0.56;
  return em;
}
function coverMaxHeight(meta) {
  const perLine = 20.5;                                     // 22pt 글자 기준 본문 폭에 들어가는 em 수
  const titleLines = meta.title_lines.reduce((n, t) => n + Math.max(1, Math.ceil(emWidth(t) / perLine)), 0);
  const subLines = meta.subtitle ? Math.max(1, Math.ceil(emWidth(meta.subtitle) / 32)) : 0;
  const used = 40 + titleLines * 44 + 14 + (subLines ? subLines * 28 + 14 : 0) + 18 + 19 + 11 + 30;
  return Math.max(240, Math.min(680, PAGE_CONTENT_HEIGHT - used));
}

// ─── 입력 검사 (selfcheck.py 가 더 자세히 봄. 여기서는 빌드를 막는 오류만) ─────────
const BLOCK_REQUIRED = { p: ['text'], fig: ['img', 'caption'], table: ['caption', 'headers', 'rows'],
  box: ['title', 'paras'], quote: ['text'], note: ['text'] };
const isText = v => typeof v === 'string' && v.trim() !== '';

function validate(c) {
  const e = [];
  if (!c || typeof c !== 'object') return ['content.json 최상위가 객체가 아님'];
  const meta = c.meta;
  if (!meta || typeof meta !== 'object') e.push('meta 없음');
  else {
    if (typeof meta.title_lines === 'string') meta.title_lines = [meta.title_lines];
    if (!Array.isArray(meta.title_lines) || meta.title_lines.length < 1 || meta.title_lines.length > 2 ||
      !meta.title_lines.every(isText)) e.push('meta.title_lines : 1~2줄 문자열 목록');
    if (meta.lang !== undefined && !['kr', 'en'].includes(meta.lang)) e.push('meta.lang : kr 또는 en');
    if (meta.date && !parseDate(meta.date)) e.push('meta.date 를 읽을 수 없음 : ' + meta.date);
  }
  const es = c.es;
  if (!es || !isText(es.key_message) || !isText(es.background)) e.push('es.key_message, es.background 필요');
  if (!es || !Array.isArray(es.flow) || !es.flow.length ||
    !es.flow.every(x => Array.isArray(x) && x.length === 2 && isText(x[0]) && isText(x[1]))) {
    e.push('es.flow : [[라벨, 문장], ...]');
  }
  if (!es || !(isText(es.next) || isText(es.outlook))) e.push('es.next(또는 outlook) 필요');
  if (c.qa !== undefined && (!Array.isArray(c.qa) || !c.qa.every(x => x && isText(x.q) && isText(x.a)))) {
    e.push('qa : [{q, a}, ...]');
  }
  if (!Array.isArray(c.chapters) || !c.chapters.length) e.push('chapters : 장이 하나 이상 필요');
  else c.chapters.forEach((ch, ci) => {
    const cl = `chapters[${ci}]`;
    if (!ch || !isText(ch.title)) e.push(cl + '.title 없음');
    if (!ch || !Array.isArray(ch.sections)) { e.push(cl + '.sections 목록 필요'); return; }
    ch.sections.forEach((s, si) => {
      const sl = `${cl}.sections[${si}]`;
      if (!s || !isText(s.title)) e.push(sl + '.title 없음');
      if (!s || !Array.isArray(s.blocks)) { e.push(sl + '.blocks 목록 필요'); return; }
      s.blocks.forEach((b, bi) => {
        const bl = `${sl}.blocks[${bi}]`;
        if (!b || !BLOCK_REQUIRED[b.type]) { e.push(`${bl} : 알 수 없는 type ${b && b.type}`); return; }
        for (const k of BLOCK_REQUIRED[b.type]) {
          if (b[k] === undefined || b[k] === null || b[k] === '' || (Array.isArray(b[k]) && !b[k].length)) {
            e.push(`${bl}(${b.type}) : ${k} 없음`);
          }
        }
        if (b.type === 'table' && Array.isArray(b.headers) && Array.isArray(b.rows)) {
          b.rows.forEach((r, ri) => {
            if (!Array.isArray(r) || r.length !== b.headers.length) e.push(`${bl}(table) : rows[${ri}] 칸 수가 headers 와 다름`);
          });
          if (b.widths !== undefined && b.widths !== null &&
            (!Array.isArray(b.widths) || b.widths.length !== b.headers.length || !b.widths.every(w => Number.isFinite(w) && w > 0))) {
            e.push(`${bl}(table) : widths 는 열 수만큼의 양수`);
          }
        }
        if (b.type === 'box' && !Array.isArray(b.paras)) e.push(`${bl}(box) : paras 는 목록`);
      });
    });
  });
  if (c.devils !== undefined && c.devils !== null) {
    const d = c.devils;
    if (!isText(d.title) || !Array.isArray(d.items) || !d.items.length ||
      !d.items.every(x => x && isText(x.claim) && isText(x.counter))) e.push('devils : {title, items:[{claim, counter}]}');
  }
  if (!c.closing || !isText(c.closing.key_sentence)) e.push('closing.key_sentence 필요');
  if (c.references !== undefined && (!Array.isArray(c.references) || !c.references.every(r => r && isText(r.text)))) {
    e.push('references : [{text, url}, ...]');
  }
  return e;
}

// ─── 메인 ────────────────────────────────────────────────────────────────────
let content;
try { content = JSON.parse(fs.readFileSync(CONTENT_PATH, 'utf8')); } catch (e) {
  die(EXIT_INPUT, `[오류] content.json 을 읽지 못함 (${CONTENT_PATH}) : ${e.message}`);
}
{
  const errs = validate(content);
  if (errs.length) die(EXIT_INPUT, '[오류] content.json 형식 오류 ' + errs.length + '건\n  ' + errs.join('\n  '));
  const left = JSON.stringify(content).match(PLACEHOLDER_RE);
  if (left) {
    die(EXIT_PROFILE, '[오류] 원고에 프로필 자리표시가 남아 있음 : ' + [...new Set(left)].join(' ') +
      '\n  원고에는 작성자 정보를 쓰지 않음. 표지 작성자 줄은 build_docx.js 가 profile.json 에서 채움');
  }
}
const { prof, from: PROFILE_FROM } = loadProfile();
const D = loadDocx();
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, Table, TableRow, TableCell, WidthType,
  BorderStyle, AlignmentType, VerticalAlign, ShadingType, UnderlineType, ExternalHyperlink, Footer,
  PageNumber, TableLayoutType,
} = D;

const meta = content.meta;
const LANG = meta.lang === 'en' ? 'en' : 'kr';
const BASE_DIR = path.dirname(CONTENT_PATH);
const F = LANG === 'en'
  ? { ascii: 'Arial', eastAsia: 'Arial', hAnsi: 'Arial' }
  : { ascii: 'Malgun Gothic', eastAsia: 'Malgun Gothic', hAnsi: 'Malgun Gothic' };
const L = {
  kr: { qa: '핵심 질문과 답변', bg: '■ 배경', flow: '■ 핵심 구조 흐름', next: '■ 다음 단계', outlook: '■ 전망',
    closing: '맺음말', key: '핵심 문장', persp: '관점별로 확인할 것', kw: '핵심 키워드', refs: '참고 자료',
    fig: '그림', tbl: '표', src: '출처' },
  en: { qa: 'Key Questions & Answers', bg: '■ Background', flow: '■ Core Structure', next: '■ Next Steps',
    outlook: '■ Outlook', closing: 'Conclusion', key: 'Key Sentence', persp: 'Stakeholder Perspectives',
    kw: 'Core Keywords', refs: 'References', fig: 'Figure', tbl: 'Table', src: 'Source' },
}[LANG];

const NAVY = '1A3A6B', DARK = '333333', GREY = '777777', HEAD_FILL = '3A3A3A';
const str = v => (v === undefined || v === null) ? '' : String(v);
const N = (t, sz, c) => new TextRun({ text: str(t), size: sz || 22, font: F, color: c || '000000' });
const B = (t, sz, c) => new TextRun({ text: str(t), bold: true, size: sz || 22, font: F, color: c || '000000' });
const P = (...runs) => new Paragraph({ children: runs, spacing: { before: 0, after: 200 } });
const BK = () => new Paragraph({ children: [], spacing: { before: 0, after: 80 } });
const H1 = (t) => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 28, font: F, color: NAVY })],
  heading: HeadingLevel.HEADING_1, pageBreakBefore: true, keepNext: true, spacing: { before: 360, after: 160 },
});
const H2 = (t) => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 24, font: F, color: DARK })],
  heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 280, after: 120 },
});
// 번호는 여기서만 붙임 : 「1. 제목」, 「1.1 제목」
let chNo = 0, secNo = 0, figNo = 0, tblNo = 0;
const H1C = (t) => { chNo += 1; secNo = 0; return H1(`${chNo}. ${t}`); };
const H2C = (t) => { secNo += 1; return H2(`${chNo}.${secNo} ${t}`); };
const SL = (label) => new Paragraph({
  children: [new TextRun({ text: label, bold: true, size: 22, font: F, color: NAVY })],
  spacing: { before: 120, after: 60 },
});
const CIRCLED = n => (n >= 1 && n <= 20) ? String.fromCharCode(0x2460 + n - 1) : `(${n})`;

function textBox(title, children) {
  const head = title ? [new Paragraph({
    children: [new TextRun({ text: title, bold: true, size: 24, font: F, color: NAVY })],
    spacing: { before: 0, after: 120 },
  })] : [];
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: [TABLE_WIDTH],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 8, color: NAVY },
      bottom: { style: BorderStyle.SINGLE, size: 3, color: 'CCCCCC' },
      left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
      right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
      insideHorizontal: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
      insideVertical: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
    },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: TABLE_WIDTH, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: 'F0F4FA', color: 'auto' },
      margins: { top: 250, right: 500, bottom: 250, left: 500 },
      verticalAlign: VerticalAlign.TOP,
      children: [...head, ...children],
    })] })],
  });
}

function colWidths(b) {
  const n = b.headers.length;
  let w = Array.isArray(b.widths) && b.widths.length === n ? b.widths.map(Number) : null;
  if (!w) {
    w = Array(n).fill(Math.floor(TABLE_WIDTH / n));
  } else {
    const sum = w.reduce((a, x) => a + x, 0);
    if (sum !== TABLE_WIDTH) {
      console.warn(`[경고] 표 「${str(b.caption).slice(0, 20)}」 widths 합 ${sum} → ${TABLE_WIDTH} 로 비율 조정 (selfcheck table 항목)`);
      w = w.map(x => Math.floor(x * TABLE_WIDTH / sum));
    }
  }
  w[w.length - 1] += TABLE_WIDTH - w.reduce((a, x) => a + x, 0);
  return w;
}

function dataTable(b) {
  const widths = colWidths(b);
  const cell = (text, i, isHead) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: isHead ? HEAD_FILL : 'FFFFFF', color: 'auto' },
    margins: { top: isHead ? 100 : 80, right: 160, bottom: isHead ? 100 : 80, left: 160 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ children: [isHead ? B(text, 19, 'FFFFFF') : N(text, 19, DARK)] })],
  });
  const line = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
  const inner = { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' };
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    layout: TableLayoutType.FIXED,
    borders: { top: line, bottom: line, left: line, right: line, insideHorizontal: inner, insideVertical: inner },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: b.headers.map((h, i) => cell(str(h), i, true)) }),
      ...b.rows.map(r => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(str(c), i, false)) })),
    ],
  });
}

function resolveImg(p, where) {
  const abs = path.isAbsolute(p) ? p : path.resolve(BASE_DIR, p);
  if (!fs.existsSync(abs)) die(EXIT_INPUT, `[오류] ${where} 그림 파일 없음 : ${p} (content.json 폴더 기준 ${abs})`);
  let size;
  try { size = pngSize(abs); } catch (e) { die(EXIT_INPUT, `[오류] ${where} 그림 ${p} : ${e.message} (PNG 만 씀)`); }
  return { data: fs.readFileSync(abs), size };
}

function imagePara(img, box, keepNext) {
  return new Paragraph({
    children: [new ImageRun({ type: 'png', data: img.data, transformation: { width: box.width, height: box.height } })],
    alignment: AlignmentType.CENTER, keepNext: !!keepNext, spacing: { before: 120, after: 80 },
  });
}

const sourceLine = (s, align) => new Paragraph({
  children: [N(`${L.src}: ${s}`, 17, GREY)],
  alignment: align || AlignmentType.LEFT, spacing: { before: 60, after: 200 },
});

function renderBlock(b, where) {
  const out = [];
  switch (b.type) {
    case 'p':
      out.push(P(N(b.text)));
      break;
    case 'note':
      out.push(new Paragraph({ children: [N(b.text, 18, GREY)], spacing: { before: 0, after: 160 } }));
      break;
    case 'quote':
      out.push(new Paragraph({
        children: [N(b.text, 22, DARK)],
        indent: { left: 400 },
        border: { left: { style: BorderStyle.SINGLE, size: 18, color: '8A8A8A', space: 10 } },
        spacing: { before: 60, after: b.sub ? 40 : 200 },
        keepNext: !!b.sub,
      }));
      if (b.sub) {
        out.push(new Paragraph({ children: [N(b.sub, 18, GREY)], indent: { left: 400 }, spacing: { before: 0, after: 200 } }));
      }
      break;
    case 'box':
      out.push(textBox(str(b.title), (b.paras || []).map(t => P(N(t)))), BK());
      break;
    case 'fig': {
      figNo += 1;
      const img = resolveImg(b.img, `${where} [${L.fig} ${figNo}]`);
      out.push(imagePara(img, fitBox(img.size.w, img.size.h, FIG_WIDTH, FIG_MAX_HEIGHT), true));
      out.push(new Paragraph({
        children: [B(`[${L.fig} ${figNo}] ${b.caption}`, 20, DARK)],
        alignment: AlignmentType.CENTER, keepNext: !!b.source, spacing: { before: 0, after: b.source ? 40 : 200 },
      }));
      if (b.source) out.push(sourceLine(b.source, AlignmentType.CENTER));
      break;
    }
    case 'table': {
      tblNo += 1;
      out.push(new Paragraph({
        children: [B(`[${L.tbl} ${tblNo}] ${b.caption}`, 20, DARK)],
        alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 80 },
      }));
      out.push(dataTable(b));
      out.push(b.source ? sourceLine(b.source) : BK());
      break;
    }
    default:
      die(EXIT_INPUT, `[오류] ${where} 알 수 없는 블록 ${b.type}`);
  }
  return out;
}

// ─── 문서 조립 ───────────────────────────────────────────────────────────────
const children = [];
const ymd = meta.date ? parseDate(meta.date) : (() => { const t = new Date(); return [t.getFullYear(), t.getMonth() + 1, t.getDate()]; })();
const DATE_TEXT = formatDate(ymd, LANG);
const AUTHOR_LABEL = isText(meta.author_label) ? meta.author_label.trim() : '작성';

// 표지 : 제목 줄 + 날짜와 작성자 줄 + 표지 그림 (한 쪽)
meta.title_lines.forEach((t, i) => children.push(new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 44, font: F, color: NAVY })],
  alignment: AlignmentType.CENTER,
  spacing: { before: i === 0 ? 600 : 0, after: i === meta.title_lines.length - 1 ? 200 : 0 },
})));
if (isText(meta.subtitle)) {
  children.push(new Paragraph({
    children: [new TextRun({ text: meta.subtitle, size: 28, font: F, color: DARK })],
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 200 },
  }));
}
children.push(new Paragraph({
  children: [N(`${DATE_TEXT} | ${AUTHOR_LABEL}: ${prof.AUTHOR_EN} (${prof.AUTHOR_KR})`, 18, '555555')],
  alignment: AlignmentType.CENTER, spacing: { before: 0, after: 280 },
}));
if (isText(meta.cover_img)) {
  const img = resolveImg(meta.cover_img, '표지');
  children.push(imagePara(img, fitBox(img.size.w, img.size.h, FIG_WIDTH, coverMaxHeight(meta)), false));
}

// Executive Summary
const es = content.es;
children.push(H1('Executive Summary'));
const esKids = [SL('■ Key Message'), P(N(es.key_message)), SL(L.bg), P(N(es.background)), SL(L.flow)];
es.flow.forEach(([label, text], i) => esKids.push(P(B(`${CIRCLED(i + 1)} ${label}: `), N(text))));
if (isText(es.next)) esKids.push(SL(L.next), P(N(es.next)));
else esKids.push(SL(L.outlook), P(N(es.outlook)));
children.push(textBox(null, esKids), BK());

// 핵심 질문과 답변
const qa = Array.isArray(content.qa) ? content.qa : [];
if (qa.length) {
  children.push(H1(L.qa));
  const kids = [];
  qa.forEach((x, i) => {
    if (i) kids.push(BK());
    kids.push(new Paragraph({ children: [B(`Q${i + 1}. ${x.q}`, 22, NAVY)], keepNext: true, spacing: { before: 0, after: 120 } }));
    kids.push(P(N(`A. ${x.a}`)));
  });
  children.push(textBox(null, kids), BK());
}

// 본문 장
content.chapters.forEach((ch) => {
  children.push(H1C(ch.title));
  (ch.intro || []).forEach(t => children.push(P(N(t))));
  ch.sections.forEach((s) => {
    children.push(H2C(s.title));
    if (isText(s.key_message)) children.push(textBox('KEY MESSAGE', [P(N(s.key_message))]), BK());
    s.blocks.forEach((b, bi) => children.push(...renderBlock(b, `${chNo}.${secNo} 블록${bi + 1}`)));
  });
});

// 반론 장 (번호 장)
const dv = content.devils;
if (dv) {
  children.push(H1C(dv.title));
  (dv.intro || []).forEach(t => children.push(P(N(t))));
  dv.items.forEach((it, i) => children.push(textBox(`${CIRCLED(i + 1)} ${it.claim}`, [P(N(it.counter))]), BK()));
}

// 맺음말
const cl = content.closing;
const closingTitle = isText(cl.title)
  ? (cl.title.toLowerCase().includes(L.closing.toLowerCase()) ? cl.title : `${L.closing}: ${cl.title}`)
  : L.closing;
children.push(H1(closingTitle));
children.push(textBox(L.key, [P(B(cl.key_sentence, 22, DARK))]), BK());
(cl.paras || []).forEach(t => children.push(P(N(t))));
if (Array.isArray(cl.perspectives) && cl.perspectives.length) {
  children.push(H2(isText(cl.perspectives_title) ? cl.perspectives_title : L.persp));
  cl.perspectives.forEach(([label, text]) => children.push(P(B(`${label}: `), N(text))));
}
if (Array.isArray(cl.keywords) && cl.keywords.length) {
  children.push(H2(L.kw));
  children.push(P(N(cl.keywords.map(k => (String(k).startsWith('#') ? k : '#' + k)).join(', '))));
}
const refs = Array.isArray(content.references) ? content.references : [];
if (refs.length) {
  children.push(H2(L.refs));
  refs.forEach((r, i) => {
    const label = N(`[${i + 1}] `, 20, DARK);
    const body = isText(r.url)
      ? new ExternalHyperlink({ link: r.url, children: [new TextRun({ text: r.text, size: 20, font: F, color: '0563C1',
        underline: { type: UnderlineType.SINGLE, color: '0563C1' } })] })
      : N(r.text, 20, DARK);
    children.push(new Paragraph({ children: [label, body], spacing: { before: 0, after: 120 } }));
  });
}

const doc = new Document({
  creator: prof.AUTHOR_EN,
  lastModifiedBy: prof.AUTHOR_EN,
  title: meta.title_lines.join(' '),
  description: 'report-harness build_docx.js',
  styles: {
    default: {
      document: { run: { font: F, size: 22 } },
      heading1: { run: { font: F, size: 28, bold: true, color: NAVY }, paragraph: { spacing: { before: 360, after: 160 } } },
      heading2: { run: { font: F, size: 24, bold: true, color: DARK }, paragraph: { spacing: { before: 280, after: 120 } } },
    },
  },
  sections: [{
    properties: {
      titlePage: true,
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1701, right: 1440, bottom: 1440, left: 1440 } },
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ children: [PageNumber.CURRENT], size: 18, font: F, color: '888888' }),
          new TextRun({ text: ' / ', size: 18, font: F, color: '888888' }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: F, color: '888888' }),
        ],
        spacing: { before: 120, after: 120 },
      })] }),
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, buf);
  const nSec = content.chapters.reduce((n, ch) => n + ch.sections.length, 0);
  console.log(`[build_docx] ${OUT_PATH} (${Math.round(buf.length / 1024)} KB)`);
  console.log(`  언어 ${LANG}, 장 ${content.chapters.length}${dv ? ' + 반론 장 1' : ''}, 절 ${nSec}, 그림 ${figNo}, 표 ${tblNo}, ` +
    `질문 ${qa.length}, 참고 자료 ${refs.length}`);
  console.log(`  표지 : ${DATE_TEXT} | ${AUTHOR_LABEL}: ${prof.AUTHOR_EN} (${prof.AUTHOR_KR})`);
  console.log(`  프로필 : ${PROFILE_FROM}`);
  console.log('다음 : python3 <generate-full-report>/references/gate_report.py --docx ' +
    path.basename(OUT_PATH) + ` --lang ${LANG} --skill-dir <generate-full-report>/references --claims claims.json --out gate.json`);
}).catch((err) => {
  die(EXIT_INPUT, '[오류] docx 생성 실패 : ' + (err && err.stack || err));
});
