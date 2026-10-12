# -*- coding: utf-8 -*-
"""bundle.py : 슬라이드 PNG 묶음 -> PDF / PPTX / PNG zip (insight-full-report / image-deck 스킬)

- PDF  : img2pdf, 쪽 크기 13.333 x 7.5 in (16:9), 쪽마다 PNG 한 장
- PPTX : python-pptx, 16:9 와이드, 쪽마다 전면 그림 한 장(편집용 PPTX 가 아님)
- zip  : 안의 파일 이름은 {base_name}_NN.png

명령행
    python3 bundle.py --in out/ --name 예시덱 --formats pdf,pptx,zip
    python3 bundle.py --in out/ --name 예시덱 --out dist/ --prefix s

파이썬
    from bundle import bundle
    outs = bundle(png_paths, "예시덱", "dist", formats=("pdf", "pptx", "zip"))
    # -> {"pdf": ".../예시덱_slides.pdf", "pptx": ".../예시덱_slides.pptx", "zip": ".../예시덱_PNG.zip"}

종료코드 : 1 = 입력 오류(PNG 없음 등), 3 = 의존성(img2pdf, python-pptx, Pillow) 없음
"""
import argparse
import datetime
import io
import json
import os
import re
import struct
import sys
import zipfile

# Windows 의 cp949·cp1252 콘솔과 파이프에서도 출력 때문에 멈추지 않게 UTF-8 로 맞춤
for _stdio in (sys.stdout, sys.stderr):
    try:
        _stdio.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

__version__ = "1.0.0"
PAGE_W_IN, PAGE_H_IN = 13.333, 7.5
PPTX_W_EMU, PPTX_H_EMU = 12192000, 6858000   # 13.333 x 7.5 in
FORMATS = ("pdf", "pptx", "zip")
SUFFIX = {"pdf": "_slides.pdf", "pptx": "_slides.pptx", "zip": "_PNG.zip"}


def _need(module, pip_name):
    try:
        return __import__(module)
    except ImportError:
        sys.stderr.write("[image-deck] %s 이(가) 없음. 설치 : python3 -m pip install %s\n" % (pip_name, pip_name))
        raise SystemExit(3)


def png_size(path):
    """PNG 헤더에서 (가로, 세로)를 읽음. PNG 가 아니면 None."""
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def _natural_key(path):
    name = os.path.basename(path)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def collect_pngs(in_dir, prefix="s"):
    """in_dir 안의 {prefix}NN.png 를 번호 순서로 모음(render_all 이 만든 이름 규칙)."""
    pat = re.compile(r"^%s(\d+)\.png$" % re.escape(prefix), re.I)
    files = [os.path.join(in_dir, f) for f in os.listdir(in_dir) if pat.match(f)]
    return sorted(files, key=lambda p: int(pat.match(os.path.basename(p)).group(1)))


def _check_inputs(png_paths):
    if not png_paths:
        raise ValueError("bundle: PNG 가 없음")
    sizes = {}
    for p in png_paths:
        if not os.path.isfile(p):
            raise ValueError("bundle: 파일 없음 : %s" % p)
        s = png_size(p)
        if s is None:
            raise ValueError("bundle: PNG 가 아님 : %s" % p)
        sizes[p] = s
    for p, (w, h) in sizes.items():
        if abs(w * 9 - h * 16) > 16:
            print("  [경고] 16:9 가 아님 %dx%d : %s (쪽에 맞춰 늘어나지 않고 가운데 놓임)" % (w, h, os.path.basename(p)))
    return sizes


def _pdf_pages(data):
    """img2pdf 출력의 쪽 수. 쪽 객체(/Type /Page)를 세고, 없으면 쪽 트리의 /Count 를 읽음. 모르면 0."""
    n = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
    if n:
        return n
    m = re.search(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data, re.S) or \
        re.search(rb"/Count\s+(\d+)[^>]*?/Type\s*/Pages\b", data, re.S)
    return int(m.group(1)) if m else 0


def make_pdf(png_paths, out_path, title=None, author=None):
    img2pdf = _need("img2pdf", "img2pdf")
    _need("PIL", "Pillow")
    from PIL import Image  # 투명 채널이 있는 PNG 를 흰 바탕으로 펴서 넣음
    lay = img2pdf.get_layout_fun((img2pdf.in_to_pt(PAGE_W_IN), img2pdf.in_to_pt(PAGE_H_IN)))
    srcs = []
    for p in png_paths:
        with Image.open(p) as im:
            if im.mode in ("RGB", "L"):
                srcs.append(p)
                continue
            rgba = im.convert("RGBA")
            flat = Image.new("RGB", rgba.size, (255, 255, 255))
            flat.paste(rgba, mask=rgba.split()[3])
            buf = io.BytesIO()
            flat.save(buf, format="PNG", optimize=True)
            srcs.append(buf.getvalue())
    meta = {"creator": "image-deck %s" % __version__, "producer": "img2pdf"}
    if title:
        meta["title"] = title
    if author:
        meta["author"] = author
    try:
        data = img2pdf.convert(srcs, layout_fun=lay, **meta)
    except TypeError:  # 오래된 img2pdf 는 일부 메타데이터 인자를 받지 않음
        data = img2pdf.convert(srcs, layout_fun=lay)
    with open(out_path, "wb") as f:
        f.write(data)
    n = _pdf_pages(data)
    if n == 0:
        print("  [경고] PDF 구조에서 쪽 수를 읽지 못해 대조를 건너뜀 : %s" % os.path.basename(out_path))
        return len(png_paths)
    if n != len(png_paths):
        raise RuntimeError("PDF 쪽 수 %d 이 PNG %d장과 다름" % (n, len(png_paths)))
    return n


def make_pptx(png_paths, out_path, title=None, author=None, alt_texts=None):
    _need("pptx", "python-pptx")
    from pptx import Presentation
    from pptx.util import Emu
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(PPTX_W_EMU), Emu(PPTX_H_EMU)
    blank = prs.slide_layouts[6]
    for i, p in enumerate(png_paths):
        slide = prs.slides.add_slide(blank)
        pic = slide.shapes.add_picture(p, 0, 0, width=Emu(PPTX_W_EMU), height=Emu(PPTX_H_EMU))
        alt = (alt_texts[i] if alt_texts and i < len(alt_texts) else "") or "slide %d" % (i + 1)
        pic._element.nvPicPr.cNvPr.set("descr", re.sub(r"\s+", " ", alt).strip()[:1500])
        pic.name = "slide %d" % (i + 1)
    cp = prs.core_properties
    now = datetime.datetime.now().replace(microsecond=0)
    cp.title = title or ""
    cp.author = author or ""
    cp.last_modified_by = author or ""
    cp.comments = "image-deck %s : one full-slide picture per page" % __version__
    cp.subject, cp.keywords, cp.category = "", "", ""
    cp.revision = 1
    cp.created, cp.modified = now, now
    prs.save(out_path)
    n = len(Presentation(out_path).slides)
    if n != len(png_paths):
        raise RuntimeError("PPTX 쪽 수 %d 이 PNG %d장과 다름" % (n, len(png_paths)))
    return n


def make_zip(png_paths, out_path, base_name):
    width = max(2, len(str(len(png_paths))))
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for i, p in enumerate(png_paths, 1):
            z.write(p, "%s_%0*d.png" % (base_name, width, i))
    with zipfile.ZipFile(out_path) as z:
        return len(z.namelist())


def _safe_base(name):
    b = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", str(name)).strip(" .")
    if not b:
        raise ValueError("bundle: base_name 이 비어 있음")
    return b


def bundle(png_paths, base_name, out_dir, formats=FORMATS, title=None, author=None, alt_texts=None):
    """PNG 목록을 묶음. 반환 : {"pdf": 경로, "pptx": 경로, "zip": 경로} (요청한 형식만)

    png_paths : 쪽 순서대로의 PNG 경로(render_all 반환값을 그대로 넘겨도 됨)
    base_name : 산출물 기본 이름. 파일 = {base}_slides.pdf / {base}_slides.pptx / {base}_PNG.zip
    title, author : PDF·PPTX 메타데이터(생략하면 title=base_name, author 는 비움)
    alt_texts : PPTX 그림마다 넣을 대체 텍스트(쪽 순서). 없으면 「slide N」
    """
    fm = [f.strip().lower() for f in (formats.split(",") if isinstance(formats, str) else formats) if f.strip()]
    bad = [f for f in fm if f not in FORMATS]
    if bad:
        raise ValueError("bundle: 알 수 없는 형식 %s (pdf, pptx, zip)" % ", ".join(bad))
    png_paths = [str(p) for p in png_paths]
    _check_inputs(png_paths)
    base = _safe_base(base_name)
    os.makedirs(out_dir, exist_ok=True)
    outs = {}
    for f in fm:
        path = os.path.join(out_dir, base + SUFFIX[f])
        if f == "pdf":
            n = make_pdf(png_paths, path, title=title or base, author=author)
        elif f == "pptx":
            n = make_pptx(png_paths, path, title=title or base, author=author, alt_texts=alt_texts)
        else:
            n = make_zip(png_paths, path, base)
        outs[f] = path
        print("  %-4s %3d쪽  %7.1f KB  %s" % (f.upper(), n, os.path.getsize(path) / 1024.0, path))
    return outs


def _alt_from_report(in_dir, n):
    """render_all 이 남긴 qa_report.json 의 쪽 글을 PPTX 대체 텍스트로 씀."""
    rep = os.path.join(in_dir, "qa_report.json")
    try:
        with open(rep, encoding="utf-8") as f:
            pages = json.load(f).get("pages", [])
    except (OSError, ValueError):
        return None
    texts = [p.get("text", "") for p in pages]
    return texts if len(texts) == n else None


def main(argv=None):
    ap = argparse.ArgumentParser(description="슬라이드 PNG -> PDF / PPTX(쪽마다 그림 한 장) / PNG zip")
    ap.add_argument("--in", dest="in_dir", required=True, help="PNG 폴더(render_all 의 out_dir)")
    ap.add_argument("--name", required=True, help="산출물 기본 이름(예 : 예시덱)")
    ap.add_argument("--formats", default="pdf,pptx,zip", help="쉼표로 구분 : pdf,pptx,zip (기본 모두)")
    ap.add_argument("--out", dest="out_dir", default=None, help="저장 폴더(기본 : --in 폴더)")
    ap.add_argument("--prefix", default="s", help="PNG 이름 접두어(기본 s : s01.png, s02.png ...)")
    ap.add_argument("--title", default=None, help="PDF·PPTX 제목 메타데이터(기본 : --name)")
    ap.add_argument("--author", default=None, help="PDF·PPTX 작성자 메타데이터(기본 : 비움)")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.in_dir):
        sys.stderr.write("[image-deck] 폴더 없음 : %s\n" % a.in_dir)
        return 1
    pngs = collect_pngs(a.in_dir, a.prefix)
    if not pngs:
        sys.stderr.write("[image-deck] %s 안에 %sNN.png 가 없음 (--prefix 확인)\n" % (a.in_dir, a.prefix))
        return 1
    print("[image-deck bundle] PNG %d장 : %s ... %s" % (len(pngs), os.path.basename(pngs[0]), os.path.basename(pngs[-1])))
    try:
        bundle(pngs, a.name, a.out_dir or a.in_dir, formats=a.formats, title=a.title, author=a.author,
               alt_texts=_alt_from_report(a.in_dir, len(pngs)))
    except (ValueError, RuntimeError) as e:
        sys.stderr.write("[image-deck] %s\n" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
