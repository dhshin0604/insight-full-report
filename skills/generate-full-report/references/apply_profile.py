#!/usr/bin/env python3
"""apply_profile.py — 프로필 플레이스홀더 일괄 치환 + 잔존 검사 (handoff edition)

정본 템플릿과 TEMPLATE.pptx 의 레이아웃/맺음말에는 작성자·연락처가 하드코딩되어
있지 않고 아래 키를 중괄호로 감싼 플레이스홀더로 들어 있다. 이 스크립트가
references/profile.json 의 값으로 치환하고, 하나라도 남아 있으면 종료코드 2 로
빌드를 중단시킨다.

  AUTHOR_KR   한글 성명            예) 홍길동
  AUTHOR_EN   영문 성명            예) Gildong Hong
  PHONE_KR    국내 표기 전화번호   예) 010-0000-0000
  PHONE_EN    국제 표기 전화번호   예) +82-10-0000-0000
  EMAIL       이메일               예) name@example.com
  (Phase 0 저장 경로용) WORKSPACE_ROOT  WORKSPACE_DIRNAME

사용법:
  python3 references/apply_profile.py build_kr.js build_en.js            # docx 빌드 스크립트
  python3 references/apply_profile.py unpacked_kr/ppt                    # 디렉터리(재귀: .xml .js .py)
  python3 references/apply_profile.py --profile ./profile.json FILE...   # 프로필 파일 직접 지정
  python3 references/apply_profile.py --set AUTHOR_KR=홍길동 --set EMAIL=a@b.c FILE...
  python3 references/apply_profile.py --check FILE...                    # 치환 없이 잔존만 검사
  python3 references/apply_profile.py --which                            # 어떤 profile.json 이 쓰이는지만 출력

프로필 파일 자동 선택 순서 (--profile 을 주지 않았을 때):
  1) 환경변수 PROFILE 이 가리키는 파일
  2) 현재 작업 폴더의 ./profile.json      ← 스킬 폴더가 읽기 전용일 때 여기에 만들면 된다
  3) 이 스크립트 옆의 references/profile.json
  필수 5개 키(AUTHOR_KR AUTHOR_EN PHONE_KR PHONE_EN EMAIL)가 모두 채워진 파일을 우선 고르고,
  그런 파일이 없으면 존재하는 첫 번째 파일을 골라 무엇이 비었는지 알려 준다.

값 우선순위: --set > 환경변수 PROFILE_<KEY> > 위에서 고른 프로필 파일
build_pptx.sh 는 슬라이드 작성 직후 unpacked_<lang>/ppt 전체에 이 스크립트를 자동 적용한다.
"""
import argparse
import json
import os
import re
import sys

REQUIRED = ['AUTHOR_KR', 'AUTHOR_EN', 'PHONE_KR', 'PHONE_EN', 'EMAIL']
OPTIONAL = ['WORKSPACE_ROOT', 'WORKSPACE_DIRNAME']
KEYS = REQUIRED + OPTIONAL
TOKEN_RE = re.compile(r'\{(' + '|'.join(KEYS) + r')\}')
EXTS = ('.xml', '.js', '.py', '.rels', '.ps1', '.sh')
HERE = os.path.dirname(os.path.abspath(__file__))


def _read(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def resolve_profile_path(explicit=None):
    """쓸 profile.json 을 고른다. 필수 키가 모두 찬 파일 > 존재하는 첫 파일."""
    if explicit:
        return explicit
    cands = [c for c in (os.environ.get('PROFILE'),
                         os.path.join(os.getcwd(), 'profile.json'),
                         os.path.join(HERE, 'profile.json')) if c]
    existing = [c for c in cands if os.path.isfile(c)]
    for c in existing:
        d = _read(c)
        if d and all(str(d.get(k, '')).strip() for k in REQUIRED):
            return c
    return existing[0] if existing else os.path.join(HERE, 'profile.json')


def load_profile(path, sets):
    prof = {k: '' for k in KEYS}
    if path and os.path.isfile(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        for k in KEYS:
            v = data.get(k, '')
            prof[k] = str(v).strip() if v is not None else ''
    for k in KEYS:
        env = os.environ.get(f'PROFILE_{k}')
        if env:
            prof[k] = env.strip()
    for kv in sets:
        if '=' not in kv:
            sys.exit(f'--set 형식 오류: {kv} (KEY=VALUE)')
        k, v = kv.split('=', 1)
        if k not in KEYS:
            sys.exit(f'알 수 없는 키: {k} (허용: {", ".join(KEYS)})')
        prof[k] = v.strip()
    return prof


def iter_files(targets):
    for t in targets:
        if os.path.isdir(t):
            for root, _, names in os.walk(t):
                for n in sorted(names):
                    if n.lower().endswith(EXTS):
                        yield os.path.join(root, n)
        elif os.path.isfile(t):
            yield t
        else:
            sys.exit(f'대상을 찾을 수 없음: {t}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('targets', nargs='*', help='파일 또는 디렉터리')
    ap.add_argument('--profile', default=None, help='프로필 파일 직접 지정 (생략하면 자동 선택)')
    ap.add_argument('--set', dest='sets', action='append', default=[], metavar='KEY=VALUE')
    ap.add_argument('--check', action='store_true', help='치환하지 않고 잔존 플레이스홀더만 검사')
    ap.add_argument('--which', action='store_true', help='선택된 프로필 경로만 출력하고 종료')
    args = ap.parse_args()

    args.profile = resolve_profile_path(args.profile)
    if args.which:
        print(args.profile)
        return
    if not args.targets:
        ap.error('대상 파일/디렉터리를 하나 이상 지정하세요 (또는 --which).')

    prof = load_profile(args.profile, args.sets)
    filled = {k: v for k, v in prof.items() if v}
    replaced = {}
    leftovers = {}

    for path in iter_files(args.targets):
        try:
            with open(path, encoding='utf-8') as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        if not TOKEN_RE.search(text):
            continue
        new = text
        if not args.check:
            for k, v in filled.items():
                cnt = new.count('{' + k + '}')
                if cnt:
                    new = new.replace('{' + k + '}', v)
                    replaced[k] = replaced.get(k, 0) + cnt
            if new != text:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new)
        left = sorted(set(TOKEN_RE.findall(new)))
        if left:
            leftovers[path] = left

    if replaced:
        print('apply_profile: 치환 완료 — ' + ', '.join(f'{k}×{n}' for k, n in replaced.items()))
    elif not args.check:
        print('apply_profile: 치환할 플레이스홀더 없음 (이미 치환됨)')

    if leftovers:
        missing = sorted({k for ks in leftovers.values() for k in ks})
        print('❌ apply_profile: 플레이스홀더 잔존 — 프로필 값이 비어 있습니다: ' + ', '.join(missing))
        for p, ks in leftovers.items():
            print(f'     {p}: {" ".join("{" + k + "}" for k in ks)}')
        print(f'   → 사용된 프로필 파일: {args.profile}')
        print( '   → 해결: (a) 작업 폴더에 profile.json 을 만들어 값을 채우거나')
        print( '           (b) --set AUTHOR_KR=... --set EMAIL=... 처럼 직접 전달하거나')
        print( '           (c) PROFILE=/경로/profile.json 환경변수로 다른 파일을 지정')
        sys.exit(2)
    print('✅ apply_profile: 잔존 플레이스홀더 0건')


if __name__ == '__main__':
    main()
