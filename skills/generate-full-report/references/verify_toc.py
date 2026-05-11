#!/usr/bin/env python3
"""
verify_toc.py — TOC ↔ 본문 챕터 일치 검증

PPTX의 INDEX 슬라이드(slide2)에 나열된 로마숫자 챕터(I~VII 등)와
모든 컨텐츠 슬라이드(z1 헤더의 좌측 텍스트)에서 추출한 챕터 라벨이
1:1로 매칭되는지 검사한다. 누락/순서불일치/중복이 있으면 종료코드 1.

사용법:
    python3 verify_toc.py <unpacked_dir>
    python3 verify_toc.py unpacked_kr/
    python3 verify_toc.py unpacked_en/
"""
import sys
import os
import re
import xml.etree.ElementTree as ET

NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
ROMAN_RE = re.compile(r'^\s*((?:VII|VI|IV|V|III|II|I))\.')


def slide_text_runs(path):
    """슬라이드 XML에서 모든 a:t 텍스트를 슬라이드별 리스트로 반환."""
    tree = ET.parse(path)
    root = tree.getroot()
    return [(t.text or '') for t in root.iter(f'{NS_A}t')]


def extract_toc_chapters(slides_dir):
    """slide2.xml에서 로마숫자로 시작하는 모든 줄을 추출."""
    p = os.path.join(slides_dir, 'slide2.xml')
    if not os.path.exists(p):
        return []
    texts = slide_text_runs(p)
    chapters = []
    for t in texts:
        m = ROMAN_RE.match(t)
        if m:
            chapters.append(m.group(1))
    return chapters


def extract_content_chapters(slides_dir):
    """slide2를 제외한 모든 슬라이드에서 z1 좌측 헤더(첫 번째 로마숫자)를 추출.

    각 슬라이드에서 처음 발견되는 로마숫자 라벨 1개만 채택한다.
    """
    found = {}  # slide_num -> roman
    for fn in os.listdir(slides_dir):
        if not fn.startswith('slide') or not fn.endswith('.xml'):
            continue
        m = re.match(r'slide(\d+)\.xml', fn)
        if not m:
            continue
        n = int(m.group(1))
        if n <= 2:
            continue  # 표지/INDEX 제외
        texts = slide_text_runs(os.path.join(slides_dir, fn))
        for t in texts:
            mm = ROMAN_RE.match(t)
            if mm:
                found[n] = mm.group(1)
                break
    # 슬라이드 번호 순으로 정렬, 챕터 라벨만 반환 (중복 제거 — 같은 챕터의 여러 슬라이드 허용)
    seq = []
    last = None
    for n in sorted(found.keys()):
        ch = found[n]
        if ch != last:
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

    toc = extract_toc_chapters(slides_dir)
    content_seq, content_map = extract_content_chapters(slides_dir)

    print(f'─── TOC ↔ 본문 검증: {base} ───')
    print(f'TOC 챕터  ({len(toc)}): {toc}')
    print(f'본문 챕터 ({len(content_seq)}): {content_seq}')
    print(f'본문 슬라이드별 챕터: {content_map}')

    errs = []

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
        print(f'\n✅ VERIFY OK — {len(toc)}개 챕터가 TOC와 본문에 모두 정렬되어 있음')
        sys.exit(0)


if __name__ == '__main__':
    main()
