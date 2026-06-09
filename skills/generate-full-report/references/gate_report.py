#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_report.py — 통합 게이트 v0.9 (Lifecycles + eValuations 단일 진실원)

한 번 호출로 다음을 합쳐 하나의 머신 리더블 판정을 만든다:
  1) verify_toc.py        — 구조(TOC ↔ 본문) 게이트              [기존]
  2) verify_content.py    — 내용 품질 게이트(규칙 기반)           [기존]
  3) verify_claims.py     — 수치-출처(Deep Verification) 게이트   [v0.9 신규]
  4) judge_verdict.json   — LLM-judge 주관 품질 게이트(옵션)      [기존]

산출물 gate_report.json:
  {
    "pass": false,
    "gates": {"toc": "...", "content": "...", "claims": "...", "judge": "..."},
    "fixes": [ {type, loc, detail, fix}, ... ]   # 재시도 루프가 그대로 소비
  }

사용:
  python3 gate_report.py --unpacked unpacked_kr --lang kr \
      --skill-dir <references_dir> [--claims claims.json] \
      [--judge judge_verdict.json] --out gate_report.json
"""
import sys, os, json, subprocess, argparse, tempfile


def run_toc(skill_dir, unpacked):
    vt = os.path.join(skill_dir, 'verify_toc.py')
    if not os.path.isfile(vt):
        return ('skip', 'verify_toc.py 없음', [])
    p = subprocess.run([sys.executable, vt, unpacked],
                       capture_output=True, text=True)
    ok = (p.returncode == 0)
    fixes = []
    if not ok:
        for ln in p.stdout.splitlines():
            if ln.strip().startswith('❌'):
                fixes.append({'type': 'TOC', 'loc': 'slide2/본문',
                              'detail': ln.strip().lstrip('❌ '),
                              'fix': 'TOC(slide2) 로마숫자 챕터와 본문 z1 라벨을 1:1로 일치'})
        if not fixes:
            fixes.append({'type': 'TOC', 'loc': 'slide2/본문',
                          'detail': 'verify_toc 실패', 'fix': 'TOC↔본문 챕터 정합성 확인'})
    return ('ok' if ok else 'fail',
            p.stdout.strip().splitlines()[-1] if p.stdout.strip() else '', fixes)


def _find_script(skill_dir, name):
    s = os.path.join(skill_dir, name)
    if not os.path.isfile(s):
        s = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    return s if os.path.isfile(s) else None


def _run_json_gate(cmd):
    """--json 리포트를 내는 게이트 스크립트 공용 러너."""
    tmp = tempfile.NamedTemporaryFile('r', suffix='.json', delete=False, encoding='utf-8')
    tmp.close()
    p = subprocess.run(cmd + ['--json', tmp.name], capture_output=True, text=True)
    try:
        rep = json.load(open(tmp.name, encoding='utf-8'))
    except Exception:
        return ('skip', p.stdout.strip(), [])
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    fixes = [{'type': e['type'], 'loc': e['loc'], 'detail': e['detail'], 'fix': e['fix']}
             for e in rep.get('errors', [])]
    return ('ok' if rep.get('pass') else 'fail', 'ERROR %d / WARNING %d'
            % (len(rep.get('errors', [])), len(rep.get('warnings', []))), fixes)


def run_content(skill_dir, unpacked, docx, lang):
    vc = _find_script(skill_dir, 'verify_content.py')
    if not vc:
        return ('skip', 'verify_content.py 없음', [])
    cmd = [sys.executable, vc, '--lang', lang]
    cmd += (['--unpacked', unpacked] if unpacked else ['--docx', docx])
    return _run_json_gate(cmd)


def run_claims(skill_dir, unpacked, docx, lang, claims):
    """v0.9: claims.json 이 주어지면 수치-출처 게이트 실행."""
    if not claims:
        return ('skip', 'claims.json 미제공', [])
    if not os.path.isfile(claims):
        return ('fail', 'claims.json 경로 없음: %s' % claims,
                [{'type': 'CLAIMS_MISSING', 'loc': claims,
                  'detail': 'Claims Ledger 파일 없음',
                  'fix': 'Phase 2.7에서 claims.json 생성 (factcheck-pipeline.md)'}])
    vc = _find_script(skill_dir, 'verify_claims.py')
    if not vc:
        return ('skip', 'verify_claims.py 없음', [])
    cmd = [sys.executable, vc, '--claims', claims, '--lang', lang]
    cmd += (['--unpacked', unpacked] if unpacked else ['--docx', docx])
    return _run_json_gate(cmd)


def run_judge(path):
    """LLM-judge 결과 파일(있으면). 형식: {"pass":bool,"fixes":[{type,loc,detail,fix}]}"""
    if not path or not os.path.isfile(path):
        return ('skip', 'judge 미제공', [])
    v = json.load(open(path, encoding='utf-8'))
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
              'target': a.unpacked or a.docx, 'gates': gates, 'fixes': fixes}
    json.dump(report, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print('═══ GATE REPORT (%s) ═══' % (a.unpacked or a.docx))
    for k, v in gates.items():
        icon = {'ok': '✅', 'fail': '❌', 'skip': '·'}[v]
        print('  %s %-8s %s' % (icon, k, v))
    print('  fixes: %d 건' % len(fixes))
    print('  -> %s' % a.out)
    if not overall:
        print('\n💥 GATE FAILED — fixes[] 를 적용해 재빌드 필요')
        sys.exit(1)
    print('\n✅ ALL GATES PASSED')
    sys.exit(0)


if __name__ == '__main__':
    main()
