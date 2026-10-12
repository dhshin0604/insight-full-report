#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ooxml_tools.py : 정본 PPTX 빌드용 최소 OOXML 도구 (자체 구현, MIT, 표준 라이브러리만 사용)

build_pptx.sh 가 TEMPLATE.pptx 를 풀고, 본문 슬라이드를 더하고, 순서를 맞추고, 다시 묶을 때 씀.
외부 스킬(pptx 스킬)의 스크립트에 기대지 않으므로 어떤 환경에 설치해도 같은 결과를 냄.

명령:
  python3 ooxml_tools.py unpack     <in.pptx> <dir>
  python3 ooxml_tools.py add-slides <dir> <slideLayoutN.xml> <count>
  python3 ooxml_tools.py move-last  <dir> <slideN.xml>
  python3 ooxml_tools.py set-layout <dir> <slideN.xml> <slideLayoutN.xml>
  python3 ooxml_tools.py clean      <dir>
  python3 ooxml_tools.py pack       <dir> <out.pptx>
  python3 ooxml_tools.py check      <file.pptx>

종료코드: 0 성공, 1 입력 오류, 2 패키지 구조 오류
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
T_SLIDE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide'
T_LAYOUT = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout'
CT_SLIDE = 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'

EMPTY_SLIDE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
    '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
    '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>'
    '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
)

SLIDE_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s" Target="../slideLayouts/{layout}"/>'
    '</Relationships>' % (NS_REL, T_LAYOUT)
)


def die(msg, code=1):
    sys.stderr.write('ooxml_tools: ' + msg + '\n')
    sys.exit(code)


def rd(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def wr(path, text):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def paths(d):
    return {
        'pres': os.path.join(d, 'ppt', 'presentation.xml'),
        'prels': os.path.join(d, 'ppt', '_rels', 'presentation.xml.rels'),
        'ct': os.path.join(d, '[Content_Types].xml'),
        'slides': os.path.join(d, 'ppt', 'slides'),
        'layouts': os.path.join(d, 'ppt', 'slideLayouts'),
    }


def require_pkg(d):
    p = paths(d)
    for k in ('pres', 'prels', 'ct'):
        if not os.path.isfile(p[k]):
            die('%s 없음 : PPTX 를 푼 폴더가 맞는지 확인' % p[k], 2)
    return p


def rel_map(prels_text):
    """presentation.xml.rels : {rId: (Type, Target)}"""
    out = {}
    for m in re.finditer(r'<Relationship\b[^>]*/>', prels_text):
        tag = m.group(0)
        rid = re.search(r'\bId="([^"]+)"', tag)
        typ = re.search(r'\bType="([^"]+)"', tag)
        tgt = re.search(r'\bTarget="([^"]+)"', tag)
        if rid and typ and tgt:
            out[rid.group(1)] = (typ.group(1), tgt.group(1))
    return out


def sld_entries(pres_text):
    m = re.search(r'<p:sldIdLst>(.*?)</p:sldIdLst>', pres_text, re.S)
    if not m:
        return None, []
    return m, re.findall(r'<p:sldId\b[^>]*/>', m.group(1))


# ── unpack ────────────────────────────────────────────────────────────────
def cmd_unpack(src, dst):
    if not os.path.isfile(src):
        die('파일 없음 : %s' % src)
    os.makedirs(dst, exist_ok=True)
    root = os.path.realpath(dst)
    with zipfile.ZipFile(src) as z:
        for info in z.infolist():
            target = os.path.realpath(os.path.join(dst, info.filename))
            if not (target == root or target.startswith(root + os.sep)):
                die('압축 안 경로가 폴더 밖을 가리킴 : %s' % info.filename, 2)
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as s, open(target, 'wb') as t:
                t.write(s.read())
    print('unpack: %s → %s' % (src, dst))


# ── add-slides ────────────────────────────────────────────────────────────
def cmd_add_slides(d, layout, count):
    p = require_pkg(d)
    if not os.path.isfile(os.path.join(p['layouts'], layout)):
        die('레이아웃 없음 : %s' % layout, 2)
    count = int(count)
    pres, prels, ct = rd(p['pres']), rd(p['prels']), rd(p['ct'])
    nums = [int(m.group(1)) for f in os.listdir(p['slides'])
            for m in [re.match(r'slide(\d+)\.xml$', f)] if m]
    next_n = (max(nums) if nums else 0) + 1
    rid_nums = [int(m.group(1)) for m in re.finditer(r'\bId="rId(\d+)"', prels)]
    next_rid = (max(rid_nums) if rid_nums else 0) + 1
    m, entries = sld_entries(pres)
    if m is None:
        die('presentation.xml 에 sldIdLst 없음', 2)
    ids = [int(x) for e in entries for x in re.findall(r'\bid="(\d+)"', e)]
    next_id = max(ids + [255]) + 1
    added, new_entries = [], []
    for i in range(count):
        n, rid, sid = next_n + i, next_rid + i, next_id + i
        name = 'slide%d.xml' % n
        wr(os.path.join(p['slides'], name), EMPTY_SLIDE)
        wr(os.path.join(p['slides'], '_rels', name + '.rels'), SLIDE_RELS.format(layout=layout))
        ct = ct.replace('</Types>', '<Override PartName="/ppt/slides/%s" ContentType="%s"/></Types>'
                        % (name, CT_SLIDE))
        prels = prels.replace('</Relationships>', '<Relationship Id="rId%d" Type="%s" Target="slides/%s"/>'
                              '</Relationships>' % (rid, T_SLIDE, name))
        new_entries.append('<p:sldId id="%d" r:id="rId%d"/>' % (sid, rid))
        added.append(name)
    inner = m.group(1) + ''.join(new_entries)
    pres = pres[:m.start()] + '<p:sldIdLst>%s</p:sldIdLst>' % inner + pres[m.end():]
    wr(p['pres'], pres); wr(p['prels'], prels); wr(p['ct'], ct)
    print('add-slides: %d장 추가 (%s ~ %s, 레이아웃 %s)' % (count, added[0], added[-1], layout) if added
          else 'add-slides: 0장')


# ── move-last ─────────────────────────────────────────────────────────────
def cmd_move_last(d, slide_name):
    p = require_pkg(d)
    pres, prels = rd(p['pres']), rd(p['prels'])
    rid = [k for k, (t, tg) in rel_map(prels).items() if t == T_SLIDE and tg.endswith('slides/' + slide_name)]
    if not rid:
        die('presentation.xml.rels 에 %s 관계 없음' % slide_name, 2)
    m, entries = sld_entries(pres)
    target = [e for e in entries if 'r:id="%s"' % rid[0] in e]
    if not target:
        die('sldIdLst 에 %s 없음' % slide_name, 2)
    others = [e for e in entries if e is not target[0] and 'r:id="%s"' % rid[0] not in e]
    pres = pres[:m.start()] + '<p:sldIdLst>%s</p:sldIdLst>' % (''.join(others) + target[0]) + pres[m.end():]
    wr(p['pres'], pres)
    print('move-last: %s 를 마지막으로 이동' % slide_name)


# ── set-layout ────────────────────────────────────────────────────────────
def cmd_set_layout(d, slide_name, layout):
    p = require_pkg(d)
    rels = os.path.join(p['slides'], '_rels', slide_name + '.rels')
    if not os.path.isfile(rels):
        die('관계 파일 없음 : %s' % rels, 2)
    if not os.path.isfile(os.path.join(p['layouts'], layout)):
        die('레이아웃 없음 : %s' % layout, 2)
    text = rd(rels)
    new = re.sub(r'(Target="\.\./slideLayouts/)slideLayout\d+\.xml(")', r'\g<1>%s\g<2>' % layout, text)
    wr(rels, new)
    print('set-layout: %s → %s' % (slide_name, layout))


# ── clean : sldIdLst 에 없는 슬라이드 파트 제거 ───────────────────────────────
def cmd_clean(d):
    p = require_pkg(d)
    pres, prels, ct = rd(p['pres']), rd(p['prels']), rd(p['ct'])
    rmap = rel_map(prels)
    _, entries = sld_entries(pres)
    used = set()
    for e in entries:
        r = re.search(r'r:id="([^"]+)"', e)
        if r and r.group(1) in rmap:
            used.add(os.path.basename(rmap[r.group(1)][1]))
    removed = []
    for f in sorted(os.listdir(p['slides'])):
        if re.match(r'slide\d+\.xml$', f) and f not in used:
            os.remove(os.path.join(p['slides'], f))
            relf = os.path.join(p['slides'], '_rels', f + '.rels')
            if os.path.isfile(relf):
                os.remove(relf)
            ct = re.sub(r'<Override PartName="/ppt/slides/%s"[^>]*/>' % re.escape(f), '', ct)
            prels = re.sub(r'<Relationship\b[^>]*Target="slides/%s"[^>]*/>' % re.escape(f), '', prels)
            removed.append(f)
    wr(p['ct'], ct); wr(p['prels'], prels)
    print('clean: 미사용 슬라이드 %d개 제거%s' % (len(removed), (' ' + ', '.join(removed)) if removed else ''))


# ── pack ──────────────────────────────────────────────────────────────────
def cmd_pack(d, out):
    require_pkg(d)
    files = []
    for base, _, names in os.walk(d):
        for n in names:
            if n in ('.DS_Store', 'Thumbs.db'):
                continue
            full = os.path.join(base, n)
            files.append(os.path.relpath(full, d).replace(os.sep, '/'))
    first = [f for f in ('[Content_Types].xml', '_rels/.rels') if f in files]
    rest = sorted(f for f in files if f not in first)
    for f in first + rest:
        if f.endswith('.xml') or f.endswith('.rels'):
            try:
                ET.parse(os.path.join(d, f))
            except ET.ParseError as e:
                die('XML 오류 %s : %s' % (f, e), 2)
    tmp = out + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in first + rest:
            z.write(os.path.join(d, f), f)
    os.replace(tmp, out)
    print('pack: %s (%d개 파트)' % (out, len(files)))


# ── check : 묶인 PPTX 의 구조 점검 ────────────────────────────────────────
def cmd_check(path):
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            die('손상된 파트 : %s' % bad, 2)
        names = set(z.namelist())
        pres = z.read('ppt/presentation.xml').decode('utf-8')
        prels = z.read('ppt/_rels/presentation.xml.rels').decode('utf-8')
        ct = z.read('[Content_Types].xml').decode('utf-8')
    rmap = rel_map(prels)
    _, entries = sld_entries(pres)
    order, problems = [], []
    for e in entries:
        r = re.search(r'r:id="([^"]+)"', e).group(1)
        if r not in rmap:
            problems.append('sldIdLst 의 %s 관계 없음' % r); continue
        part = 'ppt/' + rmap[r][1]
        order.append(os.path.basename(part))
        if part not in names:
            problems.append('파트 없음 : %s' % part)
        if '/%s"' % part not in ct:
            problems.append('Content_Types 등록 없음 : %s' % part)
    print('check: 슬라이드 %d장, 순서 %s' % (len(order), ' '.join(order)))
    if problems:
        for x in problems:
            print('  ❌ ' + x)
        sys.exit(2)
    print('check: OK')


def main(argv):
    if len(argv) < 2:
        print(__doc__); sys.exit(1)
    cmd, args = argv[1], argv[2:]
    table = {
        'unpack': (cmd_unpack, 2), 'add-slides': (cmd_add_slides, 3), 'move-last': (cmd_move_last, 2),
        'set-layout': (cmd_set_layout, 3), 'clean': (cmd_clean, 1), 'pack': (cmd_pack, 2), 'check': (cmd_check, 1),
    }
    if cmd not in table or len(args) != table[cmd][1]:
        print(__doc__); sys.exit(1)
    table[cmd][0](*args)


if __name__ == '__main__':
    main(sys.argv)
