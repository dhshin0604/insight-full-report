#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_claims.py: Deep Verification 기계 게이트 (v1.0)

claims.json(Claims Ledger)과 빌드 산출물(docx 또는 unpacked pptx)을 대조해
할루시네이션성 수치를 결정론적으로 차단한다. factcheck-pipeline.md 참조.

검사:
  [E] NUM_UNREG     본문 유의미 수치가 ledger 미등록
  [E] REMOVED_LEAK  status=removed claim 텍스트가 본문 잔존
  [E] EST_UNMARKED  estimate claim 수치가 '추정'/'est.' 표기 없이 등장
  [W] NO_URL        verified claim에 url/source 부재
  [E] BAD_STATUS    status 가 verified/estimate/removed 외의 값

수치로 보지 않는 것 (v1.0) : 문서 구조가 만드는 번호와 날짜
  - 연도 단독(1900~2099), 전화번호, 12 이하의 정수(항번호·소량 수사)
  - Word 헤딩 맨 앞의 장·절 번호 : 1. → 1.1 → 1.2 → 2. 처럼 카운터와 맞는 번호만 (목차 줄은 같은 번호일 때만)
  - 캡션 번호 : [표 3], [그림 12], [Table 3], [Figure 12], 질문 번호 Q13.
  - 날짜 : 2026.04.08, 2026-10-12, 2026/10, 2025.12 기준(연.월 뒤에 기준·말·현재 등), 2026년 10월 12일, 10월 12일,
    October 12, 2026, 12 Oct 2026
  사건의 날짜가 맞는지는 원장(claims.json)의 text 와 2차 검증·독립 검토가 맡음

사용:
  python3 verify_claims.py --claims claims.json --docx report.docx --lang kr [--json out.json]
  python3 verify_claims.py --claims claims.json --unpacked unpacked_kr --lang kr
종료코드: ERROR>=1 -> 1, 아니면 0.
"""
import sys, os, re, json, zipfile, argparse
import xml.etree.ElementTree as ET

# Windows 의 cp949·cp1252 콘솔과 파이프에서도 출력 때문에 멈추지 않게 UTF-8 로 맞춤
for _stdio in (sys.stdout, sys.stderr):
    try:
        _stdio.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# 무시할 수치: 연도 단독(1900~2099), 전화번호, 1자리 소수 아닌 단독 0~12(목차·항번호)
YEAR_RE  = re.compile(r'^(19|20)\d{2}$')
PHONE_RE = re.compile(r'(\+?82|010)[-\d]{8,}')
NUM_RE   = re.compile(r'\d[\d,]*\.?\d*')
EST_KR = ['추정', '전망치', '외삽']
EST_EN = ['est.', 'estimate', 'projected', 'extrapolat']


MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?'
          r'|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?(?![A-Za-z])')
DATE_RES = [
    re.compile(r'(?<![\d.])(?:19|20)\d{2}\s*([.\-/])\s*(?:0?[1-9]|1[0-2])\s*\1\s*(?:0?[1-9]|[12]\d|3[01])(?!\d)\.?'),  # 2026.04.08
    # 2025.12 기준 : 연.월(두 자리) 뒤에 날짜를 뜻하는 말이 올 때만 날짜로 봄 (2025.10 TWh 같은 수량은 그대로 검사)
    # 2024.01~2025.12 : 기간 전체(뒤에 단위가 오면 수량 범위이므로 그대로 검사)
    re.compile(r'(?<![\d.])(?:19|20)\d{2}\.(?:0[1-9]|1[0-2])\s*[~〜]\s*(?:19|20)\d{2}\.(?:0[1-9]|1[0-2])(?![\d.%])'
               r'(?!\s*(?:억|조|만|천|원|달러|배|위안|엔|MW|GW|kW|km|kg|t\b))'),
    # 2025.12 기준, 2024.01~현재 : 연.월 뒤에 날짜를 뜻하는 말(또는 숫자가 아닌 ~)이 올 때만
    re.compile(r'(?<![\d.])(?:19|20)\d{2}\.(?:0[1-9]|1[0-2])'
               r'(?=\s*(?:기준(?![치점선])|말|초|중순|현재|발표|출시|공개|시점|부터|까지|이후|이전|[~〜](?!\s*\d)))'),
    re.compile(r'(?<![\d.])(?:19|20)\d{2}[-/](?:0?[1-9]|1[0-2])(?![\d.])'),                                            # 2026-10, 2026/10
    re.compile(r'(?<!\d)(?:19|20)\d{2}\s*년\s*\d{1,2}\s*월(?:\s*\d{1,2}\s*일)?'),               # 2026년 10월 12일
    re.compile(r'(?<!\d)\d{1,2}\s*월\s*\d{1,2}\s*일'),                                          # 10월 12일
    re.compile(r'\b' + MONTHS + r'\s+\d{1,2},?\s+(?:19|20)\d{2}\b', re.I),                      # October 12, 2026
    re.compile(r'\b\d{1,2}\s+' + MONTHS + r',?\s+(?:19|20)\d{2}\b', re.I),                      # 12 Oct 2026
]
CAPTION_RE = re.compile(r'\[\s*(?:표|그림|Table|Figure|Fig\.)\s*\d+\s*\]', re.I)
QNUM_RE = re.compile(r'(?<![A-Za-z0-9])Q\d{1,2}(?=[.:)\s])')   # 핵심 질문 번호 Q1. Q13:
OUTLINE_RE = re.compile(r'^\s*\d+(?:\.\d+)*\.?(?=\s)')
HEADING_STYLE_RE = re.compile(r'^(?:heading|title|toc|subtitle)', re.I)


def outline_paragraphs(paras):
    """장·절 번호 카운터와 맞는 헤딩 문단의 번호만 구조 숫자로 봄 : 1. → 1.1 → 1.2 → 2. → 2.1 ...
    번호 없는 헤딩이 「3.5 GW 시대」처럼 수량으로 시작하면 카운터와 맞지 않으므로 그대로 검사함.
    목차(TOC 스타일) 줄은 앞의 번호가 실제 헤딩 번호와 같을 때만 뺌."""
    keep, seen = set(), set()
    h = [0, 0, 0]
    for idx, (_, text, style) in enumerate(paras):
        st = (style or '').lower().replace(' ', '')
        m = re.match(r'\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?\.?(?=\s)', text)
        if not m or not st.startswith('heading'):
            continue
        nums = [int(x) for x in m.groups() if x is not None]
        level = len(nums)
        if level == 1 and st == 'heading1' and nums[0] == h[0] + 1:
            h = [nums[0], 0, 0]
        elif level == 2 and st == 'heading2' and nums[0] == h[0] and nums[1] == h[1] + 1:
            h = [h[0], nums[1], 0]
        elif level == 3 and st == 'heading3' and nums[:2] == h[:2] and nums[2] == h[2] + 1:
            h = [h[0], h[1], nums[2]]
        else:
            continue
        keep.add(idx)
        seen.add(m.group(0).strip().rstrip('.'))
    for idx, (_, text, style) in enumerate(paras):
        st = (style or '').lower().replace(' ', '')
        m = re.match(r'\s*(\d+(?:\.\d+)*)\.?(?=\s)', text)
        if st.startswith('toc') and m and m.group(1) in seen:
            keep.add(idx)
    return keep


def strip_structural(text, heading=False):
    """수치 검사에서 뺄 것(헤딩 번호, 캡션 번호, 날짜)을 공백으로 바꿈. 위치는 그대로 둠."""
    if heading:
        text = OUTLINE_RE.sub(lambda m: ' ' * len(m.group(0)), text, count=1)
    text = CAPTION_RE.sub(lambda m: ' ' * len(m.group(0)), text)
    text = QNUM_RE.sub(lambda m: ' ' * len(m.group(0)), text)
    for rx in DATE_RES:
        text = rx.sub(lambda m: ' ' * len(m.group(0)), text)
    return text


def texts_from_unpacked(base):
    """[(위치, 텍스트, 헤딩 여부)] : 슬라이드마다 한 덩어리."""
    d = os.path.join(base.rstrip('/\\'), 'ppt', 'slides')
    out = []
    for fn in sorted(os.listdir(d), key=lambda f: int(re.search(r'(\d+)', f).group(1)) if re.search(r'\d+', f) else 0):
        if re.match(r'slide\d+\.xml$', fn):
            root = ET.parse(os.path.join(d, fn)).getroot()
            out.append((fn[:-4], ' '.join((t.text or '') for t in root.iter(NS_A + 't')), False))
    return out


def texts_from_docx(path):
    """[(위치, 문단 텍스트, 장·절 번호를 뺄지)] : 위치는 docx:p{문단 번호}. 번호는 outline_paragraphs 가 고름."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    raw = []
    for i, p in enumerate(root.iter(NS_W + 'p'), 1):
        s = ''.join((t.text or '') for t in p.iter(NS_W + 't'))
        if not s.strip():
            continue
        ps = p.find(NS_W + 'pPr/' + NS_W + 'pStyle')
        style = ps.get(NS_W + 'val', '') if ps is not None else ''
        raw.append(('docx:p%d' % i, s, style))
    keep = outline_paragraphs(raw)
    return [(loc, s, idx in keep) for idx, (loc, s, _) in enumerate(raw)]


def norm(s):
    return s.replace(',', '').rstrip('.')


def significant_numbers(text):
    text = PHONE_RE.sub(' ', text)
    out = []
    for m in NUM_RE.finditer(text):
        v = norm(m.group(0))
        if YEAR_RE.match(v):
            continue
        try:
            f = float(v)
        except ValueError:
            continue
        if f <= 12 and '.' not in v and '%' not in text[m.end():m.end() + 1]:
            continue  # 항번호·소량 수사는 통과
        out.append((v, text[max(0, m.start() - 30): m.end() + 30]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--claims', required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--docx'); g.add_argument('--unpacked')
    ap.add_argument('--lang', default='kr', choices=['kr', 'en'])
    ap.add_argument('--json')
    a = ap.parse_args()

    with open(a.claims, encoding='utf-8-sig') as f:
        ledger = json.load(f)
    claims = ledger.get('claims', [])
    errors, warnings = [], []

    reg_values = set()
    est_values, removed_texts = set(), []
    for c in claims:
        st = c.get('status')
        if st not in ('verified', 'estimate', 'removed'):
            errors.append({'type': 'BAD_STATUS', 'loc': c.get('id', '?'),
                           'detail': str(st), 'fix': 'status는 verified/estimate/removed 만 허용'})
            continue
        vals = NUM_RE.findall(str(c.get('value', ''))) + NUM_RE.findall(c.get('text', ''))
        vals = {norm(v) for v in vals if not YEAR_RE.match(norm(v))}
        if st == 'removed':
            removed_texts.append(c)
        else:
            reg_values |= vals
            if st == 'estimate':
                est_values |= vals
            if st == 'verified' and not (c.get('url') or c.get('source')):
                warnings.append({'type': 'NO_URL', 'loc': c.get('id', '?'),
                                 'detail': c.get('text', '')[:40],
                                 'fix': 'verified claim에 source/url 추가'})

    units = texts_from_docx(a.docx) if a.docx else texts_from_unpacked(a.unpacked)
    est_markers = EST_KR if a.lang == 'kr' else EST_EN

    for loc, text, is_heading in units:
        for v, ctx in significant_numbers(strip_structural(text, is_heading)):
            if v not in reg_values:
                errors.append({'type': 'NUM_UNREG', 'loc': loc, 'detail': '%s … "%s"' % (v, ctx.strip()),
                               'fix': '수치 %s 를 claims.json에 등록·검증하거나 본문에서 제거' % v})
            elif v in est_values and not any(m in ctx.lower() for m in est_markers):
                errors.append({'type': 'EST_UNMARKED', 'loc': loc, 'detail': v,
                               'fix': 'estimate 수치 %s 주변에 추정/est. 표기 추가' % v})
        for c in removed_texts:
            key = norm(str(c.get('value', '')))
            if key and key in norm(text):
                errors.append({'type': 'REMOVED_LEAK', 'loc': loc, 'detail': c.get('id', '?'),
                               'fix': 'removed claim "%s" 본문에서 삭제' % c.get('text', '')[:40]})

    print('─── CLAIMS GATE: %s / claims=%d ───' % (a.docx or a.unpacked, len(claims)))
    print('ERROR %d / WARNING %d' % (len(errors), len(warnings)))
    for e in errors[:30]:
        print('  ❌ [%s] %s: %s' % (e['type'], e['loc'], e['detail']))
    for w in warnings[:10]:
        print('  ⚠️  [%s] %s: %s' % (w['type'], w['loc'], w['detail']))

    report = {'pass': not errors, 'errors': errors, 'warnings': warnings,
              'claims_total': len(claims)}
    if a.json:
        json.dump(report, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('  -> %s' % a.json)
    if errors:
        print('\n💥 CLAIMS GATE FAILED'); sys.exit(1)
    print('\n✅ CLAIMS GATE OK'); sys.exit(0)


if __name__ == '__main__':
    main()
