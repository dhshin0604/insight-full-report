#!/usr/bin/env python3
"""render_slides.py - 덱을 장별 PNG와 한 장짜리 contact sheet로 렌더링한다.

사용법:
  python3 render_slides.py deck.pptx out_dir/ [--dpi 110] [--cols 4]
  python3 render_slides.py deck.pdf  out_dir/

필요 도구: LibreOffice(soffice, PPTX일 때), pdftoppm(poppler), Pillow(contact sheet).
출력:
  out_dir/slide-01.png ...   장별 이미지 (눈으로 한 장씩 볼 것)
  out_dir/contact_sheet.png  전 장 축소판 (공통 요소 일관성 확인용)
텍스트 추출 검사는 화면 검수를 대신하지 않는다.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile


def to_pdf(src, workdir):
    if src.lower().endswith('.pdf'):
        return src
    soffice = shutil.which('soffice') or shutil.which('libreoffice')
    if not soffice:
        sys.exit('soffice(LibreOffice)가 없습니다. 설치하거나 PDF로 내보낸 뒤 다시 실행하세요.')
    subprocess.run([soffice, '--headless', '--convert-to', 'pdf', '--outdir', workdir, src],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    pdf = os.path.join(workdir, os.path.splitext(os.path.basename(src))[0] + '.pdf')
    if not os.path.exists(pdf):
        sys.exit('PDF 변환에 실패했습니다: ' + src)
    return pdf


def to_png(pdf, out_dir, dpi):
    if not shutil.which('pdftoppm'):
        sys.exit('pdftoppm(poppler-utils)이 없습니다.')
    subprocess.run(['pdftoppm', '-png', '-r', str(dpi), pdf, os.path.join(out_dir, 'slide')], check=True)
    files = sorted(glob.glob(os.path.join(out_dir, 'slide-*.png')))
    width = len(str(len(files)))
    renamed = []
    for f in files:
        n = int(os.path.basename(f)[6:-4])
        dst = os.path.join(out_dir, 'slide-%0*d.png' % (max(2, width), n))
        if dst != f:
            os.replace(f, dst)
        renamed.append(dst)
    return sorted(renamed)


def contact_sheet(files, out_dir, cols):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print('Pillow가 없어 contact sheet는 건너뜁니다.')
        return None
    thumbs = []
    for f in files:
        im = Image.open(f).convert('RGB')
        im.thumbnail((480, 480))
        thumbs.append(im)
    tw = max(t.width for t in thumbs)
    th = max(t.height for t in thumbs) + 22
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw + (cols + 1) * 10, rows * th + (rows + 1) * 10), 'white')
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(thumbs):
        x = 10 + (i % cols) * (tw + 10)
        y = 10 + (i // cols) * (th + 10)
        sheet.paste(t, (x, y))
        d.rectangle([x, y, x + t.width - 1, y + t.height - 1], outline='#BBBBBB')
        d.text((x, y + t.height + 4), str(i + 1), fill='black')
    path = os.path.join(out_dir, 'contact_sheet.png')
    sheet.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out_dir')
    ap.add_argument('--dpi', type=int, default=110)
    ap.add_argument('--cols', type=int, default=4)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        pdf = to_pdf(os.path.abspath(a.src), tmp)
        files = to_png(pdf, a.out_dir, a.dpi)
    if not files:
        sys.exit('렌더링된 장이 없습니다.')
    sheet = contact_sheet(files, a.out_dir, a.cols)
    print('slides: %d' % len(files))
    for f in files:
        print('  ' + f)
    if sheet:
        print('contact sheet: ' + sheet)
    print('다음 단계: 장별 PNG를 한 장씩 열어 잘림, 겹침, 대비, 정렬, 출처 표시를 확인할 것.')


if __name__ == '__main__':
    main()
