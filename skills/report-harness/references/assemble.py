#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assemble.py : 원고 모듈(content_*.py) → content.json + claims.json (report-harness)

사용
  python3 assemble.py --front content_front --chapters content_ch1,content_ch2 \\
      --out content.json --claims claims.json --date "2026년 10월 12일"

  --front     META, ES, QA 를 가진 모듈 (CLAIMS, EXTRA 도 읽음)
  --chapters  CHAPTERS 를 가진 모듈들, 쉼표로 구분. 적은 순서대로 장이 이어짐
  --back      (선택) DEVILS, CLOSING, REFERENCES 만 가진 모듈
  --out       content.json 경로 (build_docx.js 입력)
  --claims    claims.json 경로 (gate_report.py --claims 입력)
  --date      작성일. 「2026년 10월 12일」, 2026-10-12, 2026.10.12 모두 받음. 없으면 META.date, 그것도 없으면 오늘
  --lang      kr | en (없으면 META.lang, 그것도 없으면 kr)
  --topic     claims.json 의 topic (없으면 META.topic, 그것도 없으면 제목 줄)

모듈 이름은 작업 폴더에서 import 하고, 경로(…/content_ch1.py)를 주면 그 파일을 읽음.
DEVILS, CLOSING 은 모듈 하나에만 두고, REFERENCES 는 여러 모듈에 나눠 둬도 순서대로 합침.

하는 일
  1) 모듈을 읽어 장을 순서대로 잇고 스키마를 검사함 (wb.validate_document)
  2) FIG 그림 경로를 모듈 폴더 기준으로 찾아 content.json 폴더 기준 상대 경로로 바꿈
  3) claim id 중복, status 오류, 예약 접두어(Z) 사용을 검사함 : 하나라도 있으면 파일을 쓰지 않고 종료코드 1
  4) 빌드가 찍는 수를 메타 claim 으로 자동 등록함 (verify_claims 가 미등록 수치로 잡지 않게, wb.meta_claims)
       Z001 작성일과 META.base_date(조사 기준일) / Z002 헤딩 번호(1.1 등) / Z003 그림, 표, 질문 번호
       / Z004 참고 자료 번호와 서지 정보 안의 수
  5) content.json 과 {"topic": ..., "claims": [...]} 형식의 claims.json 을 씀

종료코드 : 0 성공 / 1 원고 오류 / 2 실행 오류(모듈을 찾지 못함 등)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import wb  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass

META_PREFIX = wb.META_PREFIX
STATUSES = ("verified", "estimate", "removed")


def _get(mod, name, default=None):
    return getattr(mod, name, default)


def _module_dir(mod):
    f = getattr(mod, "__file__", None)
    return os.path.dirname(os.path.abspath(f)) if f else os.getcwd()


def _fix_img(path, mod_dir, out_dir, missing):
    """그림 경로 : 절대 경로면 그대로 확인, 상대 경로면 모듈 폴더 → 작업 폴더 순으로 찾음."""
    if not isinstance(path, str) or not path:
        return path
    if os.path.isabs(path):
        found = path if os.path.isfile(path) else None
    else:
        found = None
        for base in (mod_dir, os.getcwd()):
            cand = os.path.abspath(os.path.join(base, path))
            if os.path.isfile(cand):
                found = cand
                break
    if not found:
        missing.append(path)
        return path
    try:
        rel = os.path.relpath(found, out_dir)
    except ValueError:  # 다른 드라이브(Windows)
        return found
    # content.json 폴더 아래에 있으면 상대 경로(폴더째 옮겨도 됨), 밖에 있으면 절대 경로
    return found if rel.startswith("..") else rel.replace(os.sep, "/")


def _fix_chapter_imgs(chapters, mod_dir, out_dir, missing):
    for ch in chapters or []:
        if not isinstance(ch, dict):
            continue
        for s in ch.get("sections", []) or []:
            if not isinstance(s, dict):
                continue
            for b in s.get("blocks", []) or []:
                if isinstance(b, dict) and b.get("type") == "fig":
                    b["img"] = _fix_img(b.get("img"), mod_dir, out_dir, missing)


def check_claims(all_claims, errs):
    ids = {}
    for src, c in all_claims:
        if not isinstance(c, dict):
            errs.append("%s: claim 이 dict 가 아님" % src)
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not cid.strip():
            errs.append("%s: id 없는 claim (%s)" % (src, str(c.get("text", ""))[:30]))
            continue
        if cid.startswith(META_PREFIX):
            errs.append("%s: %s : %s 로 시작하는 id 는 메타 claim 용으로 비워 둠" % (src, cid, META_PREFIX))
        ids.setdefault(cid, []).append(src)
        if c.get("status") not in STATUSES:
            errs.append("%s: %s status %r (verified, estimate, removed 만 씀)" % (src, cid, c.get("status")))
        if not str(c.get("text", "")).strip():
            errs.append("%s: %s text 없음" % (src, cid))
    for cid, srcs in ids.items():
        if len(srcs) > 1:
            errs.append("claim id 중복 %s : %s" % (cid, ", ".join(srcs)))


def main():
    ap = argparse.ArgumentParser(description="원고 모듈 → content.json + claims.json")
    ap.add_argument("--front", required=True)
    ap.add_argument("--chapters", required=True, help="쉼표로 구분한 모듈 목록")
    ap.add_argument("--back", default=None)
    ap.add_argument("--out", default="content.json")
    ap.add_argument("--claims", default="claims.json")
    ap.add_argument("--date", default=None)
    ap.add_argument("--lang", choices=["kr", "en"], default=None)
    ap.add_argument("--topic", default=None)
    a = ap.parse_args()

    names = [x.strip() for x in a.chapters.split(",") if x.strip()]
    if not names:
        print("[오류] --chapters 에 모듈을 하나 이상 적어야 함", file=sys.stderr)
        sys.exit(2)
    try:
        front = wb.load_module(a.front)
        chmods = [wb.load_module(n) for n in names]
        back = wb.load_module(a.back) if a.back else None
    except Exception as e:  # ImportError, FileNotFoundError, 원고 문법 오류
        print("[오류] 원고 모듈을 읽지 못함 : %s: %s" % (type(e).__name__, e), file=sys.stderr)
        sys.exit(2)

    out_path = os.path.abspath(a.out)
    out_dir = os.path.dirname(out_path)
    errs, warns, missing = [], [], []

    meta = dict(_get(front, "META") or {})
    if not meta:
        errs.append("%s: META 없음" % a.front)
    lang = a.lang or meta.get("lang") or "kr"
    meta["lang"] = lang
    raw_date = a.date or meta.get("date")
    if raw_date:
        ymd = wb.parse_date(raw_date)
        if ymd is None:
            print("[오류] 날짜를 읽을 수 없음 : %r (「2026년 10월 12일」 또는 2026-10-12)" % raw_date, file=sys.stderr)
            sys.exit(1)
    else:
        ymd = wb.today_ymd()
        warns.append("작성일이 없어 오늘 날짜를 씀 (--date 로 지정 가능)")
    meta["date"] = wb.format_date(ymd, lang)
    date_kr = wb.format_date(ymd, "kr")
    if isinstance(meta.get("title_lines"), str):
        meta["title_lines"] = [meta["title_lines"]]
    if meta.get("cover_img"):
        meta["cover_img"] = _fix_img(meta["cover_img"], _module_dir(front), out_dir, missing)

    mods = [(a.front, front)] + list(zip(names, chmods)) + ([(a.back, back)] if back else [])
    chapters, refs, devils, closing = [], [], [], []
    seen_mod = set()
    for label, m in mods:
        if id(m) in seen_mod:
            warns.append("%s: 같은 모듈이 두 번 들어옴 (한 번만 씀)" % label)
            continue
        seen_mod.add(id(m))
        mdir = _module_dir(m)
        chs = _get(m, "CHAPTERS")
        if chs is not None:
            if not isinstance(chs, list):
                errs.append("%s: CHAPTERS 가 목록이 아님" % label)
            else:
                try:
                    chs = json.loads(json.dumps(chs, ensure_ascii=False))  # 원본 모듈 객체를 건드리지 않음
                except (TypeError, ValueError) as e:
                    errs.append("%s: CHAPTERS 에 JSON 으로 바꿀 수 없는 값이 있음 (%s)" % (label, e))
                    continue
                _fix_chapter_imgs(chs, mdir, out_dir, missing)
                chapters.extend(chs)
        elif m in chmods:
            errs.append("%s: CHAPTERS 없음" % label)
        if _get(m, "DEVILS") is not None:
            devils.append((label, _get(m, "DEVILS")))
        if _get(m, "CLOSING") is not None:
            closing.append((label, _get(m, "CLOSING")))
        for r in (_get(m, "REFERENCES") or []):
            refs.append(r)
    if len(devils) > 1:
        errs.append("DEVILS 가 여러 모듈에 있음 : %s (하나만 둠)" % ", ".join(x[0] for x in devils))
    if len(closing) > 1:
        errs.append("CLOSING 이 여러 모듈에 있음 : %s (하나만 둠)" % ", ".join(x[0] for x in closing))
    if not closing:
        errs.append("CLOSING 이 어느 모듈에도 없음 (맺음말)")

    uniq_refs, seen = [], set()
    for r in refs:
        key = (r.get("text"), r.get("url")) if isinstance(r, dict) else (str(r), None)
        if key in seen:
            continue
        seen.add(key)
        uniq_refs.append(r)

    content = {
        "meta": meta,
        "es": _get(front, "ES"),
        "qa": _get(front, "QA") or [],
        "chapters": chapters,
        "closing": closing[0][1] if closing else None,
        "references": uniq_refs,
    }
    if devils:
        content["devils"] = devils[0][1]

    e2, w2 = wb.validate_document(content)
    errs += e2
    warns += w2
    for p in missing:
        errs.append("그림 파일 없음 : %s (모듈 폴더와 작업 폴더에서 찾지 못함)" % p)

    all_claims = []
    for label, m in mods:
        for attr in ("CLAIMS", "EXTRA"):
            for c in (_get(m, attr) or []):
                all_claims.append(("%s.%s" % (label, attr), c))
    check_claims(all_claims, errs)

    if errs:
        print("[assemble] 원고 오류 %d건 : 파일을 쓰지 않음" % len(errs))
        for e in errs:
            print("  !! " + e)
        for w in warns:
            print("  ~~ " + w)
        sys.exit(1)

    claims = [c for _, c in all_claims] + wb.meta_claims(content, date_kr)
    topic = a.topic or meta.get("topic") or " ".join(meta.get("title_lines") or [])
    try:  # 원고에 JSON 으로 바꿀 수 없는 값(set, 객체 등)이 있으면 파일을 쓰기 전에 멈춤
        content_txt = json.dumps(content, ensure_ascii=False, indent=1)
        claims_txt = json.dumps({"topic": topic, "claims": claims}, ensure_ascii=False, indent=1)
    except (TypeError, ValueError) as e:
        print("[assemble] 원고 오류 : JSON 으로 바꿀 수 없는 값이 있음 (%s). 문자열, 숫자, 목록, dict 만 씀" % e)
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content_txt + "\n")
    cpath = os.path.abspath(a.claims)
    os.makedirs(os.path.dirname(cpath), exist_ok=True)
    with open(cpath, "w", encoding="utf-8") as f:
        f.write(claims_txt + "\n")

    plan = wb.render_plan(content)
    st = {k: sum(1 for c in claims if c.get("status") == k) for k in STATUSES}
    print("[assemble] content : %s" % out_path)
    print("[assemble] claims  : %s" % cpath)
    print("  장 %d (반론 장 %s), 절 %d, 그림 %d, 표 %d, 질문 %d, 참고 자료 %d" % (
        plan["chapters"], "있음" if plan["devils"] else "없음", plan["sections"], plan["figures"],
        plan["tables"], plan["questions"], plan["references"]))
    print("  claims 총 %d : verified %d, estimate %d, removed %d (메타 claim %d 포함)" % (
        len(claims), st["verified"], st["estimate"], st["removed"],
        sum(1 for c in claims if str(c.get("id", "")).startswith(META_PREFIX))))
    print("  작성일 %s, 언어 %s" % (meta["date"], lang))
    for w in warns:
        print("  ~~ " + w)
    if st["estimate"]:
        print("  확인 : estimate 수치 옆에는 본문에 「추정」을 적어야 함 (verify_claims EST_UNMARKED)")
    print("다음 : node build_docx.js %s <out.docx>" % a.out)


if __name__ == "__main__":
    main()
