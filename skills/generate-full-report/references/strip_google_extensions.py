#!/usr/bin/env python3
"""
strip_google_extensions.py — PPTX Google Slides 잔존물 제거

TEMPLATE.pptx가 Google Slides에서 export된 경우 `<p:extLst>` 안에
`GoogleSlidesCustomDataVersion2` 확장이 남아 있어 Microsoft PowerPoint가
"읽을 수 없습니다" 에러로 거부합니다. 이 스크립트는:

1. ppt/presentation.xml 에서 <p:extLst>...</p:extLst> 블록 제거
2. ppt/_rels/presentation.xml.rels 에서 customschemas.google.com 관계 제거
3. [Content_Types].xml 에서 /ppt/metadata Override 제거
4. ppt/metadata (Google ARC binary) 파일 삭제

**두 가지 용도**:
- 이미 팩된 .pptx 파일 전체 정화:
    python3 strip_google_extensions.py input.pptx [output.pptx]
- unpack된 디렉터리 정화 (빌드 파이프라인 중간 단계):
    python3 strip_google_extensions.py --unpacked path/to/unpacked/

빌드 파이프라인(build_pptx_kr.py / build_pptx_en.py)에서는 pack 호출
직전에 반드시 `--unpacked` 모드로 실행해야 합니다.
"""
import os, re, sys, shutil, zipfile, tempfile


def strip_unpacked(root):
    """unpack된 디렉터리 root 내부에서 Google 잔존물 제거. 변경 건수 반환."""
    changed = 0

    pres = os.path.join(root, 'ppt', 'presentation.xml')
    if os.path.exists(pres):
        with open(pres, 'r', encoding='utf-8') as f:
            x = f.read()
        x2 = re.sub(r'<p:extLst>.*?</p:extLst>', '', x, flags=re.DOTALL)
        if x2 != x:
            with open(pres, 'w', encoding='utf-8') as f:
                f.write(x2)
            changed += 1
            print(f'  stripped <p:extLst> from presentation.xml ({len(x)} -> {len(x2)} bytes)')

    rels = os.path.join(root, 'ppt', '_rels', 'presentation.xml.rels')
    if os.path.exists(rels):
        with open(rels, 'r', encoding='utf-8') as f:
            r = f.read()
        r2 = re.sub(
            r'<Relationship[^/]*customschemas\.google\.com[^/]*/>',
            '', r)
        if r2 != r:
            with open(rels, 'w', encoding='utf-8') as f:
                f.write(r2)
            changed += 1
            print(f'  stripped Google relationship from rels ({len(r)} -> {len(r2)} bytes)')

    ct = os.path.join(root, '[Content_Types].xml')
    if os.path.exists(ct):
        with open(ct, 'r', encoding='utf-8') as f:
            c = f.read()
        c2 = re.sub(
            r'<Override[^/]*PartName="/ppt/metadata"[^/]*/>',
            '', c)
        if c2 != c:
            with open(ct, 'w', encoding='utf-8') as f:
                f.write(c2)
            changed += 1
            print(f'  stripped /ppt/metadata Override from Content_Types ({len(c)} -> {len(c2)} bytes)')

    meta = os.path.join(root, 'ppt', 'metadata')
    if os.path.exists(meta):
        os.remove(meta)
        changed += 1
        print(f'  deleted ppt/metadata (Google ARC binary)')

    return changed


def strip_pptx(src, dst=None):
    """src .pptx 전체 파일을 정화하여 dst로 저장. dst=None이면 in-place."""
    if dst is None:
        dst = src
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(src, 'r') as z:
            z.extractall(tmp)
        n = strip_unpacked(tmp)
        print(f'total {n} modifications in {src}')
        # Repack
        tmp_out = dst + '.tmp'
        with zipfile.ZipFile(tmp_out, 'w', zipfile.ZIP_DEFLATED) as z:
            for base, _, files in os.walk(tmp):
                for f in files:
                    full = os.path.join(base, f)
                    rel = os.path.relpath(full, tmp)
                    z.write(full, rel.replace(os.sep, '/'))
        shutil.move(tmp_out, dst)
        print(f'wrote {dst}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)
    if args[0] == '--unpacked':
        if len(args) < 2:
            print('usage: --unpacked <dir>'); sys.exit(1)
        n = strip_unpacked(args[1])
        print(f'done. {n} modifications.')
    else:
        src = args[0]
        dst = args[1] if len(args) > 1 else None
        strip_pptx(src, dst)
