#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doctor.py : insight-full-report 실행 환경 점검

설치한 뒤 가장 먼저 돌려 보는 스크립트. 스킬마다 필요한 프로그램·패키지·글꼴이 있는지 보고,
없으면 설치 명령을 알려 줌. 아무것도 설치하거나 바꾸지 않음.

사용:
  python3 scripts/doctor.py                      # 전체
  python3 scripts/doctor.py --skill image-deck   # 한 스킬만
  python3 scripts/doctor.py --json report.json   # 결과를 JSON 으로도 저장

종료코드: 0 = 고른 스킬에 꼭 필요한 것이 모두 있음, 1 = 빠진 것이 있음
"""
import argparse
import glob
import json
import os
import platform
import shutil
import subprocess
import sys

SKILLS = ['generate-full-report', 'image-deck', 'report-harness', 'quality-core']
SYS = platform.system()  # Linux, Darwin, Windows


def run(cmd, timeout=60, env=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def hint(linux=None, mac=None, win=None, any_=None):
    if any_:
        return any_
    return {'Linux': linux, 'Darwin': mac, 'Windows': win}.get(SYS) or linux or any_ or ''


def check_python():
    ok = sys.version_info >= (3, 9)
    return ok, 'Python %s' % platform.python_version(), hint(
        linux='sudo apt install python3', mac='brew install python', win='winget install Python.Python.3.12')


def check_node():
    node = shutil.which('node')
    if not node:
        return False, 'node 없음', hint(linux='sudo apt install nodejs npm (또는 nvm 으로 Node 18 이상)',
                                       mac='brew install node', win='winget install OpenJS.NodeJS.LTS')
    rc, out = run([node, '--version'])
    try:
        major = int(out.strip().lstrip('v').split('.')[0])
    except ValueError:
        major = 0
    return major >= 18, 'node %s' % out.strip(), 'Node 18 이상으로 올림'


def npm_root():
    npm = shutil.which('npm')
    if not npm:
        return None
    rc, out = run([npm, 'root', '-g'])
    return out.strip().splitlines()[-1] if rc == 0 and out.strip() else None


def check_docx():
    node = shutil.which('node')
    if not node:
        return False, 'node 없음', 'node 를 먼저 설치'
    env = dict(os.environ)
    root = npm_root()
    if root:
        env['NODE_PATH'] = root + (os.pathsep + env['NODE_PATH'] if env.get('NODE_PATH') else '')
    # docx 9.x 는 package.json 의 exports 때문에 require('docx/package.json') 이 막힘 : 진입 파일에서 위로 올라가며 찾음
    js = ("require('docx');const fs=require('fs'),path=require('path');let d=path.dirname(require.resolve('docx')),v='';"
          "while(d!==path.dirname(d)){const f=path.join(d,'package.json');"
          "if(fs.existsSync(f)){const j=JSON.parse(fs.readFileSync(f,'utf8'));if(j.name==='docx'){v=j.version;break;}}d=path.dirname(d);}"
          "console.log(v||'?')")
    rc, out = run([node, '-e', js], env=env)
    if rc == 0:
        return True, 'docx %s (NODE_PATH=%s)' % (out.strip().splitlines()[-1], root or '기본'), ''
    return False, 'npm 패키지 docx 없음', 'npm install -g docx  (실행할 때 NODE_PATH="$(npm root -g)")'


def check_module(mod, label, fix):
    try:
        m = __import__(mod)
        ver = getattr(m, '__version__', '')
        return True, '%s %s' % (label, ver), ''
    except Exception:  # noqa: BLE001 : 어떤 import 오류든 '없음' 으로 보고
        return False, '%s 없음' % label, fix


def check_chromium():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:  # noqa: BLE001
        return False, 'playwright 없음', 'python3 -m pip install playwright && python3 -m playwright install chromium'
    code = ('from playwright.sync_api import sync_playwright\n'
            'with sync_playwright() as p:\n'
            '    b = p.chromium.launch(); pg = b.new_page(); pg.set_content("<p>ok</p>"); print(pg.inner_text("p")); b.close()\n')
    rc, out = run([sys.executable, '-c', code], timeout=120)
    if rc == 0 and 'ok' in out:
        return True, 'chromium 실행 확인', ''
    fix = 'python3 -m playwright install chromium'
    if SYS == 'Linux':
        fix += '  (라이브러리 부족 오류면 : python3 -m playwright install --with-deps chromium)'
    return False, 'chromium 실행 실패 : ' + out.splitlines()[-1][:120] if out else 'chromium 실행 실패', fix


def check_korean_font():
    names = ('Noto Sans CJK KR', 'Noto Sans KR', 'NanumGothic', 'Malgun Gothic', 'Apple SD Gothic Neo')
    fc = shutil.which('fc-list')
    if fc:
        rc, out = run([fc, ':lang=ko', 'family'])
        hits = [n for n in names if n.lower() in out.lower()]
        if hits:
            return True, '한글 글꼴 : ' + ', '.join(hits), ''
    pats = []
    if SYS == 'Darwin':
        pats = ['/System/Library/Fonts/AppleSDGothicNeo*', '/Library/Fonts/*Noto*CJK*', os.path.expanduser('~/Library/Fonts/*Noto*')]
    elif SYS == 'Windows':
        pats = [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'malgun*.ttf')]
    else:
        pats = ['/usr/share/fonts/**/*NotoSansCJK*', '/usr/share/fonts/**/*Nanum*', os.path.expanduser('~/.fonts/*Nanum*')]
    for p in pats:
        if glob.glob(p, recursive=True):
            return True, '한글 글꼴 파일 : ' + os.path.basename(glob.glob(p, recursive=True)[0]), ''
    return False, '한글 글꼴 없음', hint(linux='sudo apt install fonts-noto-cjk',
                                        mac='macOS 기본 Apple SD Gothic Neo 가 있으면 됨 (없으면 brew install --cask font-noto-sans-cjk-kr)',
                                        win='Windows 기본 맑은 고딕(Malgun Gothic)이 있으면 됨')


def check_bash():
    b = shutil.which('bash')
    if SYS == 'Windows':
        cands = [os.path.join(os.environ.get(k, ''), 'Git', 'bin', 'bash.exe')
                 for k in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)')]
        cands.append(os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Git', 'bin', 'bash.exe'))
        found = next((c for c in cands if os.path.isfile(c)), None)
        if found:
            return True, 'Git Bash : %s (PPTX 빌드는 Git Bash 에서 PYTHON=python 으로 실행)' % found, ''
        if b and 'system32' not in b.lower():
            return True, 'bash : %s' % b, ''
        return False, 'Git Bash 없음 (WSL 의 bash 는 Windows 경로를 그대로 못 씀)', 'winget install Git.Git'
    return (True, 'bash : %s' % b, '') if b else (False, 'bash 없음', hint(linux='sudo apt install bash', mac='macOS 기본 bash 또는 zsh 의 bash'))


def check_tool(name, label, fix):
    path = shutil.which(name)
    return (True, '%s : %s' % (label, path), '') if path else (False, '%s 없음' % label, fix)


CHECKS = [
    # (이름, 함수, 꼭 필요한 스킬, 있으면 좋은 스킬)
    ('python', check_python, SKILLS, []),
    ('node', check_node, ['generate-full-report', 'report-harness'], []),
    ('docx', check_docx, ['generate-full-report', 'report-harness'], []),
    ('bash', check_bash, ['generate-full-report'], []),
    ('pillow', lambda: check_module('PIL', 'Pillow', 'python3 -m pip install Pillow'), ['generate-full-report', 'image-deck'], []),
    ('chromium', check_chromium, ['image-deck'], ['report-harness']),
    ('img2pdf', lambda: check_module('img2pdf', 'img2pdf', 'python3 -m pip install img2pdf'), ['image-deck'], ['report-harness']),
    ('python-pptx', lambda: check_module('pptx', 'python-pptx', 'python3 -m pip install python-pptx'), ['image-deck'], ['report-harness']),
    ('korean-font', check_korean_font, ['image-deck'], ['generate-full-report', 'report-harness']),
    ('soffice', lambda: check_tool('soffice', 'LibreOffice', hint(linux='sudo apt install libreoffice-writer libreoffice-impress', mac='brew install --cask libreoffice', win='winget install TheDocumentFoundation.LibreOffice')), [], ['generate-full-report', 'report-harness']),
    ('claude-cli', lambda: check_tool('claude', 'Claude Code CLI', 'npm install -g @anthropic-ai/claude-code'), [], ['generate-full-report']),
]


def main():
    ap = argparse.ArgumentParser(description='insight-full-report 실행 환경 점검')
    ap.add_argument('--skill', choices=SKILLS + ['all'], default='all')
    ap.add_argument('--json', dest='json_out')
    a = ap.parse_args()
    targets = SKILLS if a.skill == 'all' else [a.skill]

    rows, missing_required = [], []
    for name, fn, req, opt in CHECKS:
        need = [s for s in req if s in targets]
        nice = [s for s in opt if s in targets]
        if not need and not nice:
            continue
        ok, detail, fix = fn()
        level = '필수' if need else '선택'
        status = 'OK' if ok else ('MISSING' if need else 'OPTIONAL')
        rows.append({'check': name, 'status': status, 'level': level, 'detail': detail,
                     'fix': '' if ok else fix, 'skills': need or nice})
        if not ok and need:
            missing_required.append(name)

    print('insight-full-report doctor : %s %s, Python %s' % (SYS, platform.release(), platform.python_version()))
    print('대상 스킬 : %s' % ', '.join(targets))
    w = max(len(r['check']) for r in rows)
    for r in rows:
        mark = {'OK': 'OK  ', 'MISSING': 'FAIL', 'OPTIONAL': 'SKIP'}[r['status']]
        print('  [%s] %-*s  %s  (%s : %s)' % (mark, w, r['check'], r['detail'], r['level'], ', '.join(r['skills'])))
        if r['fix']:
            print('         설치 : %s' % r['fix'])
    if a.json_out:
        with open(a.json_out, 'w', encoding='utf-8') as f:
            json.dump({'system': SYS, 'targets': targets, 'checks': rows}, f, ensure_ascii=False, indent=2)
    if missing_required:
        print('\n결과 : 꼭 필요한 항목 %d개가 빠짐 (%s). 위 설치 명령을 실행한 뒤 다시 확인하세요.'
              % (len(missing_required), ', '.join(missing_required)))
        sys.exit(1)
    print('\n결과 : 고른 스킬을 실행할 준비가 됨.')


if __name__ == '__main__':
    main()
