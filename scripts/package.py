#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""package.py : 업로드용 zip 만들기

claude.ai(웹, 데스크톱)나 Cowork 에 올릴 zip 을 dist/ 에 만듦. 저장소 파일은 바꾸지 않음.

  dist/insight-full-report-plugin-v{버전}.zip   플러그인 통째(권장) : Customize > Plugins > Add > Upload plugin
  dist/skills/{스킬}.zip                        스킬 하나씩 : Customize > Skills 에서 올림

규칙(공식 문서 기준)
  - 플러그인 zip : 맨 위 폴더 하나(insight-full-report/) 안에 .claude-plugin/plugin.json
  - 스킬 zip     : 맨 위가 스킬 폴더 자체(예: image-deck/SKILL.md). SKILL.md 가 zip 맨 위에 있으면 인식 안 됨
  - __pycache__, .DS_Store, *.pyc 등은 넣지 않음. 파일 시각을 고정해 같은 내용이면 같은 zip 이 나옴

사용
  python3 scripts/package.py              # dist/ 에 만들고 구조를 검사
  python3 scripts/package.py --out 경로    # 다른 폴더에
  python3 scripts/package.py --check 파일.zip  # 이미 있는 zip 의 구조만 검사

종료코드 : 0 = 성공, 1 = 구조 검사 실패
"""
import argparse
import hashlib
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, 'skills')
EXCLUDE_DIRS = {'.git', 'dist', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode'}
EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
EXCLUDE_EXT = ('.pyc', '.pyo', '.log', '.tmp', '.bak', '.swp')
PLUGIN_TOP = ['.claude-plugin', 'skills', 'scripts', 'assets', 'README.md', 'CHANGELOG.md', 'LICENSE']
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def files_under(base):
    for d, dirs, files in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x not in EXCLUDE_DIRS and not x.startswith('ifr-selftest-'))
        for f in sorted(files):
            if f in EXCLUDE_FILES or f.endswith(EXCLUDE_EXT):
                continue
            yield os.path.join(d, f)


def add(z, src, arc):
    info = zipfile.ZipInfo(arc, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    exe = src.endswith('.sh') or (src.endswith('.py') and open(src, 'rb').read(2) == b'#!')
    info.external_attr = ((0o755 if exe else 0o644) | 0o100000) << 16
    with open(src, 'rb') as f:
        z.writestr(info, f.read())


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def frontmatter_name(text):
    m = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', text, re.S)
    if not m:
        return None
    mm = re.search(r'^name:\s*(\S+)\s*$', m.group(1), re.M)
    return mm.group(1) if mm else None


def check_zip(path):
    """zip 의 모양을 보고 (종류, 문제 목록) 을 돌려줌."""
    probs = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if not n.endswith('/')]
        bad = z.testzip()
        if bad:
            probs.append('손상된 항목 : %s' % bad)
        tops = sorted({n.split('/')[0] for n in names})
        if any(n.startswith('/') or '..' in n.split('/') for n in names):
            probs.append('절대 경로나 .. 이 든 항목이 있음')
        junk = [n for n in names if os.path.basename(n) in EXCLUDE_FILES or n.endswith(EXCLUDE_EXT) or '/__pycache__/' in n]
        if junk:
            probs.append('넣지 않아야 할 파일 : %s' % ', '.join(junk[:5]))
        if len(tops) != 1:
            return 'unknown', probs + ['맨 위 항목이 하나가 아님 : %s' % ', '.join(tops[:6])]
        top = tops[0]
        if '%s/.claude-plugin/plugin.json' % top in names:
            kind = 'plugin'
            pj = json.loads(z.read('%s/.claude-plugin/plugin.json' % top).decode('utf-8'))
            skills = sorted({n.split('/')[2] for n in names if n.startswith('%s/skills/' % top) and n.endswith('/SKILL.md')
                             and n.count('/') == 3})
            if not skills:
                probs.append('skills/<이름>/SKILL.md 가 없음')
            if any(n.startswith('%s/bin/' % top) for n in names):
                probs.append('맨 위 bin/ 폴더가 있으면 claude.ai, Cowork 가 설치를 거부함')
            if len(names) > 5000:
                probs.append('파일 %d개 (한도 5,000)' % len(names))
            size = sum(i.file_size for i in z.infolist())
            if size > 200 * 1024 * 1024:
                probs.append('풀린 크기 %.1f MB (한도 200 MB)' % (size / 1048576.0))
            return 'plugin %s %s, 스킬 %s' % (pj.get('name'), pj.get('version'), ', '.join(skills)), probs
        if '%s/SKILL.md' % top in names:
            name = frontmatter_name(z.read('%s/SKILL.md' % top).decode('utf-8'))
            if name != top:
                probs.append('SKILL.md 의 name(%s) 과 폴더 이름(%s)이 다름' % (name, top))
            return 'skill %s' % top, probs
        if 'SKILL.md' in names:
            probs.append('SKILL.md 가 zip 맨 위에 있음 : 스킬 폴더째 묶어야 함')
        return 'unknown', probs + ['plugin.json 도 SKILL.md 도 찾지 못함']


def build(out_dir):
    pj = json.load(open(os.path.join(ROOT, '.claude-plugin', 'plugin.json'), encoding='utf-8'))
    name, ver = pj['name'], pj['version']
    os.makedirs(os.path.join(out_dir, 'skills'), exist_ok=True)
    made = []

    plug = os.path.join(out_dir, '%s-plugin-v%s.zip' % (name, ver))
    with zipfile.ZipFile(plug, 'w') as z:
        for top in PLUGIN_TOP:
            src = os.path.join(ROOT, top)
            if os.path.isdir(src):
                for f in files_under(src):
                    add(z, f, '%s/%s' % (name, os.path.relpath(f, ROOT).replace(os.sep, '/')))
            elif os.path.isfile(src):
                add(z, src, '%s/%s' % (name, top))
    made.append(plug)

    for d in sorted(os.listdir(SK)):
        sd = os.path.join(SK, d)
        if not os.path.isfile(os.path.join(sd, 'SKILL.md')):
            continue
        zp = os.path.join(out_dir, 'skills', '%s.zip' % d)
        with zipfile.ZipFile(zp, 'w') as z:
            for f in files_under(sd):
                add(z, f, '%s/%s' % (d, os.path.relpath(f, sd).replace(os.sep, '/')))
        made.append(zp)
    return made


def main():
    ap = argparse.ArgumentParser(description='업로드용 zip 만들기')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist'))
    ap.add_argument('--check', nargs='+', help='이미 있는 zip 의 구조만 검사')
    a = ap.parse_args()
    paths = a.check or build(os.path.abspath(a.out))
    failed = 0
    for p in paths:
        kind, probs = check_zip(p)
        size = os.path.getsize(p) / 1024.0
        mark = 'FAIL' if probs else 'OK  '
        shown = os.path.relpath(p, os.getcwd())
        shown = p if shown.startswith('..') else shown
        print('[%s] %s  (%.0f KB)  %s' % (mark, shown, size, kind))
        print('       sha256 %s' % sha256(p))
        for x in probs:
            print('       - ' + x)
        failed += bool(probs)
    if not a.check:
        print('\n올리는 곳 : claude.ai 또는 데스크톱 앱 > Customize > Plugins > Add > Upload plugin (플러그인 zip, 권장)')
        print('           스킬만 따로 쓸 때 > Customize > Skills (dist/skills/*.zip). report-harness 는 generate-full-report, image-deck 과 함께 올려야 게이트·덱이 동작')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
