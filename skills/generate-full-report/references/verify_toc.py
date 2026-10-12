#!/usr/bin/env python3
"""
verify_toc.py: TOC ↔ 본문 챕터 일치 검증

PPTX의 INDEX 슬라이드(보이는 순서로 두 번째, 정본은 slide2)에 나열된 로마숫자 챕터(I~XII)와
본문 슬라이드(z1 헤더의 좌측 텍스트)에서 추출한 챕터 라벨이 1:1로 매칭되는지 검사한다.
슬라이드 순서는 파일 번호가 아니라 presentation.xml 의 sldIdLst(실제 보이는 순서)를 따름.
누락, 순서 불일치, 중복, 빈 슬라이드, 슬라이드 목록 밖의 본문이 있으면 종료코드 1.

사용법:
    python3 verify_toc.py <unpacked_dir>
    python3 verify_toc.py unpacked_kr/
    python3 verify_toc.py unpacked_en/
"""
import sys
import os
import re
import xml.etree.ElementTree as ET

# Windows 의 cp949·cp1252 콘솔과 파이프에서도 출력 때문에 멈추지 않게 UTF-8 로 맞춤
for _stdio in (sys.stdout, sys.stderr):
    try:
        _stdio.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
ROMAN_RE = re.compile(r'^\s*(XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)\.')   # 동적 워크플로 5~9장 + 여유(긴 것부터)


def slide_text_runs(path):
    """슬라이드 XML에서 모든 a:t 텍스트를 슬라이드별 리스트로 반환."""
    tree = ET.parse(path)
    root = tree.getroot()
    return [(t.text or '') for t in root.iter(f'{NS_A}t')]


def _num(fn):
    m = re.search(r'(\d+)', fn)
    return int(m.group(1)) if m else 0


def ordered_slide_files(base):
    """presentation.xml 의 sldIdLst(실제 보이는 순서)대로 슬라이드 파일 이름. 읽지 못하면 파일 번호 순."""
    ppt = os.path.join(base, 'ppt')
    try:
        with open(os.path.join(ppt, 'presentation.xml'), encoding='utf-8') as f:
            pres = f.read()
        with open(os.path.join(ppt, '_rels', 'presentation.xml.rels'), encoding='utf-8') as f:
            rels = f.read()
        rmap = {}
        for tag in re.findall(r'<Relationship\b[^>]*/>', rels):
            i = re.search(r'\bId="([^"]+)"', tag)
            t = re.search(r'\bTarget="([^"]+)"', tag)
            if i and t:
                rmap[i.group(1)] = os.path.basename(t.group(1))
        lst = re.search(r'<p:sldIdLst>(.*?)</p:sldIdLst>', pres, re.S)
        order = [rmap.get(r) for r in re.findall(r'<p:sldId\b[^>]*\br:id="([^"]+)"', lst.group(1))] if lst else []
        order = [o for o in order if o]
        if order:
            return order
    except OSError:
        pass
    d = os.path.join(ppt, 'slides')
    return sorted((f for f in os.listdir(d) if re.match(r'slide\d+\.xml$', f)), key=_num)


def extract_toc_chapters(slides_dir, order):
    """INDEX(보이는 순서로 두 번째 슬라이드)에서 로마숫자로 시작하는 모든 줄을 추출."""
    if len(order) < 2:
        return []
    p = os.path.join(slides_dir, order[1])
    if not os.path.exists(p):
        return []
    chapters = []
    for t in slide_text_runs(p):
        m = ROMAN_RE.match(t)
        if m:
            chapters.append(m.group(1))
    return chapters


def first_roman(path):
    for t in slide_text_runs(path):
        mm = ROMAN_RE.match(t)
        if mm:
            return mm.group(1)
    return None


def extract_content_chapters(slides_dir, order):
    """표지·INDEX 를 뺀 슬라이드를 보이는 순서대로 보고, 각 슬라이드의 첫 로마숫자 라벨을 챕터로 씀."""
    found = {}  # 파일 이름 -> 로마숫자
    for fn in order[2:]:
        r = first_roman(os.path.join(slides_dir, fn))
        if r:
            found[fn] = r
    seq, last = [], None
    for fn in order[2:]:
        ch = found.get(fn)
        if ch and ch != last:
            seq.append(ch)
            last = ch
    return seq, found


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 verify_toc.py <unpacked_dir>')
        sys.exit(2)
    base = sys.argv[1].rstrip('/')
    slides_dir = os.path.join(base, 'ppt', 'slides')
    if not os.path.isdir(slides_dir):
        print(f'ERROR: {slides_dir} not found'); sys.exit(2)

    order = ordered_slide_files(base)
    toc = extract_toc_chapters(slides_dir, order)
    content_seq, content_map = extract_content_chapters(slides_dir, order)

    print(f'─── TOC ↔ 본문 검증: {base} ───')
    print(f'보이는 순서 ({len(order)}장): {" ".join(order)}')
    print(f'TOC 챕터  ({len(toc)}): {toc}')
    print(f'본문 챕터 ({len(content_seq)}): {content_seq}')
    print(f'본문 슬라이드별 챕터: {content_map}')

    errs = []

    # 빈 슬라이드 : 빌드 스크립트가 채우지 않은 슬라이드가 목록에 있음 (N_CONTENT 가 큼)
    blank = [fn for fn in order if not any(t.strip() for t in slide_text_runs(os.path.join(slides_dir, fn)))]
    if blank:
        errs.append(f'❌ 빈 슬라이드 {blank} : N_CONTENT 가 빌드 스크립트의 본문 슬라이드 수보다 큼')
    # 목록 밖 슬라이드 : 빌드 스크립트가 썼지만 sldIdLst 에 없음 (N_CONTENT 가 작음, clean 이 지움)
    on_disk = [f for f in os.listdir(slides_dir) if re.match(r'slide\d+\.xml$', f)]
    lost = sorted((f for f in on_disk if f not in order
                   and any(t.strip() for t in slide_text_runs(os.path.join(slides_dir, f)))), key=_num)
    if lost:
        errs.append(f'❌ 슬라이드 목록에 없는 슬라이드 {lost} : 빌드 스크립트가 썼지만 목록에 없음. '
                    f'N_CONTENT 를 {len(lost)} 늘려 다시 빌드 (지금 묶으면 이 슬라이드가 빠짐)')

    if not toc:
        errs.append('TOC가 비어 있음 (slide2.xml에서 로마숫자 챕터를 찾지 못함)')

    toc_set = set(toc)
    cont_set = set(content_seq)
    missing_in_content = toc_set - cont_set
    extra_in_content = cont_set - toc_set
    if missing_in_content:
        errs.append(f'❌ TOC에는 있지만 본문에 없는 챕터: {sorted(missing_in_content)}')
    if extra_in_content:
        errs.append(f'❌ 본문에는 있지만 TOC에 없는 챕터: {sorted(extra_in_content)}')

    if toc and content_seq and toc != content_seq:
        # 순서 불일치
        if toc_set == cont_set:
            errs.append(f'❌ 챕터 순서 불일치: TOC={toc} vs 본문={content_seq}')

    # TOC 자체 중복 검사
    if len(toc) != len(set(toc)):
        errs.append(f'❌ TOC 내 중복 챕터: {toc}')

    if errs:
        print('\n'.join(errs))
        print('\n💥 VERIFY FAILED')
        sys.exit(1)
    else:
        print(f'\n✅ VERIFY OK: {len(toc)}개 챕터가 TOC와 본문에 모두 정렬되어 있음')
        sys.exit(0)


if __name__ == '__main__':
    main()
