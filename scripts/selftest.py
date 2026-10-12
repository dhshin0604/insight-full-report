#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest.py : insight-full-report 설치 자가 시험

가상의 프로필(홍길동, name@example.com)로 네 스킬의 예시를 임시 폴더에서 끝까지 만들고
게이트까지 돌림. 저장소(설치 폴더)의 파일은 바꾸지 않음.

묶음
  static   의존성 없이 되는 정적 검사 : 매니페스트, SKILL.md 머리말, 참조 파일, 사전 사본,
           줄표, 개인정보·비밀값 패턴, 파이썬·자바스크립트·셸 문법, 패키지 크기
  gfr      generate-full-report : PPTX KR/EN(build_pptx.sh) + Word KR/EN(정본 템플릿) → 게이트, 언어 순도
  harness  report-harness : selfcheck → assemble → build_docx → gate_report(--claims)
  deck     image-deck : 데모 덱 렌더(자동 QA) → PDF, PPTX, PNG zip
  core     quality-core : verify_claims_lite 로 맞는 초안은 통과, 틀린 초안은 실패하는지
  plugin   claude plugin validate --strict (Claude Code CLI 가 있을 때)

사용
  python3 scripts/selftest.py                      # 전체
  python3 scripts/selftest.py --only static        # 정적 검사만 (설치 직후 빠른 확인)
  python3 scripts/selftest.py --only gfr,deck      # 일부만
  python3 scripts/selftest.py --render             # LibreOffice 로 Word·PPTX 를 PDF 로 바꿔 열리는지도 확인
  python3 scripts/selftest.py --deny my_terms.txt  # 공개하면 안 되는 낱말(한 줄에 하나)을 추가로 검사
  python3 scripts/selftest.py --keep               # 임시 폴더를 남김 (FAIL 이 있으면 늘 남김)

결과 : 항목마다 PASS / FAIL / SKIP 과 요약. 임시 폴더에 selftest_report.json.
종료코드 : 0 = FAIL 없음, 1 = FAIL 있음
"""
import argparse
import json
import os
import platform
import py_compile
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zipfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, 'skills')
GFR = os.path.join(SK, 'generate-full-report', 'references')
HAR = os.path.join(SK, 'report-harness', 'references')
DECK = os.path.join(SK, 'image-deck', 'references')
SKILLS = ['generate-full-report', 'image-deck', 'report-harness', 'quality-core']
GROUPS = ['static', 'gfr', 'harness', 'deck', 'core', 'plugin']
CORE = os.path.join(SK, 'quality-core', 'references')
SYS = platform.system()
PY = sys.executable

PROFILE = {
    'AUTHOR_KR': '홍길동', 'AUTHOR_EN': 'Gildong Hong', 'PHONE_KR': '010-0000-0000',
    'PHONE_EN': '+82-10-0000-0000', 'EMAIL': 'name@example.com', 'BRAND': 'Insight Report',
    'WORKSPACE_ROOT': '', 'WORKSPACE_DIRNAME': '',
}

TEXT_EXT = {'.md', '.py', '.js', '.json', '.sh', '.ps1', '.svg', '.txt', '.yml', '.yaml',
            '.html', '.css', '.toml', '.cfg', '.ini'}
OFFICE_EXT = {'.pptx', '.docx', '.xlsx'}
SKIP_DIRS = {'.git', 'dist', 'node_modules', '__pycache__', '.venv', 'venv'}

RESULTS = []
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass


# ── 공용 ──────────────────────────────────────────────────────────────────
def rec(group, name, status, detail='', secs=None):
    RESULTS.append({'group': group, 'name': name, 'status': status, 'detail': detail,
                    'secs': round(secs, 1) if secs is not None else None})
    mark = {'PASS': 'PASS', 'FAIL': 'FAIL', 'SKIP': 'SKIP'}[status]
    t = '' if secs is None else ' (%.0fs)' % secs
    first, *rest = (detail or '').splitlines() or ['']
    print('  [%s] %-8s %-22s %s%s' % (mark, group, name, first, t))
    for ln in rest:
        print('         ' + ln)
    sys.stdout.flush()


def run(cmd, cwd=None, env=None, timeout=600, utf8=True):
    """utf8=False 는 한국어 Windows 의 파이프(cp949)를 흉내 냄 : 스크립트가 스스로 UTF-8 로 맞추는지 시험."""
    e = dict(os.environ)
    e['PYTHONIOENCODING'] = 'utf-8' if utf8 else 'cp949'
    e['PYTHONUTF8'] = '1' if utf8 else '0'
    e['PYTHONDONTWRITEBYTECODE'] = '1'   # 저장소 안에 __pycache__ 를 남기지 않음
    if env:
        e.update(env)
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=cwd, env=e, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 124, '시간 초과 (%ds)' % timeout
    except OSError as ex:
        return 127, str(ex)


def tail(out, n=8):
    lines = [ln for ln in (out or '').strip().splitlines() if ln.strip()]
    return '\n'.join(lines[-n:])


def walk_files(base):
    for d, dirs, files in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith('ifr-selftest-'))
        for f in sorted(files):
            yield os.path.join(d, f)


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, '/')


def write_png(path, w=1600, h=900, rgb=(226, 232, 240)):
    """Pillow 없이 단색 PNG 를 씀 (표지 그림 자리)."""
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))

    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return path


def node_env():
    npm = shutil.which('npm')
    paths = []
    if npm:
        rc, out = run([npm, 'root', '-g'], timeout=60)
        if rc == 0 and out.strip():
            paths.append(out.strip().splitlines()[-1].strip())
    if os.environ.get('NODE_PATH'):
        paths.append(os.environ['NODE_PATH'])
    return {'NODE_PATH': os.pathsep.join(paths)} if paths else {}


def has_docx(node, env):
    rc, _ = run([node, '-e', "require('docx')"], env=env, timeout=60)
    return rc == 0


def find_bash():
    b = shutil.which('bash')
    if SYS == 'Windows':
        cands = [os.path.join(os.environ.get(k, ''), 'Git', 'bin', 'bash.exe')
                 for k in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)')]
        cands.append(os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Git', 'bin', 'bash.exe'))
        for c in cands:
            if os.path.isfile(c):
                return c
        if b and 'system32' in b.lower():   # WSL 실행기 : Windows 경로를 그대로 못 씀
            return None
    return b


def fwd(p):
    return p.replace('\\', '/')


def gate_summary(path):
    try:
        g = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return False, 'gate.json 없음'
    gates = g.get('gates', {})
    s = ', '.join('%s=%s' % (k, v) for k, v in gates.items())
    fx = g.get('fixes', [])
    if fx:
        s += '\n' + '\n'.join('fix: %s %s %s' % (x.get('type'), x.get('loc'), (x.get('detail') or '')[:80]) for x in fx[:6])
    return bool(g.get('pass')), s


# ── static ────────────────────────────────────────────────────────────────
def frontmatter(text):
    m = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', text, re.S)
    if not m:
        return None, '머리말(---) 없음'
    raw = m.group(1)
    try:
        import yaml  # noqa: WPS433
        try:
            d = yaml.safe_load(raw)
        except Exception as ex:  # noqa: BLE001
            return None, 'YAML 오류 : %s' % str(ex).splitlines()[0]
        return (d, '') if isinstance(d, dict) else (None, 'YAML 이 사전이 아님')
    except ImportError:
        pass
    d, key, buf = {}, None, []
    for line in raw.splitlines():
        mm = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if mm and not line[:1].isspace():
            if key:
                d[key] = '\n'.join(buf).strip()
            key, val = mm.group(1), mm.group(2).strip()
            buf = [] if val in ('|', '>', '|-', '>-', '') else [val]
        elif key:
            buf.append(line.strip())
    if key:
        d[key] = '\n'.join(buf).strip()
    return d, ''


def st_manifest():
    probs = []
    try:
        pj = json.load(open(os.path.join(ROOT, '.claude-plugin', 'plugin.json'), encoding='utf-8'))
        mj = json.load(open(os.path.join(ROOT, '.claude-plugin', 'marketplace.json'), encoding='utf-8'))
    except (OSError, ValueError) as ex:
        return rec('static', 'manifest', 'FAIL', str(ex))
    name, ver = pj.get('name', ''), pj.get('version', '')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name):
        probs.append('plugin.json name 형식 : %r' % name)
    if not re.fullmatch(r'\d+\.\d+\.\d+', ver):
        probs.append('plugin.json version 형식 : %r' % ver)
    entries = {p.get('name'): p for p in mj.get('plugins', [])}
    if name not in entries:
        probs.append('marketplace.json 에 %s 항목 없음' % name)
    elif entries[name].get('source') not in ('.', './'):
        probs.append('marketplace.json source 가 저장소 루트(.)가 아님')
    cl = os.path.join(ROOT, 'CHANGELOG.md')
    if os.path.isfile(cl):
        head = open(cl, encoding='utf-8').read()[:3000]
        if ver not in head:
            probs.append('CHANGELOG.md 맨 위에 %s 없음' % ver)
    else:
        probs.append('CHANGELOG.md 없음')
    bad_json = []
    for p in walk_files(ROOT):
        if p.endswith('.json'):
            try:
                json.load(open(p, encoding='utf-8'))
            except (OSError, ValueError) as ex:
                bad_json.append('%s : %s' % (rel(p), ex))
    probs += bad_json
    rec('static', 'manifest', 'FAIL' if probs else 'PASS',
        '\n'.join(probs) if probs else '%s %s, 마켓플레이스 %s, JSON 파일 모두 읽힘' % (name, ver, mj.get('name')))


def st_frontmatter():
    probs, info = [], []
    dirs = sorted(d for d in os.listdir(SK) if os.path.isdir(os.path.join(SK, d)))
    for d in dirs:
        p = os.path.join(SK, d, 'SKILL.md')
        if not os.path.isfile(p):
            probs.append('%s : SKILL.md 없음' % d)
            continue
        fm, err = frontmatter(open(p, encoding='utf-8').read())
        if fm is None:
            probs.append('%s : %s' % (d, err))
            continue
        name, desc = str(fm.get('name', '')), str(fm.get('description', '') or '').strip()
        if name != d:
            probs.append('%s : name(%s) 이 폴더 이름과 다름' % (d, name))
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name) or len(name) > 64:
            probs.append('%s : name 은 소문자, 숫자, 하이픈 64자 이하' % d)
        if 'claude' in name or 'anthropic' in name:
            probs.append('%s : name 에 예약어(claude, anthropic)' % d)
        if not desc:
            probs.append('%s : description 없음' % d)
        if len(desc) > 1024:
            probs.append('%s : description %d자 (1024자 이하)' % (d, len(desc)))
        if re.search(r'<[A-Za-z/!]', desc):
            probs.append('%s : description 에 XML 태그 모양(<...>)' % d)
        n_lines = open(p, encoding='utf-8').read().count('\n')
        info.append('%s(설명 %d자, %d줄)' % (d, len(desc), n_lines))
    missing = [s for s in SKILLS if s not in dirs]
    if missing:
        probs.append('스킬 폴더 없음 : %s' % ', '.join(missing))
    rec('static', 'skill-frontmatter', 'FAIL' if probs else 'PASS', '\n'.join(probs) if probs else ', '.join(info))


OPTIONAL_REFS = {'logo.png'}  # 사용자가 넣는 선택 파일


def st_refs():
    miss = []
    pat = re.compile(r'(?:(generate-full-report|image-deck|report-harness|quality-core)/)?references/'
                     r'([\w\-./]+?\.(?:py|js|md|json|sh|ps1|pptx|png))(?![\w])')
    for d in SKILLS:
        p = os.path.join(SK, d, 'SKILL.md')
        if not os.path.isfile(p):
            continue
        for i, line in enumerate(open(p, encoding='utf-8'), 1):
            for m in pat.finditer(line):
                sk, f = m.group(1) or d, m.group(2)
                if os.path.basename(f) in OPTIONAL_REFS:
                    continue
                if not os.path.isfile(os.path.join(SK, sk, 'references', f)):
                    miss.append('%s:%d → %s/references/%s' % (rel(p), i, sk, f))
    rpat = re.compile(r'(?<![\w/.\-])((?:scripts|skills|assets|\.claude-plugin)/[\w\-./]+?\.(?:py|js|md|json|sh|png|svg|pptx))(?![\w])')
    for doc in ('README.md', 'CHANGELOG.md'):
        p = os.path.join(ROOT, doc)
        if not os.path.isfile(p):
            continue
        for i, line in enumerate(open(p, encoding='utf-8'), 1):
            for m in rpat.finditer(line):
                f = m.group(1)
                if os.path.basename(f) in OPTIONAL_REFS:
                    continue
                if not os.path.exists(os.path.join(ROOT, f)):
                    miss.append('%s:%d → %s' % (doc, i, f))
    rec('static', 'referenced-files', 'FAIL' if miss else 'PASS',
        '\n'.join(sorted(set(miss))[:20]) if miss else 'SKILL.md, README, CHANGELOG 가 가리키는 파일이 모두 있음')


def st_lexicon():
    copies = sorted(p for p in walk_files(SK) if os.path.basename(p) == 'lexicon.json')
    if len(copies) < 2:
        return rec('static', 'lexicon-copies', 'FAIL', 'lexicon.json 사본이 %d개 (2개 이상이어야 함)' % len(copies))
    blobs = {p: open(p, 'rb').read() for p in copies}
    first = blobs[copies[0]]
    diff = [rel(p) for p in copies if blobs[p] != first]
    if diff:
        return rec('static', 'lexicon-copies', 'FAIL', '내용이 다름 : %s (기준 %s)' % (', '.join(diff), rel(copies[0])))
    lx = json.loads(first.decode('utf-8'))
    rec('static', 'lexicon-copies', 'PASS', '%d개 사본 같음 : %s, 줄표 수준 %s' % (
        len(copies), ', '.join(rel(p) for p in copies), lx.get('dash', {}).get('level')))


def iter_text_sources():
    """(경로, 표시 이름, 텍스트) : 텍스트 파일과 Office 파일 안의 XML."""
    for p in walk_files(ROOT):
        ext = os.path.splitext(p)[1].lower()
        base = os.path.basename(p)
        if ext in TEXT_EXT or base in ('LICENSE', '.gitignore', '.gitattributes'):
            try:
                yield p, rel(p), open(p, encoding='utf-8').read()
            except (UnicodeDecodeError, OSError):
                continue
        elif ext in OFFICE_EXT:
            try:
                with zipfile.ZipFile(p) as z:
                    for n in z.namelist():
                        if n.endswith(('.xml', '.rels')):
                            yield p, '%s!%s' % (rel(p), n), z.read(n).decode('utf-8', 'replace')
            except (zipfile.BadZipFile, OSError):
                continue


def st_dash():
    hits = []
    for _, name, text in iter_text_sources():
        n = text.count('\u2014')
        if n:
            hits.append('%s : %d개' % (name, n))
    rec('static', 'no-em-dash', 'FAIL' if hits else 'PASS',
        '\n'.join(hits[:20]) if hits else '배포 파일(텍스트, Office XML)에 줄표(U+2014) 0개')


def st_privacy(deny_terms):
    allow_mail = {'name@example.com', 'noreply@anthropic.com'}
    try:
        pj = json.load(open(os.path.join(ROOT, '.claude-plugin', 'plugin.json'), encoding='utf-8'))
        if pj.get('author', {}).get('email'):
            allow_mail.add(pj['author']['email'].lower())
    except (OSError, ValueError):
        pass
    pats = [
        ('전화번호', re.compile(r'(?<![\d-])01[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)'), {'010-0000-0000'}),
        ('국제 전화번호', re.compile(r'\+82[-. ]?1[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)'), {'+82-10-0000-0000'}),
        ('이메일', re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'), None),
        ('사용자 폴더 경로', re.compile(r'(?:[A-Za-z]:)?[\\/]{1,2}Users[\\/]{1,2}(?![<%${])([A-Za-z0-9._ -]+)[\\/]'), None),
        ('홈 폴더 경로', re.compile(r'/home/(?![<{$])[a-z][\w.-]*/'), None),
        ('세션 경로', re.compile(r'/sessions/(?![*<{$])[a-z]+-[a-z]+'), None),
        ('비밀값 모양', re.compile(r'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-ant-[A-Za-z0-9_-]{10,}'
                                r'|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}'), None),
    ]
    deny_rx = []
    for t in deny_terms:
        if re.fullmatch(r'[A-Za-z0-9 ._-]+', t):   # 영문·숫자는 낱말 단위로 (짧은 낱말이 다른 낱말 속에서 걸리지 않게)
            deny_rx.append((t, re.compile(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % re.escape(t), re.I)))
        else:                                        # 한글·한자는 그대로 포함 여부
            deny_rx.append((t, re.compile(re.escape(t))))
    hits = []
    for _, name, text in iter_text_sources():
        for label, rx, allow in pats:
            for m in rx.finditer(text):
                v = m.group(0)
                if label == '이메일':
                    low = v.lower()
                    if low in allow_mail or low.endswith(('@example.com', '@example.org', '@example.net')):
                        continue
                    if re.search(r'@\d+\.\d+', v):  # 패키지@버전 모양
                        continue
                elif allow and v in allow:
                    continue
                elif label == '사용자 폴더 경로' and m.group(1).strip().lower() in ('public', 'default', 'shared'):
                    continue
                line = text.count('\n', 0, m.start()) + 1
                hits.append('%s:%d %s : %s' % (name, line, label, v))
        for t, rx in deny_rx:
            m = rx.search(text)
            if m:
                hits.append('%s:%d 금지 낱말 : %s' % (name, text.count('\n', 0, m.start()) + 1, t))
    extra = ', 금지 낱말 %d개 함께 검사' % len(deny_terms) if deny_terms else ''
    rec('static', 'privacy-scan', 'FAIL' if hits else 'PASS',
        '\n'.join(sorted(set(hits))[:30]) if hits else
        '전화, 이메일, 개인 경로, 비밀값 모양 없음 (예시 값과 작성자 이메일만 허용%s)' % extra)


def st_syntax(tmp):
    errs, n_py, n_js, n_sh = [], 0, 0, 0
    node, bash = shutil.which('node'), find_bash()
    for p in walk_files(ROOT):
        ext = os.path.splitext(p)[1]
        if ext == '.py':
            n_py += 1
            try:
                py_compile.compile(p, cfile=os.path.join(tmp, 'syntax_check.pyc'), doraise=True)
            except py_compile.PyCompileError as ex:
                errs.append('%s : %s' % (rel(p), str(ex).splitlines()[-1]))
        elif ext == '.js' and node:
            n_js += 1
            rc, out = run([node, '--check', p], timeout=60)
            if rc:
                errs.append('%s : %s' % (rel(p), tail(out, 2)))
        elif ext == '.sh' and bash:
            n_sh += 1
            rc, out = run([bash, '-n', fwd(p)], timeout=60)
            if rc:
                errs.append('%s : %s' % (rel(p), tail(out, 2)))
    note = '' if node else ' (node 없음 : JS 검사 생략)'
    note += '' if bash else ' (bash 없음 : 셸 검사 생략)'
    rec('static', 'syntax', 'FAIL' if errs else 'PASS',
        '\n'.join(errs) if errs else 'Python %d, JS %d, Shell %d 파일 문법 OK%s' % (n_py, n_js, n_sh, note))


def st_package():
    n, size, bad = 0, 0, []
    for p in walk_files(ROOT):
        n += 1
        size += os.path.getsize(p)
        b = os.path.basename(p)
        if b in ('.DS_Store', 'Thumbs.db', 'desktop.ini') or b.endswith(('.pyc', '.log', '.tmp')):
            bad.append(rel(p))
    probs = []
    if n > 5000:
        probs.append('파일 %d개 (claude.ai 플러그인 업로드 한도 5,000개)' % n)
    if size > 200 * 1024 * 1024:
        probs.append('크기 %.1f MB (claude.ai 플러그인 업로드 한도 200 MB)' % (size / 1048576.0))
    if bad:
        probs.append('배포에 넣지 않을 파일 : %s' % ', '.join(bad[:10]))
    rec('static', 'package-size', 'FAIL' if probs else 'PASS',
        '\n'.join(probs) if probs else '파일 %d개, %.1f MB (업로드 한도 5,000개, 200 MB 안)' % (n, size / 1048576.0))


def claims_roundtrip(d, target, lang):
    """원장 대조 경로 시험 : 빈 원장으로 걸린 숫자를 모두 등록하면 claims 게이트가 통과해야 함.
    헤딩 번호·날짜 같은 구조 숫자가 걸리면 등록해도 남는 소음이므로 실패로 봄. target = ['--docx', f] 또는 ['--unpacked', d]."""
    with open(os.path.join(d, 'empty_claims.json'), 'w', encoding='utf-8') as f:
        json.dump({'topic': 'selftest', 'claims': []}, f)
    run([PY, os.path.join(GFR, 'verify_claims.py'), '--claims', 'empty_claims.json', '--lang', lang,
         '--json', 'claims_first.json'] + target, cwd=d)
    try:
        first = json.load(open(os.path.join(d, 'claims_first.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return False, 'verify_claims 리포트 없음'
    vals = sorted({e['detail'].split(' …')[0] for e in first.get('errors', []) if e.get('type') == 'NUM_UNREG'})
    noise = [v for v in vals if re.fullmatch(r'\d{1,2}\.\d{1,2}', v) and v in HEADING_NUMS.get(d, set())]
    led = {'topic': 'selftest', 'claims': [
        {'id': 'S%03d' % i, 'text': 'selftest 등록 수치 %s' % v, 'value': v, 'status': 'verified', 'source': 'selftest'}
        for i, v in enumerate(vals, 1)]}
    with open(os.path.join(d, 'claims_all.json'), 'w', encoding='utf-8') as f:
        json.dump(led, f, ensure_ascii=False)
    run([PY, os.path.join(GFR, 'gate_report.py'), '--lang', lang, '--skill-dir', GFR, '--claims', 'claims_all.json',
         '--out', 'gate_claims.json'] + target, cwd=d)
    ok_gate, gs = gate_summary(os.path.join(d, 'gate_claims.json'))
    ok = ok_gate and 'claims=ok' in gs and not noise
    return ok, ('원장 대조 OK (본문 수치 %d개 등록)' % len(vals)) if ok else ('원장 대조 실패 : %s, 구조 숫자 %s' % (gs.splitlines()[0], noise))


HEADING_NUMS = {}


def docx_heading_numbers(path):
    """Word 헤딩의 장·절 번호(1.1 등) : 원장 대조에서 이것이 걸리면 소음."""
    out = set()
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read('word/document.xml').decode('utf-8', 'replace')
    except (OSError, zipfile.BadZipFile, KeyError):
        return out
    for para in re.findall(r'<w:p[ >].*?</w:p>', xml, re.S):
        if re.search(r'<w:pStyle w:val="(?:Heading|heading|Title|TOC)', para):
            text = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', para))
            m = re.match(r'\s*(\d+\.\d+)', text)
            if m:
                out.add(m.group(1))
    return out


# ── gfr ───────────────────────────────────────────────────────────────────
def gfr_pptx(out_dir, prof, lang, render):
    t0 = time.time()
    bash = find_bash()
    if not bash:
        return rec('gfr', 'pptx-%s' % lang, 'SKIP', 'bash 없음 (Windows 는 Git for Windows 의 Git Bash 필요)')
    d = os.path.join(out_dir, 'gfr_pptx_%s' % lang)
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(GFR, 'build_pptx_%s.template.py' % lang), os.path.join(d, 'build_pptx_%s.py' % lang))
    out = 'Selftest_%s_Presentation_20261012.pptx' % lang.upper()
    rc, o = run([bash, fwd(os.path.join(GFR, 'build_pptx.sh')), lang, 'build_pptx_%s.py' % lang, out],
                cwd=d, env={'PROFILE': fwd(prof), 'PYTHON': fwd(PY)}, timeout=600)
    if rc != 0 or not os.path.isfile(os.path.join(d, out)):
        return rec('gfr', 'pptx-%s' % lang, 'FAIL', 'build_pptx.sh 종료코드 %d\n%s' % (rc, tail(o)), time.time() - t0)
    rc, o = run([PY, os.path.join(GFR, 'gate_report.py'), '--unpacked', 'unpacked_%s' % lang, '--lang', lang,
                 '--skill-dir', GFR, '--out', 'gate.json'], cwd=d)
    ok_gate, gs = gate_summary(os.path.join(d, 'gate.json'))
    rc2, o2 = run([PY, os.path.join(GFR, 'verify_lang_purity.py'), '--pptx', out, lang], cwd=d)
    with zipfile.ZipFile(os.path.join(d, out)) as z:
        n = sum(1 for x in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', x))
    ok_c, msg_c = claims_roundtrip(d, ['--unpacked', 'unpacked_%s' % lang], lang)
    detail = '%d장, 게이트 %s, 언어 순도 %s, %s' % (n, gs.splitlines()[0], 'OK' if rc2 == 0 else 'FAIL', msg_c)
    if render:
        detail += ', ' + soffice_pdf(os.path.join(d, out), d)
    ok = rc == 0 and ok_gate and rc2 == 0 and n >= 6 and ok_c and 'PDF 실패' not in detail
    if not ok:
        detail += '\n' + '\n'.join(gs.splitlines()[1:]) + ('\n' + tail(o2, 4) if rc2 else '')
    rec('gfr', 'pptx-%s' % lang, 'PASS' if ok else 'FAIL', detail.strip(), time.time() - t0)


def gfr_word(out_dir, prof, lang, nenv, render):
    t0 = time.time()
    node = shutil.which('node')
    if not node:
        return rec('gfr', 'word-%s' % lang, 'SKIP', 'node 없음 (python3 scripts/doctor.py 로 설치 안내 확인)')
    if not has_docx(node, nenv):
        return rec('gfr', 'word-%s' % lang, 'SKIP', 'npm 패키지 docx 없음 (npm install -g docx)')
    d = os.path.join(out_dir, 'gfr_word_%s' % lang)
    os.makedirs(d, exist_ok=True)
    js = 'build_%s.js' % lang
    shutil.copy(os.path.join(GFR, 'build_%s.template.js' % lang), os.path.join(d, js))
    rc, o = run([PY, os.path.join(GFR, 'apply_profile.py'), '--profile', prof, js], cwd=d)
    if rc != 0:
        return rec('gfr', 'word-%s' % lang, 'FAIL', 'apply_profile 종료코드 %d\n%s' % (rc, tail(o)), time.time() - t0)
    cover = write_png(os.path.join(d, 'cover.png'))
    out = 'Selftest_%s_Report_20261012.docx' % lang.upper()
    env = dict(nenv)
    env['COVER_IMG'] = cover
    rc, o = run([node, js, out], cwd=d, env=env, timeout=300)
    if rc != 0 or not os.path.isfile(os.path.join(d, out)):
        return rec('gfr', 'word-%s' % lang, 'FAIL', 'node %s 종료코드 %d\n%s' % (js, rc, tail(o)), time.time() - t0)
    run([PY, os.path.join(GFR, 'gate_report.py'), '--docx', out, '--lang', lang, '--skill-dir', GFR,
         '--out', 'gate.json'], cwd=d)
    ok_gate, gs = gate_summary(os.path.join(d, 'gate.json'))
    rc2, o2 = run([PY, os.path.join(GFR, 'verify_lang_purity.py'), '--docx', out, lang], cwd=d)
    HEADING_NUMS[d] = docx_heading_numbers(os.path.join(d, out))
    ok_c, msg_c = claims_roundtrip(d, ['--docx', out], lang)
    detail = '게이트 %s, 언어 순도 %s, %s' % (gs.splitlines()[0], 'OK' if rc2 == 0 else 'FAIL', msg_c)
    if render:
        detail += ', ' + soffice_pdf(os.path.join(d, out), d)
    ok = ok_gate and rc2 == 0 and ok_c and 'PDF 실패' not in detail
    if not ok:
        detail += '\n' + '\n'.join(gs.splitlines()[1:]) + ('\n' + tail(o2, 4) if rc2 else '')
    rec('gfr', 'word-%s' % lang, 'PASS' if ok else 'FAIL', detail.strip(), time.time() - t0)


def soffice_pdf(path, d):
    so = shutil.which('soffice') or shutil.which('libreoffice')
    if not so:
        return 'PDF 확인 생략(LibreOffice 없음)'
    prof_dir = os.path.join(d, '_lo_profile')
    url = 'file:///' + fwd(os.path.abspath(prof_dir)).lstrip('/')
    rc, o = run([so, '-env:UserInstallation=' + url, '--headless', '--convert-to', 'pdf', '--outdir', d, path],
                cwd=d, timeout=300)
    pdf = os.path.splitext(path)[0] + '.pdf'
    if not os.path.isfile(pdf):
        return 'PDF 실패 : %s' % tail(o, 2)
    data = open(pdf, 'rb').read()
    pages = len(re.findall(rb'/Type\s*/Page(?!s)', data))
    return 'PDF %d쪽' % pages


def gfr_negative(out_dir):
    """게이트가 실제로 잡는지 : 통과한 EN PPTX 에 줄표와 과장어를 넣으면 content 게이트가 실패해야 함."""
    t0 = time.time()
    src = os.path.join(out_dir, 'gfr_pptx_en', 'unpacked_en')
    if not os.path.isdir(src):
        return rec('gfr', 'gate-catches', 'SKIP', 'pptx-en 결과가 없어 생략')
    d = os.path.join(out_dir, 'gfr_negative')
    bad = os.path.join(d, 'unpacked_en')
    shutil.copytree(src, bad)
    sl = os.path.join(bad, 'ppt', 'slides', 'slide3.xml')
    xml = open(sl, encoding='utf-8').read()
    m = re.search(r'<a:t>([^<]{8,})</a:t>', xml)
    if not m:
        return rec('gfr', 'gate-catches', 'FAIL', 'slide3.xml 에서 글자를 찾지 못함')
    inject = m.group(1) + ' \u2014 a revolutionary paradigm shift'
    xml = xml[:m.start(1)] + inject + xml[m.end(1):]
    open(sl, 'w', encoding='utf-8').write(xml)
    rc, o = run([PY, os.path.join(GFR, 'verify_content.py'), '--unpacked', bad, '--lang', 'en',
                 '--json', os.path.join(d, 'content.json')], cwd=d)
    try:
        rep = json.load(open(os.path.join(d, 'content.json'), encoding='utf-8'))
    except (OSError, ValueError):
        rep = {}
    types = sorted({e.get('type') for e in rep.get('errors', [])})
    ok = rc != 0 and rep.get('pass') is False and 'DASH' in types and 'HYPE_HARD' in types
    # 게이트가 돌지 못한 경우는 통과가 아니어야 함 : 없는 DOCX, 형식이 틀린 claims.json
    rc_m, _ = run([PY, os.path.join(GFR, 'gate_report.py'), '--docx', 'no_such.docx', '--skill-dir', GFR,
                   '--out', 'missing.json'], cwd=d)
    with open(os.path.join(d, 'bad_claims.json'), 'w', encoding='utf-8') as f:
        json.dump([{'id': 'C1'}], f)
    rc_c, _ = run([PY, os.path.join(GFR, 'gate_report.py'), '--unpacked', src, '--lang', 'en', '--skill-dir', GFR,
                   '--claims', 'bad_claims.json', '--out', 'badclaims.json'], cwd=d)
    try:
        g_c = json.load(open(os.path.join(d, 'badclaims.json'), encoding='utf-8'))
    except (OSError, ValueError):
        g_c = {}
    err_ok = rc_m == 2 and rc_c == 1 and g_c.get('gates', {}).get('claims') == 'fail'
    # 8장 이상 : INDEX 의 VIII 를 알아보는지, 목록 밖에 남은 슬라이드(VIII)를 잡는지 (N_CONTENT 불일치)
    good = os.path.join(out_dir, 'gfr_pptx_kr', 'unpacked_kr')
    viii_ok = False
    if os.path.isdir(good):
        t1 = os.path.join(d, 'toc_viii')
        shutil.copytree(good, t1)
        p2 = os.path.join(t1, 'ppt', 'slides', 'slide2.xml')
        x = open(p2, encoding='utf-8').read()
        open(p2, 'w', encoding='utf-8').write(re.sub(r'<a:t>VII\.', '<a:t>VIII.', x, count=1))
        rc1, o1 = run([PY, os.path.join(GFR, 'verify_toc.py'), t1], cwd=d)
        t2 = os.path.join(d, 'lost_viii')
        shutil.copytree(good, t2)
        sd = os.path.join(t2, 'ppt', 'slides')
        x = open(os.path.join(sd, 'slide13.xml'), encoding='utf-8').read()
        open(os.path.join(sd, 'slide14.xml'), 'w', encoding='utf-8').write(re.sub(r'<a:t>VII\.', '<a:t>VIII.', x, count=1))
        rc2, o2 = run([PY, os.path.join(GFR, 'verify_toc.py'), t2], cwd=d)
        viii_ok = rc1 == 1 and "'VIII'" in o1 and rc2 == 1 and 'slide14.xml' in o2
    ok = ok and err_ok and viii_ok
    rec('gfr', 'gate-catches', 'PASS' if ok else 'FAIL',
        '줄표와 과장어를 넣은 EN 슬라이드에서 %s 검출, 없는 DOCX 와 틀린 claims.json 도 실패, '
        'VIII 장 누락과 목록 밖 슬라이드도 검출' % ', '.join(types)
        if ok else 'rc=%d, 오류 종류 %s, 없는 DOCX rc=%d, 틀린 claims rc=%d %s, VIII 검사 %s\n%s'
        % (rc, types, rc_m, rc_c, g_c.get('gates'), viii_ok, tail(o, 6)), time.time() - t0)


def gfr_cp949(out_dir):
    """한국어 Windows 파이프(cp949)를 흉내 내어 게이트 스크립트가 출력 때문에 멈추지 않는지, 판정이 그대로인지 봄."""
    t0 = time.time()
    good = os.path.join(out_dir, 'gfr_pptx_kr', 'unpacked_kr')
    bad = os.path.join(out_dir, 'gfr_negative', 'unpacked_en')
    pptx = os.path.join(out_dir, 'gfr_pptx_kr', 'Selftest_KR_Presentation_20261012.pptx')
    if not (os.path.isdir(good) and os.path.isdir(bad)):
        return rec('gfr', 'cp949-pipe', 'SKIP', 'pptx-kr 또는 gate-catches 결과가 없어 생략')
    d = os.path.join(out_dir, 'gfr_cp949')
    os.makedirs(d, exist_ok=True)
    checks = [
        ('verify_toc', [PY, os.path.join(GFR, 'verify_toc.py'), good], 0),
        ('apply_profile --which', [PY, os.path.join(GFR, 'apply_profile.py'), '--which'], 0),
        ('ooxml_tools check', [PY, os.path.join(GFR, 'ooxml_tools.py'), 'check', pptx], 0),
        ('verify_lang_purity', [PY, os.path.join(GFR, 'verify_lang_purity.py'), '--pptx', pptx, 'kr'], 0),
        ('gate_report 좋은 PPTX', [PY, os.path.join(GFR, 'gate_report.py'), '--unpacked', good, '--lang', 'kr',
                                 '--skill-dir', GFR, '--out', 'good.json'], 0),
        ('gate_report 나쁜 PPTX', [PY, os.path.join(GFR, 'gate_report.py'), '--unpacked', bad, '--lang', 'en',
                                 '--skill-dir', GFR, '--out', 'bad.json'], 1),
    ]
    probs = []
    for label, cmd, want in checks:
        rc, o = run(cmd, cwd=d, env={'PROFILE': os.path.join(out_dir, 'profile.json')}, utf8=False)
        if rc != want or 'Traceback' in o or 'UnicodeEncodeError' in o:
            probs.append('%s : 종료코드 %d (기대 %d) %s' % (label, rc, want, tail(o, 3)))
    try:
        gb = json.load(open(os.path.join(d, 'bad.json'), encoding='utf-8'))
        if gb.get('pass') is not False or gb.get('gates', {}).get('content') != 'fail':
            probs.append('나쁜 PPTX 가 cp949 에서 통과로 나옴 : %s' % gb.get('gates'))
    except (OSError, ValueError):
        probs.append('bad.json 없음')
    rec('gfr', 'cp949-pipe', 'FAIL' if probs else 'PASS',
        '\n'.join(probs) if probs else 'cp949 파이프에서도 6개 스크립트가 멈추지 않고, 나쁜 PPTX 는 그대로 실패',
        time.time() - t0)


# ── harness ───────────────────────────────────────────────────────────────
def harness(out_dir, prof, nenv, render):
    d = os.path.join(out_dir, 'harness')
    shutil.copytree(os.path.join(HAR, 'examples'), d, ignore=shutil.ignore_patterns('__pycache__'))
    env = {'PROFILE': prof}
    t0 = time.time()
    rc, o = run([PY, os.path.join(HAR, 'selfcheck.py'), 'content_front', 'content_ch1', 'content_ch2',
                 '--mode', 'status'], cwd=d, env=env)
    last = tail(o, 1)
    ok = rc == 0 and last.strip().startswith('PASS')
    rec('harness', 'selfcheck', 'PASS' if ok else 'FAIL', last if ok else tail(o, 12), time.time() - t0)
    if not ok:
        return
    t0 = time.time()
    rc, o = run([PY, os.path.join(HAR, 'assemble.py'), '--front', 'content_front', '--chapters',
                 'content_ch1,content_ch2', '--out', 'content.json', '--claims', 'claims.json',
                 '--date', '2026년 10월 12일'], cwd=d, env=env)
    ok = rc == 0 and os.path.isfile(os.path.join(d, 'content.json')) and os.path.isfile(os.path.join(d, 'claims.json'))
    n_claims = 0
    if ok:
        n_claims = len(json.load(open(os.path.join(d, 'claims.json'), encoding='utf-8')).get('claims', []))
    rec('harness', 'assemble', 'PASS' if ok else 'FAIL',
        'content.json, claims.json (claim %d개)' % n_claims if ok else tail(o), time.time() - t0)
    if not ok:
        return
    t0 = time.time()
    node = shutil.which('node')
    if not node or not has_docx(node, nenv):
        return rec('harness', 'build-docx', 'SKIP', 'node 또는 npm 패키지 docx 없음 (python3 scripts/doctor.py)')
    e = dict(nenv)
    e.update(env)
    rc, o = run([node, os.path.join(HAR, 'build_docx.js'), 'content.json', 'report.docx'], cwd=d, env=e, timeout=300)
    ok = rc == 0 and os.path.isfile(os.path.join(d, 'report.docx'))
    detail = ('report.docx %.0f KB' % (os.path.getsize(os.path.join(d, 'report.docx')) / 1024.0)) if ok \
        else 'build_docx.js 종료코드 %d\n%s' % (rc, tail(o))
    if ok and render:
        detail += ', ' + soffice_pdf(os.path.join(d, 'report.docx'), d)
    rec('harness', 'build-docx', 'PASS' if ok and 'PDF 실패' not in detail else 'FAIL', detail, time.time() - t0)
    if not ok:
        return
    t0 = time.time()
    run([PY, os.path.join(GFR, 'gate_report.py'), '--docx', 'report.docx', '--lang', 'kr', '--skill-dir', GFR,
         '--claims', 'claims.json', '--out', 'gate.json'], cwd=d)
    ok_gate, gs = gate_summary(os.path.join(d, 'gate.json'))
    claims_ok = 'claims=ok' in gs
    rec('harness', 'gate', 'PASS' if ok_gate and claims_ok else 'FAIL',
        gs if ok_gate and claims_ok else gs + ('' if claims_ok else '\nclaims 게이트가 실행되지 않음'), time.time() - t0)


def harness_negative(out_dir, nenv):
    """원고에 과장어와 미등록 수치를 넣으면 selfcheck 와 게이트(content, claims)가 모두 실패해야 함."""
    t0 = time.time()
    d = os.path.join(out_dir, 'harness')
    if not os.path.isfile(os.path.join(d, 'content.json')):
        return rec('harness', 'gate-catches', 'SKIP', 'assemble 결과가 없어 생략')
    c = json.load(open(os.path.join(d, 'content.json'), encoding='utf-8'))
    target = None
    for ch in c.get('chapters', []):
        for sec in ch.get('sections', []):
            for b in sec.get('blocks', []):
                if b.get('type') == 'p' and target is None:
                    target = b
    if target is None:
        return rec('harness', 'gate-catches', 'FAIL', 'content.json 에 문단 블록이 없음')
    target['text'] += ' 혁명적인 변화로 대여가 1,234,567건 늘었음.'
    with open(os.path.join(d, 'bad_content.json'), 'w', encoding='utf-8') as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
    rc_s, o_s = run([PY, os.path.join(HAR, 'selfcheck.py'), '--json', 'bad_content.json', '--claims', 'claims.json',
                     '--mode', 'status'], cwd=d)
    sc_ok = rc_s != 0 and tail(o_s, 1).startswith('FIX') and 'hype_hard' in o_s and 'unregistered' in o_s
    node = shutil.which('node')
    if not node or not has_docx(node, nenv):
        return rec('harness', 'gate-catches', 'PASS' if sc_ok else 'FAIL',
                   'selfcheck 가 과장어, 미등록 수치를 잡음 (docx 없음 : 게이트 단계 생략)' if sc_ok else tail(o_s, 8),
                   time.time() - t0)
    e = dict(nenv)
    e['PROFILE'] = os.path.join(out_dir, 'profile.json')
    rc_b, o_b = run([node, os.path.join(HAR, 'build_docx.js'), 'bad_content.json', 'bad.docx'], cwd=d, env=e, timeout=300)
    run([PY, os.path.join(GFR, 'gate_report.py'), '--docx', 'bad.docx', '--lang', 'kr', '--skill-dir', GFR,
         '--claims', 'claims.json', '--out', 'bad_gate.json'], cwd=d)
    try:
        g = json.load(open(os.path.join(d, 'bad_gate.json'), encoding='utf-8'))
    except (OSError, ValueError):
        g = {}
    gates = g.get('gates', {})
    gate_ok = rc_b == 0 and g.get('pass') is False and gates.get('content') == 'fail' and gates.get('claims') == 'fail'
    ok = sc_ok and gate_ok
    rec('harness', 'gate-catches', 'PASS' if ok else 'FAIL',
        'selfcheck FIX, 게이트 content=fail, claims=fail (과장어, 미등록 수치 1,234,567)' if ok else
        'selfcheck %s, build rc=%d, gates %s\n%s' % ('OK' if sc_ok else 'X', rc_b, gates, tail(o_s, 4)), time.time() - t0)


# ── deck ──────────────────────────────────────────────────────────────────
def deck(out_dir):
    t0 = time.time()
    try:
        import playwright  # noqa: F401
    except ImportError:
        return rec('deck', 'demo-deck', 'SKIP', 'playwright 없음 (python3 scripts/doctor.py --skill image-deck)')
    d = os.path.join(out_dir, 'deck')
    rc, o = run([PY, os.path.join(DECK, 'examples', 'demo_deck.py'), '--out', d, '--example-profile'],
                cwd=out_dir, timeout=900)
    want = ['image_deck_demo_slides.pdf', 'image_deck_demo_slides.pptx', 'image_deck_demo_PNG.zip', 'qa_report.json']
    miss = [w for w in want if not os.path.isfile(os.path.join(d, w))]
    if rc != 0 or miss:
        return rec('deck', 'demo-deck', 'FAIL', '종료코드 %d, 없는 파일 %s\n%s' % (rc, miss, tail(o)), time.time() - t0)
    qa = json.load(open(os.path.join(d, 'qa_report.json'), encoding='utf-8'))
    pages = qa.get('pages', [])
    n_err = qa.get('errors', None)
    if not isinstance(n_err, int):
        n_err = sum(len(p.get('errors', [])) if isinstance(p.get('errors'), list) else int(p.get('errors') or 0)
                    for p in pages)
    with zipfile.ZipFile(os.path.join(d, 'image_deck_demo_PNG.zip')) as z:
        n_png = sum(1 for x in z.namelist() if x.lower().endswith('.png'))
    ok = n_err == 0 and n_png > 0
    rec('deck', 'demo-deck', 'PASS' if ok else 'FAIL',
        'PNG %d장, QA 오류 %d, PDF·PPTX·zip 생성' % (n_png, n_err), time.time() - t0)


# ── core ──────────────────────────────────────────────────────────────────
def core(out_dir):
    t0 = time.time()
    d = os.path.join(out_dir, 'core')
    os.makedirs(d, exist_ok=True)
    claims = {'topic': '가상의 A사 판매', 'claims': [
        {'id': 'C1', 'text': 'A사 2025년 판매량 1,250대', 'type': 'numeric', 'value': '1,250', 'status': 'verified',
         'source': 'A사 사업보고서(가상)', 'url': 'https://example.com/a/2025'},
        {'id': 'C2', 'text': 'A사 점유율 34%', 'type': 'numeric', 'value': '34', 'status': 'estimate',
         'source': '판매량으로 계산(가상)'},
        {'id': 'C3', 'text': 'A사 매출 980억 원', 'type': 'numeric', 'value': '980', 'status': 'removed',
         'source': '원문에서 찾지 못함'},
    ]}
    with open(os.path.join(d, 'claims.json'), 'w', encoding='utf-8') as f:
        json.dump(claims, f, ensure_ascii=False, indent=2)
    good = '가상의 A사는 2025년에 1,250대를 팔았음. 점유율은 34%로 추정됨.\n'
    bad = good + '매출은 980억 원이고 영업이익은 4,321만 원임. 점유율 34%는 업계 1위 수준임.\n'
    lite = os.path.join(CORE, 'verify_claims_lite.py')
    res = {}
    for name, text in (('good', good), ('bad', bad)):
        with open(os.path.join(d, name + '.md'), 'w', encoding='utf-8') as f:
            f.write(text)
        res[name] = run([PY, lite, '--claims', 'claims.json', '--text', name + '.md'], cwd=d)
    (rc_g, o_g), (rc_b, o_b) = res['good'], res['bad']
    caught = [k for k in ('REMOVED_LEAK', 'NUM_UNREG') if k in o_b]
    ok = rc_g == 0 and rc_b == 1 and len(caught) == 2
    rec('core', 'claims-lite', 'PASS' if ok else 'FAIL',
        '맞는 초안 통과, 틀린 초안에서 %s 검출' % ', '.join(caught) if ok else
        'good rc=%d, bad rc=%d\n%s\n%s' % (rc_g, rc_b, tail(o_g, 4), tail(o_b, 6)), time.time() - t0)


# ── plugin ────────────────────────────────────────────────────────────────
def plugin_validate():
    t0 = time.time()
    claude = shutil.which('claude')
    if not claude:
        return rec('plugin', 'validate', 'SKIP', 'Claude Code CLI 없음 (claude.ai 업로드만 쓸 때는 필요 없음)')
    rc, o = run([claude, 'plugin', 'validate', '--strict', ROOT], timeout=300)
    passed = rc == 0 and 'passed' in o.lower()
    rec('plugin', 'validate', 'PASS' if passed else 'FAIL',
        'claude plugin validate --strict 통과' if passed else tail(o, 12), time.time() - t0)


# ── main ──────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='insight-full-report 설치 자가 시험')
    ap.add_argument('--only', default='', help='쉼표로 고른 묶음 : ' + ','.join(GROUPS))
    ap.add_argument('--out', default=None, help='작업 폴더 (기본 : 임시 폴더)')
    ap.add_argument('--keep', action='store_true', help='끝난 뒤 작업 폴더를 남김')
    ap.add_argument('--render', action='store_true', help='LibreOffice 로 PDF 변환까지 확인')
    ap.add_argument('--deny', default=os.environ.get('SELFTEST_DENY'), help='추가 금지 낱말 파일(한 줄에 하나)')
    a = ap.parse_args()
    groups = [g.strip() for g in a.only.split(',') if g.strip()] or GROUPS
    bad = [g for g in groups if g not in GROUPS]
    if bad:
        ap.error('모르는 묶음 : %s (가능 : %s)' % (', '.join(bad), ', '.join(GROUPS)))

    out_dir = os.path.abspath(a.out) if a.out else tempfile.mkdtemp(prefix='ifr-selftest-')
    os.makedirs(out_dir, exist_ok=True)
    prof = os.path.join(out_dir, 'profile.json')
    with open(prof, 'w', encoding='utf-8') as f:
        json.dump(PROFILE, f, ensure_ascii=False, indent=2)
    deny_terms = []
    if a.deny:
        with open(a.deny, encoding='utf-8') as f:
            deny_terms = [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]

    print('insight-full-report selftest : %s %s, Python %s' % (SYS, platform.release(), platform.python_version()))
    print('저장소 : %s' % ROOT)
    print('작업 폴더 : %s' % out_dir)
    print('묶음 : %s' % ', '.join(groups))
    t_all = time.time()

    if 'static' in groups:
        st_manifest()
        st_frontmatter()
        st_refs()
        st_lexicon()
        st_dash()
        st_privacy(deny_terms)
        st_syntax(out_dir)
        st_package()
    nenv = node_env() if ('gfr' in groups or 'harness' in groups) else {}
    if 'gfr' in groups:
        for lang in ('kr', 'en'):
            gfr_pptx(out_dir, prof, lang, a.render)
        for lang in ('kr', 'en'):
            gfr_word(out_dir, prof, lang, nenv, a.render)
        gfr_negative(out_dir)
        gfr_cp949(out_dir)
    if 'harness' in groups:
        harness(out_dir, prof, nenv, a.render)
        harness_negative(out_dir, nenv)
    if 'deck' in groups:
        deck(out_dir)
    if 'core' in groups:
        core(out_dir)
    if 'plugin' in groups:
        plugin_validate()

    cnt = {s: sum(1 for r in RESULTS if r['status'] == s) for s in ('PASS', 'FAIL', 'SKIP')}
    rep = {'system': SYS, 'python': platform.python_version(), 'root': ROOT, 'groups': groups,
           'counts': cnt, 'seconds': round(time.time() - t_all, 1), 'results': RESULTS}
    with open(os.path.join(out_dir, 'selftest_report.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print('\n결과 : PASS %d, FAIL %d, SKIP %d (%.0f초)' % (cnt['PASS'], cnt['FAIL'], cnt['SKIP'], time.time() - t_all))
    if cnt['SKIP']:
        print('SKIP 은 그 기능에 필요한 프로그램이 없다는 뜻. python3 scripts/doctor.py 로 설치 안내를 봄.')
    if cnt['FAIL'] or a.keep or a.out:
        print('작업 폴더를 남김 : %s' % out_dir)
    else:
        shutil.rmtree(out_dir, ignore_errors=True)
    sys.exit(1 if cnt['FAIL'] else 0)


if __name__ == '__main__':
    main()
