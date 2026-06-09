#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_content.py — 내용 품질 게이트 (deterministic content eValuation)

verify_toc.py 가 '구조(TOC ↔ 본문 챕터)'를 검사한다면, 이 스크립트는 '내용 품질'을
LLM 없이 규칙 기반으로 채점한다. 결정론적으로 잡을 수 있는 위반만 본다.

검사 항목 (SKILL.md ANTI-DRIFT / WRODING 프롬프팅에서 유래):
  [E] HYPE_HARD   과장 형용사(혁명적/압도적/유일무이 ...)            -> ERROR
  [W] HYPE_SOFT   완화 대상 형용사(가장/최고/근본적 ...)             -> WARNING(빈도)
  [E] BULLET      Word 본문 bullet 문자(•▪‣ 등) — docx 전용          -> ERROR
  [E] CJK_KR      한글문서 본문의 '괄호 밖' 독립 한자/가나 토큰        -> ERROR
  [W] CJK_EN      영문문서 본문의 pinyin 없는 단독 中文                -> WARNING
  [W] KEYMSG      PPTX content 슬라이드에 KEY MESSAGE(임./음.) 부재    -> WARNING
  [W] SOURCE      문서 끝 출처/Source 섹션 부재                       -> WARNING
  [E] HEADNUM     Word 챕터 헤딩 번호(1. / 1.1) 누락·순서 오류 — docx  -> ERROR (v0.9.1)

입력(택1): --unpacked unpacked_kr/  |  --docx report.docx
공통: --lang kr|en  --json gate_content.json  --judge-extract judge_in.json
종료코드: ERROR>=1 -> 1, 아니면 0.
"""
import sys, os, re, json, zipfile, argparse
import xml.etree.ElementTree as ET

NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

HYPE_HARD_KR = ['혁명적', '혁명을', '압도적', '전무후무', '유일무이', '독보적',
                '궁극의', '궁극적', '세계 최초', '세계최초', '초유의', '미증유']
HYPE_SOFT_KR = ['가장', '최고', '최고의', '근본적', '단연', '무한한', '완벽한', '완벽히']
HYPE_HARD_EN = ['revolutionary', 'unprecedented', 'unparalleled', 'world-first',
                'world first', 'game-changing', 'game changer', 'paradigm shift',
                'paradigm-shift', 'best-in-class', 'second to none']
HYPE_SOFT_EN = ['ultimate', 'cutting-edge', 'state-of-the-art', 'most advanced']

BULLET_CHARS = ['•', '▪', '‣', '◦', '·', '●', '∙', '￭']
CJK_RE = re.compile(r'[㐀-䶿一-鿿぀-ゟ゠-ヿ]+')
KEYMSG_RE = re.compile(r'(임|음)\.\s*$')
SOURCE_HINT = ['출처', 'source', 'sources', 'references', '참고문헌']


def slides_from_unpacked(base):
    d = os.path.join(base.rstrip('/'), 'ppt', 'slides')
    if not os.path.isdir(d):
        sys.stderr.write('ERROR: %s 없음\n' % d); sys.exit(2)
    out = {}
    for fn in os.listdir(d):
        m = re.match(r'slide(\d+)\.xml$', fn)
        if not m:
            continue
        root = ET.parse(os.path.join(d, fn)).getroot()
        out[int(m.group(1))] = [(t.text or '') for t in root.iter('%st' % NS_A)]
    return dict(sorted(out.items()))


def runs_from_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml')
    root = ET.fromstring(xml)
    return [(t.text or '') for t in root.iter('%st' % NS_W)]



H1_NUM_RE = re.compile(r'^(\d+)\.\s+\S')
H2_NUM_RE = re.compile(r'^(\d+)\.(\d+)\s+\S')
# 번호를 강제하지 않는 특수 H1/H2 (정본 고정 섹션)
HEAD_EXEMPT = ['executive summary', '핵심 질문', 'key question', '맺음말', 'conclusion',
               '참고 자료', 'references', '핵심 키워드', 'core keyword', '관점별', 'stakeholder']


def headings_from_docx(path):
    """document.xml 에서 (스타일, 텍스트) 헤딩 목록을 문서 순서로 추출."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    out = []
    for p in root.iter('%sp' % NS_W):
        style = None
        ppr = p.find('%spPr' % NS_W)
        if ppr is not None:
            ps = ppr.find('%spStyle' % NS_W)
            if ps is not None:
                style = ps.get('%sval' % NS_W)
        if style in ('Heading1', 'Heading2'):
            txt = ''.join((t.text or '') for t in p.iter('%st' % NS_W)).strip()
            if txt:
                out.append((style, txt))
    return out


def check_docx_headings(path, errors, warnings):
    """v0.9.1: 챕터 헤딩 번호 체계(1. / 1.1) 검사 — H1C/H2C 드리프트 게이트."""
    heads = headings_from_docx(path)
    h1_nums, cur_h1 = [], None
    for style, txt in heads:
        low = txt.lower()
        exempt = any(k in low for k in HEAD_EXEMPT)
        if style == 'Heading1':
            m = H1_NUM_RE.match(txt)
            if m:
                cur_h1 = int(m.group(1)); h1_nums.append(cur_h1)
            else:
                cur_h1 = None
                if not exempt:
                    errors.append({'type': 'HEADNUM', 'loc': 'H1:%s' % txt[:30],
                                   'detail': '챕터 H1 번호 없음',
                                   'fix': "H1C() 헬퍼 사용 — '1. %s' 형태로 자동 번호" % txt[:20]})
        else:  # Heading2
            m = H2_NUM_RE.match(txt)
            if m:
                if cur_h1 is not None and int(m.group(1)) != cur_h1:
                    errors.append({'type': 'HEADNUM', 'loc': 'H2:%s' % txt[:30],
                                   'detail': '소제목 번호 %s.%s 가 챕터 %s 와 불일치'
                                             % (m.group(1), m.group(2), cur_h1),
                                   'fix': 'H2C() 헬퍼 사용 — 챕터 카운터와 자동 동기화'})
            elif cur_h1 is not None and not exempt:
                errors.append({'type': 'HEADNUM', 'loc': 'H2:%s' % txt[:30],
                               'detail': '소제목 H2 번호(%d.x) 없음' % cur_h1,
                               'fix': "H2C() 헬퍼 사용 — '%d.1 %s' 형태" % (cur_h1, txt[:20])})
    if len(heads) >= 4 and not h1_nums:
        errors.append({'type': 'HEADNUM', 'loc': 'docx', 'detail': '번호 달린 챕터 H1 이 0개',
                       'fix': '본문 챕터 전부 H1C()/H2C() 로 작성 (build 템플릿 헬퍼)'})
    if h1_nums != sorted(h1_nums) or (h1_nums and h1_nums != list(range(1, len(h1_nums) + 1))):
        errors.append({'type': 'HEADNUM', 'loc': 'docx',
                       'detail': '챕터 번호 순서 오류: %s' % h1_nums,
                       'fix': '1..N 연속 증가하도록 H1C() 사용'})


def _bare_cjk_tokens(text):
    bare = []
    for m in CJK_RE.finditer(text):
        before = text[max(0, m.start() - 1): m.start()]
        if before not in ('(', '（', '/', '·', '，'):
            bare.append(m.group(0))
    return bare


def check_texts(loc, texts, lang, errors, warnings, kind):
    joined = '\n'.join(texts)
    hard = HYPE_HARD_KR if lang == 'kr' else HYPE_HARD_EN
    soft = HYPE_SOFT_KR if lang == 'kr' else HYPE_SOFT_EN
    low = joined.lower()

    for w in hard:
        if (w in joined) or (lang == 'en' and w.lower() in low):
            errors.append({'type': 'HYPE_HARD', 'loc': loc, 'detail': w,
                           'fix': '과장 형용사 "%s" 제거 -> 객관·수치 기반 표현' % w})
    for w in soft:
        n = joined.count(w) if lang == 'kr' else low.count(w.lower())
        if n:
            warnings.append({'type': 'HYPE_SOFT', 'loc': loc, 'detail': '%s x%d' % (w, n),
                             'fix': '"%s" %d회 — 필요한 곳만 남기고 축소' % (w, n)})

    if kind == 'docx':
        for ch in BULLET_CHARS:
            if ch in joined:
                errors.append({'type': 'BULLET', 'loc': loc, 'detail': ch,
                               'fix': 'Word 본문 bullet "%s" 제거 -> 산문 3~4 단락' % ch})

    if lang == 'kr':
        for t in texts:
            for tok in _bare_cjk_tokens(t):
                errors.append({'type': 'CJK_KR', 'loc': loc, 'detail': tok,
                               'fix': '괄호 밖 한자/가나 "%s" -> 한글 번역(첫등장만 한글(原文))' % tok})
    else:
        for t in texts:
            for m in CJK_RE.finditer(t):
                ctx = t[max(0, m.start() - 12): m.end() + 2]
                if not re.search(r'[A-Za-zÀ-ɏ]', ctx):
                    warnings.append({'type': 'CJK_EN', 'loc': loc, 'detail': m.group(0),
                                     'fix': '영문본 단독 中文 "%s" -> English (Pinyin, 中文)' % m.group(0)})


def run(args):
    errors, warnings, judge_dump = [], [], {}

    if args.unpacked:
        slides = slides_from_unpacked(args.unpacked)
        last = max(slides) if slides else 0
        for n, texts in slides.items():
            judge_dump['slide%d' % n] = texts
            kind = 'pptx_meta' if n <= 2 or n == last else 'pptx_body'
            check_texts('slide%d' % n, texts, args.lang, errors, warnings, kind)
            if kind == 'pptx_body':
                if not any(KEYMSG_RE.search(t.strip()) for t in texts):
                    warnings.append({'type': 'KEYMSG', 'loc': 'slide%d' % n,
                                     'detail': 'KEY MESSAGE 없음',
                                     'fix': 'Zone2에 ~임./~음. 완결 통찰문 1줄 추가'})
        tail = ' '.join(slides.get(last, []) + slides.get(last - 1, [])).lower()
        if not any(h in tail for h in SOURCE_HINT):
            warnings.append({'type': 'SOURCE', 'loc': 'pptx-tail', 'detail': 'Source 미검출',
                             'fix': '본문 Zone5/말미에 출처 표기 확인'})
    elif args.docx:
        texts = runs_from_docx(args.docx)
        judge_dump['docx'] = texts
        check_texts(os.path.basename(args.docx), texts, args.lang, errors, warnings, 'docx')
        check_docx_headings(args.docx, errors, warnings)
        if not any(h in '\n'.join(texts).lower() for h in SOURCE_HINT):
            warnings.append({'type': 'SOURCE', 'loc': 'docx-tail', 'detail': '출처 섹션 미검출',
                             'fix': '문서 말미 출처명+링크 섹션 추가(WRODING ④)'})
    else:
        sys.stderr.write('ERROR: --unpacked 또는 --docx 필요\n'); sys.exit(2)

    print('─── 내용 품질 게이트: lang=%s ───' % args.lang)
    print('ERROR %d / WARNING %d' % (len(errors), len(warnings)))
    for e in errors:
        print('  ❌ [%s] %s: %s' % (e['type'], e['loc'], e['detail']))
    for w in warnings:
        print('  ⚠️  [%s] %s: %s' % (w['type'], w['loc'], w['detail']))

    report = {'pass': len(errors) == 0, 'lang': args.lang,
              'errors': errors, 'warnings': warnings}
    if args.json:
        json.dump(report, open(args.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('  -> %s' % args.json)
    if args.judge_extract:
        json.dump(judge_dump, open(args.judge_extract, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('  -> %s (LLM-judge 입력)' % args.judge_extract)

    if errors:
        print('\n💥 CONTENT GATE FAILED'); sys.exit(1)
    print('\n✅ CONTENT GATE OK'); sys.exit(0)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--unpacked'); g.add_argument('--docx')
    ap.add_argument('--lang', default='kr', choices=['kr', 'en'])
    ap.add_argument('--json'); ap.add_argument('--judge-extract', dest='judge_extract')
    run(ap.parse_args())
