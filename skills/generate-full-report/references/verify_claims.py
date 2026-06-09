#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_claims.py — Deep Verification 기계 게이트 (v0.9)

claims.json(Claims Ledger)과 빌드 산출물(docx 또는 unpacked pptx)을 대조해
할루시네이션성 수치를 결정론적으로 차단한다. factcheck-pipeline.md 참조.

검사:
  [E] NUM_UNREG     본문 유의미 수치가 ledger 미등록
  [E] REMOVED_LEAK  status=removed claim 텍스트가 본문 잔존
  [E] EST_UNMARKED  estimate claim 수치가 '추정'/'est.' 표기 없이 등장
  [W] NO_URL        verified claim에 url/source 부재
  [E] BAD_STATUS    status 가 verified/estimate/removed 외의 값

사용:
  python3 verify_claims.py --claims claims.json --docx report.docx --lang kr [--json out.json]
  python3 verify_claims.py --claims claims.json --unpacked unpacked_kr --lang kr
종료코드: ERROR>=1 -> 1, 아니면 0.
"""
import sys, os, re, json, zipfile, argparse
import xml.etree.ElementTree as ET

NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# 무시할 수치: 연도 단독(1900~2099), 전화번호, 1자리 소수 아닌 단독 0~12(목차·항번호)
YEAR_RE  = re.compile(r'^(19|20)\d{2}$')
PHONE_RE = re.compile(r'(\+?82|010)[-\d]{8,}')
NUM_RE   = re.compile(r'\d[\d,]*\.?\d*')
EST_KR = ['추정', '전망치', '외삽']
EST_EN = ['est.', 'estimate', 'projected', 'extrapolat']


def texts_from_unpacked(base):
    d = os.path.join(base.rstrip('/'), 'ppt', 'slides')
    out = []
    for fn in sorted(os.listdir(d)):
        if re.match(r'slide\d+\.xml$', fn):
            root = ET.parse(os.path.join(d, fn)).getroot()
            out.append((fn, ' '.join((t.text or '') for t in root.iter(NS_A + 't'))))
    return out


def texts_from_docx(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    paras = []
    for p in root.iter(NS_W + 'p'):
        s = ''.join((t.text or '') for t in p.iter(NS_W + 't'))
        if s.strip():
            paras.append(('docx', s))
    return paras


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

    ledger = json.load(open(a.claims, encoding='utf-8'))
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

    for loc, text in units:
        for v, ctx in significant_numbers(text):
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
