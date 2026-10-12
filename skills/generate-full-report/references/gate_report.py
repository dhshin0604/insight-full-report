#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_report.py: 통합 게이트 v1.0 (Lifecycles + eValuations 단일 진실원)

한 번 호출로 다음을 합쳐 하나의 머신 리더블 판정을 만든다:
  1) verify_toc.py       : 구조(TOC ↔ 본문) 게이트, PPTX 만
  2) verify_content.py   : 내용 품질 게이트(규칙 기반)
  3) verify_claims.py    : 수치-출처(Deep Verification) 게이트, claims.json 이 있을 때
  4) judge_verdict.json  : LLM-judge 주관 품질 게이트(옵션)

산출물 gate_report.json:
  {
    "pass": false,
    "gates": {"toc": "...", "content": "...", "claims": "...", "judge": "..."},
    "fixes": [ {type, loc, detail, fix}, ... ]   # 재시도 루프가 그대로 소비
  }

판정 원칙 (v1.0):
  - 게이트가 돌지 못하면(스크립트 없음, 비정상 종료, 리포트 없음, 대상 파일 없음) 통과가 아니라 fail(GATE_ERROR).
    skip 은 "그 게이트를 쓸 이유가 없음"(Word 의 toc, claims.json 미제공, judge 미제공)일 때만 씀
  - 하위 스크립트 출력은 UTF-8 로 읽음. Windows 의 cp949 콘솔·파이프에서도 멈추지 않음

사용:
  python3 gate_report.py --unpacked unpacked_kr --lang kr \
      --skill-dir <references_dir> [--claims claims.json] \
      [--judge judge_verdict.json] --out gate_report.json
  python3 gate_report.py --docx 보고서.docx --lang kr --skill-dir <references_dir> --claims claims.json

종료코드: 0 = 통과, 1 = 게이트 실패, 2 = 대상 파일 문제(검사 불가)
"""
import sys, os, json, subprocess, argparse, tempfile, zipfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

CHILD_ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')


def _sub(cmd):
    """하위 게이트 실행 : 출력은 UTF-8 로 읽고, 못 읽는 바이트는 바꿔 넣음(멈추지 않음)."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', env=CHILD_ENV)
    except OSError as e:
        return subprocess.CompletedProcess(cmd, 127, '', str(e))


def _tail(p, n=4):
    out = ((p.stdout or '') + '\n' + (p.stderr or '')).strip().splitlines()
    return ' / '.join(x.strip() for x in out[-n:] if x.strip())[:400]


def _gate_error(name, detail, fix):
    return ('fail', detail, [{'type': 'GATE_ERROR', 'loc': name, 'detail': detail, 'fix': fix}])


def check_target(unpacked, docx):
    """검사할 대상이 실제로 있고 열리는지 먼저 확인. 문제가 있으면 문구를 돌려줌."""
    if unpacked:
        if not os.path.isfile(os.path.join(unpacked, 'ppt', 'presentation.xml')):
            return 'unpacked 폴더가 없거나 PPTX 구조가 아님 : %s (ppt/presentation.xml 없음)' % unpacked
        return ''
    if not os.path.isfile(docx):
        return 'DOCX 파일 없음 : %s' % docx
    try:
        with zipfile.ZipFile(docx) as z:
            if 'word/document.xml' not in z.namelist():
                return 'DOCX 가 아님(word/document.xml 없음) : %s' % docx
    except zipfile.BadZipFile:
        return 'DOCX 가 아님(zip 이 아님) : %s' % docx
    return ''


def run_toc(skill_dir, unpacked):
    vt = _find_script(skill_dir, 'verify_toc.py')
    if not vt:
        return _gate_error('toc', 'verify_toc.py 없음', 'generate-full-report/references 전체를 함께 설치')
    p = _sub([sys.executable, vt, unpacked])
    if p.returncode not in (0, 1):
        return _gate_error('toc', 'verify_toc 비정상 종료(%d) : %s' % (p.returncode, _tail(p)),
                           '오류 내용을 고친 뒤 다시 실행')
    ok = (p.returncode == 0)
    fixes = []
    if not ok:
        for ln in (p.stdout or '').splitlines():
            if ln.strip().startswith('❌'):
                fixes.append({'type': 'TOC', 'loc': 'slide2/본문',
                              'detail': ln.strip().lstrip('❌ '),
                              'fix': '먼저 본문 챕터 슬라이드가 빠졌는지 확인(N_CONTENT 와 빌드 스크립트의 슬라이드 수). '
                                     '본문이 맞으면 TOC(slide2) 로마숫자 챕터를 본문 z1 라벨과 1:1 로 맞춤'})
        if not fixes:
            fixes.append({'type': 'TOC', 'loc': 'slide2/본문',
                          'detail': 'verify_toc 실패 : %s' % _tail(p, 2), 'fix': 'TOC↔본문 챕터 정합성 확인'})
    return ('ok' if ok else 'fail',
            p.stdout.strip().splitlines()[-1] if (p.stdout or '').strip() else '', fixes)


def _find_script(skill_dir, name):
    s = os.path.join(skill_dir, name)
    if not os.path.isfile(s):
        s = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    return s if os.path.isfile(s) else None


def _run_json_gate(name, cmd):
    """--json 리포트를 내는 게이트 스크립트 공용 러너. 리포트가 없으면 fail(GATE_ERROR)."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(path)  # 스크립트가 직접 만들게 비워 둠 : 남아 있으면 리포트를 썼다는 뜻
    p = _sub(cmd + ['--json', path])
    try:
        with open(path, encoding='utf-8') as f:
            rep = json.load(f)
        if not isinstance(rep, dict) or 'pass' not in rep:
            raise ValueError('리포트 형식이 아님')
    except (OSError, ValueError) as e:
        return _gate_error(name, '%s 게이트가 리포트를 내지 못함(종료코드 %d) : %s %s'
                           % (name, p.returncode, e.__class__.__name__, _tail(p)),
                           '위 오류(입력 파일 형식, 인코딩, 경로)를 고친 뒤 다시 실행. 게이트가 돌지 못한 결과는 통과로 보지 않음')
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if p.returncode not in (0, 1) or (rep.get('pass') and p.returncode != 0):
        return _gate_error(name, '%s 게이트 비정상 종료(%d) : %s' % (name, p.returncode, _tail(p)),
                           '오류 내용을 고친 뒤 다시 실행. 통과 리포트를 쓰고 비정상 종료한 결과는 믿지 않음')
    fixes = [{'type': e.get('type'), 'loc': e.get('loc'), 'detail': e.get('detail'), 'fix': e.get('fix')}
             for e in rep.get('errors', [])]
    return ('ok' if rep.get('pass') else 'fail', 'ERROR %d / WARNING %d'
            % (len(rep.get('errors', [])), len(rep.get('warnings', []))), fixes)


def run_content(skill_dir, unpacked, docx, lang):
    vc = _find_script(skill_dir, 'verify_content.py')
    if not vc:
        return _gate_error('content', 'verify_content.py 없음', 'generate-full-report/references 전체를 함께 설치')
    cmd = [sys.executable, vc, '--lang', lang]
    cmd += (['--unpacked', unpacked] if unpacked else ['--docx', docx])
    return _run_json_gate('content', cmd)


def run_claims(skill_dir, unpacked, docx, lang, claims):
    """claims.json 이 주어지면 수치-출처 게이트 실행."""
    if not claims:
        return ('skip', 'claims.json 미제공', [])
    if not os.path.isfile(claims):
        return ('fail', 'claims.json 경로 없음: %s' % claims,
                [{'type': 'CLAIMS_MISSING', 'loc': claims,
                  'detail': 'Claims Ledger 파일 없음',
                  'fix': 'Phase 2.7에서 claims.json 생성 (factcheck-pipeline.md)'}])
    try:
        with open(claims, encoding='utf-8-sig') as f:
            led = json.load(f)
        if not isinstance(led, dict) or not isinstance(led.get('claims'), list):
            raise ValueError('최상위가 {"claims": [...]} 형식이 아님')
    except (OSError, ValueError) as e:
        return ('fail', 'claims.json 을 읽지 못함 : %s' % e,
                [{'type': 'CLAIMS_INVALID', 'loc': claims, 'detail': str(e)[:200],
                  'fix': 'factcheck-pipeline.md 의 형식 {"topic": ..., "claims": [{id, text, value, status, source}]} 으로 다시 씀'}])
    vc = _find_script(skill_dir, 'verify_claims.py')
    if not vc:
        return _gate_error('claims', 'verify_claims.py 없음', 'generate-full-report/references 전체를 함께 설치')
    cmd = [sys.executable, vc, '--claims', claims, '--lang', lang]
    cmd += (['--unpacked', unpacked] if unpacked else ['--docx', docx])
    return _run_json_gate('claims', cmd)


def run_judge(path):
    """LLM-judge 결과 파일(있으면). 형식: {"pass":bool,"fixes":[{type,loc,detail,fix}]}"""
    if not path:
        return ('skip', 'judge 미제공', [])
    try:
        with open(path, encoding='utf-8-sig') as f:
            v = json.load(f)
        if not isinstance(v, dict) or 'pass' not in v:
            raise ValueError('{"pass": bool, ...} 형식이 아님')
    except (OSError, ValueError) as e:
        return _gate_error('judge', 'judge 결과를 읽지 못함 : %s' % e,
                           'quality_rubric.md 의 judge 출력 형식으로 judge_verdict.json 을 다시 씀')
    return ('ok' if v.get('pass') else 'fail',
            v.get('summary', ''), v.get('fixes', []))


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--unpacked')
    g.add_argument('--docx')
    ap.add_argument('--lang', default='kr', choices=['kr', 'en'])
    ap.add_argument('--skill-dir', default='.')
    ap.add_argument('--claims', help='claims.json (Deep Verification ledger)')
    ap.add_argument('--judge')
    ap.add_argument('--out', default='gate_report.json')
    a = ap.parse_args()

    target = a.unpacked or a.docx
    problem = check_target(a.unpacked, a.docx)
    if problem:
        report = {'pass': False, 'lang': a.lang, 'target': target, 'gates': {'target': 'fail'},
                  'fixes': [{'type': 'GATE_ERROR', 'loc': target, 'detail': problem,
                             'fix': '빌드가 끝났는지, 경로가 맞는지 확인한 뒤 다시 실행'}]}
        with open(a.out, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('═══ GATE REPORT (%s) ═══' % target)
        print('  ❌ 검사 불가 : %s' % problem)
        print('  -> %s' % a.out)
        sys.exit(2)

    # claims 기본값: cwd 의 claims.json 자동 감지
    claims = a.claims or ('claims.json' if os.path.isfile('claims.json') else None)

    gates, fixes = {}, []

    if a.unpacked:  # TOC 게이트는 PPTX 에만 적용
        s, msg, fx = run_toc(a.skill_dir, a.unpacked)
        gates['toc'] = s
        fixes += fx
    else:
        gates['toc'] = 'skip'

    s, msg, fx = run_content(a.skill_dir, a.unpacked, a.docx, a.lang)
    gates['content'] = s
    fixes += fx

    s, msg, fx = run_claims(a.skill_dir, a.unpacked, a.docx, a.lang, claims)
    gates['claims'] = s
    fixes += fx

    s, msg, fx = run_judge(a.judge)
    gates['judge'] = s
    fixes += fx

    overall = all(v in ('ok', 'skip') for v in gates.values())
    report = {'pass': overall, 'lang': a.lang,
              'target': target, 'gates': gates, 'fixes': fixes}
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print('═══ GATE REPORT (%s) ═══' % target)
    for k, v in gates.items():
        icon = {'ok': '✅', 'fail': '❌', 'skip': '·'}[v]
        print('  %s %-8s %s' % (icon, k, v))
    print('  fixes: %d 건' % len(fixes))
    for x in fixes:
        if x.get('type') == 'GATE_ERROR':
            print('  ❌ GATE_ERROR %s : %s' % (x.get('loc'), x.get('detail')))
    print('  -> %s' % a.out)
    if not overall:
        print('\n💥 GATE FAILED: fixes[] 를 적용해 재빌드 필요')
        sys.exit(1)
    print('\n✅ ALL GATES PASSED')
    sys.exit(0)


if __name__ == '__main__':
    main()
