#!/usr/bin/env python3
"""
verify_lang_purity.py — 산출물 본문 언어 정합성 검증
================================================================
원문이 KR/EN이 아닌 자료(중국어 간체/번체, 일본어 등)에서 보고서를 생성할 때
KR/EN 산출물 본문에 원문 문자가 그대로 남아 있는 드리프트를 잡아낸다.

검사 대상 문자 클래스:
  • CJK Unified Ideographs       U+4E00-U+9FFF  (한자/汉字/漢字)
  • CJK Extension A              U+3400-U+4DBF
  • CJK Compatibility Ideographs U+F900-U+FAFF
  • Hiragana                     U+3040-U+309F  (일본어 ひらがな)
  • Katakana                     U+30A0-U+30FF  (일본어 カタカナ)

규칙 (기본값, 환경변수로 조정 가능):
  KR 본문: kana 0개, hanja(CJK) ≤ LANG_PURITY_KR_HANJA_MAX (기본 10)
            → KR 본문에 한자 병기('인공지능(人工知能)' 같은) 소량 허용
  EN 본문: 위 모든 카테고리 합계 ≤ LANG_PURITY_EN_CJK_MAX (기본 0)
            → 영어 본문에 한자/가나 잔존은 원칙적으로 0건

화이트리스트 (CJK가 있어도 봐주는 컨텍스트):
  • Source: / 출처: / Cite: / 引用: 으로 시작하는 텍스트 (출처 인용 보존)
  • 이메일/전화번호/URL 라인
  • 표지의 저자/매체명 메타데이터 라인

사용법:
  # PPTX (unpacked 디렉터리)
  python3 verify_lang_purity.py --pptx-unpacked unpacked_kr/ kr
  python3 verify_lang_purity.py --pptx-unpacked unpacked_en/ en

  # PPTX (packed .pptx 파일)
  python3 verify_lang_purity.py --pptx EmbodiedAI_KR_Presentation.pptx kr

  # DOCX
  python3 verify_lang_purity.py --docx Report_KR.docx kr
  python3 verify_lang_purity.py --docx Report_EN.docx en

  # 자동 모드: 파일명에 _KR_/_EN_가 있으면 target_lang 자동 추정
  python3 verify_lang_purity.py --auto Report_KR_20260426.docx
"""
import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# ── 문자 분류 ─────────────────────────────────────────────────────
def classify(s: str):
    """문자열 s를 스캔해 (hanja, hiragana, katakana, samples) 반환."""
    hanja = 0
    hira = 0
    kata = 0
    samples = []
    for ch in s:
        cp = ord(ch)
        is_hanja = (
            0x4E00 <= cp <= 0x9FFF
            or 0x3400 <= cp <= 0x4DBF
            or 0xF900 <= cp <= 0xFAFF
        )
        is_hira = 0x3040 <= cp <= 0x309F
        is_kata = 0x30A0 <= cp <= 0x30FF
        if is_hanja:
            hanja += 1
            if len(samples) < 8:
                samples.append(ch)
        elif is_hira:
            hira += 1
            if len(samples) < 8:
                samples.append(ch)
        elif is_kata:
            kata += 1
            if len(samples) < 8:
                samples.append(ch)
    return hanja, hira, kata, ''.join(samples)


# ── 화이트리스트 (검사 제외 컨텍스트) ─────────────────────────────
WHITELIST_PREFIXES = (
    'Source:', 'source:', 'SOURCE:',
    '출처:', '출처 :',
    'Cite:', 'Citation:', '引用:',
    'Reference:', 'References:', '참고:',
)
PHONE_RE  = re.compile(r'\+?\d[\d\-\s]{7,}')
EMAIL_RE  = re.compile(r'[\w\.\-]+@[\w\.\-]+\.\w+')
URL_RE    = re.compile(r'https?://')

def is_whitelisted(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    for p in WHITELIST_PREFIXES:
        if t.startswith(p):
            return True
    if EMAIL_RE.search(t) or URL_RE.search(t):
        return True
    if PHONE_RE.fullmatch(t):
        return True
    return False


# ── 텍스트 추출 ───────────────────────────────────────────────────
def texts_from_pptx_unpacked(unpacked_dir: str):
    """unpacked PPTX의 ppt/slides/*.xml 에서 모든 a:t 추출."""
    slides_dir = os.path.join(unpacked_dir, 'ppt', 'slides')
    out = []
    if not os.path.isdir(slides_dir):
        return out
    for fn in sorted(os.listdir(slides_dir)):
        if not fn.endswith('.xml'):
            continue
        path = os.path.join(slides_dir, fn)
        try:
            tree = ET.parse(path)
            for t in tree.iter(f'{NS_A}t'):
                if t.text:
                    out.append((fn, t.text))
        except ET.ParseError:
            pass
    return out


def texts_from_pptx_packed(pptx_path: str):
    out = []
    with zipfile.ZipFile(pptx_path) as z:
        for name in sorted(z.namelist()):
            if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                try:
                    root = ET.fromstring(z.read(name))
                    for t in root.iter(f'{NS_A}t'):
                        if t.text:
                            out.append((os.path.basename(name), t.text))
                except ET.ParseError:
                    pass
    return out


def texts_from_docx(docx_path: str):
    out = []
    with zipfile.ZipFile(docx_path) as z:
        # document.xml + headers/footers
        candidates = [n for n in z.namelist() if n.endswith('.xml') and (
            n == 'word/document.xml'
            or n.startswith('word/header')
            or n.startswith('word/footer')
        )]
        for name in sorted(candidates):
            try:
                root = ET.fromstring(z.read(name))
                for t in root.iter(f'{NS_W}t'):
                    if t.text:
                        out.append((os.path.basename(name), t.text))
            except ET.ParseError:
                pass
    return out


# ── 메인 검증 ─────────────────────────────────────────────────────
def verify(text_items, target_lang: str, kr_max: int, en_max: int):
    target_lang = target_lang.lower()
    if target_lang not in ('kr', 'en'):
        raise ValueError(f'target_lang must be kr or en, got: {target_lang}')

    total_hanja = 0
    total_hira = 0
    total_kata = 0
    flagged = []  # (source, text, hanja, hira, kata)

    for src, text in text_items:
        if is_whitelisted(text):
            continue
        h, hi, ka, _ = classify(text)
        if h or hi or ka:
            total_hanja += h
            total_hira  += hi
            total_kata  += ka
            flagged.append((src, text, h, hi, ka))

    fail = False
    reasons = []
    if target_lang == 'kr':
        if total_hira > 0 or total_kata > 0:
            fail = True
            reasons.append(f'KR 본문에 일본어 가나(hiragana={total_hira}, katakana={total_kata}) 잔존 — 0개 필요')
        if total_hanja > kr_max:
            fail = True
            reasons.append(f'KR 본문 한자(漢字) {total_hanja}개 > 허용치 {kr_max} (KR_HANJA_MAX)')
    else:  # en
        cjk_total = total_hanja + total_hira + total_kata
        if cjk_total > en_max:
            fail = True
            reasons.append(f'EN 본문 CJK/kana 잔존 {cjk_total}개 > 허용치 {en_max} (EN_CJK_MAX)')

    return fail, reasons, flagged, (total_hanja, total_hira, total_kata)


def render_report(target, target_lang, totals, reasons, flagged, fail):
    print(f'─── verify_lang_purity.py: {target}  (target_lang={target_lang}) ───')
    print(f'한자(CJK)={totals[0]}, 히라가나={totals[1]}, 카타카나={totals[2]}, 화이트리스트 제외 후')
    if flagged:
        print(f'\n⚠ 잔존 문자가 포함된 본문 텍스트 ({len(flagged)}건, 최대 12건 표시):')
        for src, text, h, hi, ka in flagged[:12]:
            preview = text[:80].replace('\n', ' ')
            print(f'  [{src}] hanja={h} hira={hi} kata={ka} :: {preview}')
    if fail:
        print('\n💥 VERIFY FAILED')
        for r in reasons:
            print(f'  • {r}')
    else:
        print('\n✅ VERIFY OK — 언어 정합성 통과')


def parse_args():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--pptx-unpacked', help='unpacked PPTX 디렉터리')
    g.add_argument('--pptx',          help='packed .pptx 파일')
    g.add_argument('--docx',          help='packed .docx 파일')
    g.add_argument('--auto',          help='파일명에서 _KR_/_EN_ 추정')
    p.add_argument('target_lang', nargs='?', default=None, help='kr | en (auto 모드에서는 생략 가능)')
    p.add_argument('--kr-hanja-max', type=int,
                   default=int(os.environ.get('LANG_PURITY_KR_HANJA_MAX', '10')))
    p.add_argument('--en-cjk-max', type=int,
                   default=int(os.environ.get('LANG_PURITY_EN_CJK_MAX', '0')))
    return p.parse_args()


def main():
    args = parse_args()
    target_lang = args.target_lang

    if args.auto:
        path = args.auto
        if target_lang is None:
            base = os.path.basename(path).lower()
            if '_kr_' in base or '/kr/' in base:
                target_lang = 'kr'
            elif '_en_' in base or '/en/' in base:
                target_lang = 'en'
            else:
                print('ERROR: --auto requires _KR_/_EN_ in filename or explicit target_lang')
                sys.exit(2)
        if path.endswith('.pptx'):
            items = texts_from_pptx_packed(path)
            tag = path
        elif path.endswith('.docx'):
            items = texts_from_docx(path)
            tag = path
        else:
            print(f'ERROR: --auto only supports .pptx / .docx, got {path}')
            sys.exit(2)
    elif args.pptx_unpacked:
        items = texts_from_pptx_unpacked(args.pptx_unpacked)
        tag = args.pptx_unpacked
    elif args.pptx:
        items = texts_from_pptx_packed(args.pptx)
        tag = args.pptx
    elif args.docx:
        items = texts_from_docx(args.docx)
        tag = args.docx

    if target_lang is None:
        print('ERROR: target_lang required (kr|en)')
        sys.exit(2)

    fail, reasons, flagged, totals = verify(
        items, target_lang, args.kr_hanja_max, args.en_cjk_max
    )
    render_report(tag, target_lang, totals, reasons, flagged, fail)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
