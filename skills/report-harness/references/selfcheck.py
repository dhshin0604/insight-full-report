#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfcheck.py : 원고 자체 점검기 (report-harness)

사용
  python3 selfcheck.py content_front content_ch1 content_ch2 [--mode status|analysis] [--lang kr|en]
  python3 selfcheck.py --json content.json [--claims claims.json] [--mode ...] [--lang ...]

  모듈 이름은 작업 폴더에서 import 하고, 경로(.../content_ch1.py)를 주면 그 파일을 읽음
  --mode     status   = 현황 단계 : 평가어(lexicon eval_terms)도 오류로 잡음
             analysis = 분석, 진단, 제언 단계 : 평가어는 검사하지 않음 (기본)
  --lang     kr | en (없으면 META.lang, 그것도 없으면 kr)
  --claims   --json 일 때 대조할 claims.json (없으면 content.json 옆의 claims.json)
  --lexicon  금지어 사전 경로 (없으면 이 파일 옆 lexicon.json)
  --report   결과를 JSON 으로도 씀 : {"pass", "errors": [{type, loc, detail, fix}], "warnings": [...]}
  --strict   경고 항목도 오류로 셈 (kr 줄표처럼 lexicon 이 경고로 둔 것을 막고 싶을 때)

검사 (규칙의 정본은 lexicon.json 과 generate-full-report 의 verify_content.py, verify_claims.py)
  schema           content-schema.md 형식                                        오류
  auto_number      빌드가 붙이는 번호(1., 1.1, Q1., A., [그림 1], [표 1], ①, [1])를 원고에 씀  오류
  bullets          bullet 문자와 가운뎃점                                          오류
  cjk_bare         괄호 바로 뒤가 아닌 한자, 가나 (en 은 경고)                       오류
  dates            Word 날짜 형식 위반 : 2026-10-12, 2026.10.12, 2026. 10. 12, 2026.10   오류
  hype_hard        과장 표현                                                      오류
  hype_soft        완화 대상 표현                                                  경고
  eval_terms       평가어 (status 모드만)                                          오류
  ai_tone          AI 티 문형                                                     경고
  pointer          장과 장을 잇는 가리킴                                            오류
  self_commentary  필자 자기 해설                                                  오류
  user_banned      팀 고유 금지 표현                                               오류
  dash             줄표 (lexicon dash.level 의 언어별 수준)                          오류 또는 경고
  quotes           작은따옴표, 큰따옴표 (kr 만, 「」 로 바꿈)                         오류
  placeholder      {자리표시}, TODO, TBD 잔존                                       오류
  table            열 5 이하, widths 합 9026, 행 14 이하, 셀 60자 이하                오류
  unregistered     CLAIMS 에 없는 수치 (연도 단독, 12 이하 정수는 제외)               오류
                   (모듈 점검 때는 assemble 이 넣을 메타 claim Z001~Z004 도 등록된 것으로 봄)
  estimate_mark    estimate 수치 앞뒤 30자 안에 「추정」 없음                         오류
  removed_leak     removed claim 의 값이 본문에 남음                                오류
  claim_ids        id 없음, id 중복, 메타 예약 접두어 Z 사용                         오류
  claim_status     status 가 verified, estimate, removed 가 아님                    오류
  claim_source     verified claim 에 source, url 둘 다 없음                         경고

출력 : 항목마다 OK(통과) / !!(오류) / ~~(경고, FIX 수에 넣지 않음) / --(검사 안 함),
       마지막 줄 PASS 또는 FIX n (n = 오류가 난 항목 수. 바로 윗줄에 오류 건수와 항목 이름)
종료코드 : 0 PASS / 1 FIX / 2 실행 오류
"""
import argparse
import json
import os
import re
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

ORDER = ["schema", "auto_number", "bullets", "cjk_bare", "dates", "hype_hard", "hype_soft", "eval_terms",
         "ai_tone", "pointer", "self_commentary", "user_banned", "dash", "quotes", "placeholder", "table",
         "unregistered", "estimate_mark", "removed_leak"]
CLAIM_ORDER = ["claim_ids", "claim_status", "claim_source"]

FIX = {
    "schema": "content-schema.md 의 필드 이름과 형식에 맞춤",
    "auto_number": "제목, 질문, 답변, 캡션, 라벨 앞의 번호를 지움 (빌드가 1., 1.1, Q1., A., [그림 1], [표 1], ①, [1] 을 붙임)",
    "bullets": "bullet 과 가운뎃점을 쉼표, 「와/과」, 문장으로 바꿈",
    "cjk_bare": "한자, 가나는 한글로 쓰고 원문은 괄호 바로 안에 둠 : 인공지능(人工知能)",
    "dates": "Word 날짜는 「2026년 10월 12일」(en : October 12, 2026) 형식으로 씀",
    "hype_hard": "과장 표현을 지우고 수치나 사실로 바꿈",
    "hype_soft": "필요한 곳만 남김",
    "eval_terms": "현황 단계에서는 평가어를 쓰지 않고 셀 수 있는 사실로 씀",
    "ai_tone": "문형을 바꿔 다시 씀",
    "pointer": "다른 장을 가리키지 않고 장마다 자기 결론으로 끝냄",
    "self_commentary": "필자 자기 해설 문장을 지움",
    "user_banned": "팀 금지 표현을 다른 말로 바꿈",
    "dash": "줄표를 콜론, 쉼표, 괄호로 바꿈",
    "quotes": "따옴표를 「」 로 바꿈",
    "placeholder": "브리프 뼈대의 자리표시와 TODO 를 실제 내용으로 채움",
    "table": "열 5개 이하, widths 합 9026(W() 헬퍼), 행 14개 이하, 셀 60자 이하로 나눔",
    "unregistered": "수치를 CLAIMS 에 등록하거나(claim 의 value 또는 text) 본문에서 뺌",
    "estimate_mark": "estimate 수치 앞뒤 30자 안에 「추정」(en : est.)을 적음",
    "removed_leak": "removed claim 의 값을 본문에서 지움",
    "claim_ids": "claim id 를 겹치지 않게 바꾸고 Z 로 시작하는 id 는 쓰지 않음(메타 claim 용)",
    "claim_status": "status 는 verified, estimate, removed 셋 중 하나로 씀",
    "claim_source": "verified claim 에 source 나 url 을 적음",
}

CJK_RE = re.compile("[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+")
CJK_OK_BEFORE = ("(", "\uff08", "/", "\u00b7", "\uff0c")  # verify_content._bare_cjk_tokens 와 같음
DATE_FULL = re.compile(r"(?<![\d.])(?:19|20)\d{2}\s*[.\-/]\s*(?:0?[1-9]|1[0-2])\s*[.\-/]\s*"
                       r"(?:0?[1-9]|[12]\d|3[01])(?!\d)")
DATE_YM = re.compile(r"(?<![\d.])(?:19|20)\d{2}[.\-/](?:0?[1-9]|1[0-2])"
                     r"(?![\d.\-/%]|\s*(?:억|만|조|천|원|배|명|건|개|대|곳|회|점|위|분|시간|달러|위안|엔))")
QUOTE_CHARS = ["'", '"', "\u2018", "\u2019", "\u201c", "\u201d"]
PLACEHOLDER_RE = re.compile(r"\{[^{}\n]{1,40}\}|\b(?:TODO|TBD|FIXME|XXX)\b")
TITLE_NUM_RE = re.compile(r"^\s*(?:제\s*\d+\s*[장절]|(?:chapter|section)\s+\d+|\d+\.(?:\d+\.?)*\s|[IVX]+\.\s)", re.I)
QNUM_RE = re.compile(r"^\s*Q\s*\d+", re.I)
ANUM_RE = re.compile(r"^\s*(?:A|답)\s*[.:]", re.I)
CAPNUM_RE = re.compile(r"^\s*(?:\[\s*(?:그림|표|figure|fig\.?|table)\s*\d+\s*\]|(?:그림|표|figure|table)\s*\d+\s*[.:])", re.I)
LABELNUM_RE = re.compile("^\\s*(?:[\u2460-\u2473]|\\d+[.)]\\s)")
REFNUM_RE = re.compile(r"^\s*\[\d+\]")


def die(msg):
    print("[오류] " + msg, file=sys.stderr)
    sys.exit(2)


def load_lexicon(path=None):
    cands = [path] if path else [os.path.join(HERE, "lexicon.json"),
                                 os.path.join(HERE, "..", "..", "generate-full-report", "references", "lexicon.json")]
    for p in cands:
        if p and os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return json.load(f), os.path.abspath(p)
            except ValueError as e:
                die("lexicon.json 을 읽지 못함 (%s): %s" % (p, e))
    die("lexicon.json 을 찾지 못함 : %s (--lexicon 으로 지정)" % ", ".join(c for c in cands if c))


def terms(lex, key, lang):
    v = lex.get(key, {})
    if isinstance(v, dict):
        v = v.get(lang, [])
    return [w for w in (v or []) if isinstance(w, str) and w]


def strip_corner(s):
    return re.sub("「[^」]*」", "", s)


def find_terms(text, words, lang, boundary):
    """kr 은 부분 문자열, en 은 대소문자 무시. boundary=True 면 en 단어 경계로 찾음(s, es, ed, ing 어미는 허용)."""
    hits = []
    low = text.lower()
    for w in words:
        if lang == "en":
            if boundary:
                if re.search(r"(?<![A-Za-z])" + re.escape(w.lower()) + r"(?:s|es|d|ed|ing)?(?![A-Za-z])", low):
                    hits.append(w)
            elif w.lower() in low:
                hits.append(w)
        elif w in text:
            hits.append(w)
    return hits


def short(s, n=40):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + "..."


class Unit(object):
    """점검 단위 하나(모듈 하나 또는 content.json)."""

    def __init__(self, name, content, partial):
        self.name = name
        self.content = content
        self.partial = partial
        self.body = [(loc, t) for loc, t in wb.iter_texts(content) if isinstance(t, str) and t.strip()]
        self.refs = [(loc, t) for loc, t in wb.iter_ref_texts(content) if isinstance(t, str) and t.strip()]
        self.found = {k: [] for k in ORDER}
        self.level = {k: "error" for k in ORDER}


def run_text_checks(u, lex, lang, mode, reg, est, removed, have_claims):
    f = u.found
    all_txt = u.body + u.refs

    errs, warns = wb.validate_document(u.content, partial=u.partial)
    f["schema"] += [("", e) for e in errs]
    for w in warns:
        f.setdefault("_schema_warn", []).append(("", w))

    # 빌드가 붙이는 번호를 원고에 직접 쓴 경우
    c = u.content
    for ci, ch in enumerate(wb._as_list(c.get("chapters")), 1):
        if not isinstance(ch, dict):
            continue
        if TITLE_NUM_RE.match(str(ch.get("title", ""))):
            f["auto_number"].append(("장%d 제목" % ci, short(ch.get("title"))))
        for si, s in enumerate(wb._as_list(ch.get("sections")), 1):
            if not isinstance(s, dict):
                continue
            if TITLE_NUM_RE.match(str(s.get("title", ""))):
                f["auto_number"].append(("장%d 절%d 제목" % (ci, si), short(s.get("title"))))
            for bi, b in enumerate(wb._as_list(s.get("blocks")), 1):
                if isinstance(b, dict) and b.get("type") in ("fig", "table") and CAPNUM_RE.match(str(b.get("caption", ""))):
                    f["auto_number"].append(("장%d 절%d 블록%d 캡션" % (ci, si, bi), short(b.get("caption"))))
    for qi, qa in enumerate(wb._as_list(c.get("qa")), 1):
        if isinstance(qa, dict) and QNUM_RE.match(str(qa.get("q", ""))):
            f["auto_number"].append(("Q%d 질문" % qi, short(qa.get("q"))))
        if isinstance(qa, dict) and ANUM_RE.match(str(qa.get("a", ""))):
            f["auto_number"].append(("Q%d 답변" % qi, short(qa.get("a"))))
    for fi, fl in enumerate(wb._as_list((c.get("es") or {}).get("flow")), 1):
        if isinstance(fl, (list, tuple)) and fl and LABELNUM_RE.match(str(fl[0])):
            f["auto_number"].append(("ES 흐름%d 라벨" % fi, short(fl[0])))
    dv = c.get("devils")
    if isinstance(dv, dict):
        if TITLE_NUM_RE.match(str(dv.get("title", ""))):
            f["auto_number"].append(("반론 장 제목", short(dv.get("title"))))
        for ii, it in enumerate(wb._as_list(dv.get("items")), 1):
            if isinstance(it, dict) and LABELNUM_RE.match(str(it.get("claim", ""))):
                f["auto_number"].append(("반론%d 주장" % ii, short(it.get("claim"))))
    for loc, t in u.refs:
        if REFNUM_RE.match(t):
            f["auto_number"].append((loc, short(t)))

    bullets = [b for b in lex.get("bullets", []) if isinstance(b, str) and b]
    dash = lex.get("dash", {}) if isinstance(lex.get("dash"), dict) else {}
    dash_chars = [d for d in dash.get("chars", ["\u2014"]) if isinstance(d, str) and d] or ["\u2014"]
    u.level["dash"] = "warn" if (dash.get("level", {}) or {}).get(lang, "error") == "warn" else "error"
    u.level["hype_soft"] = "warn"
    u.level["ai_tone"] = "warn"
    u.level["cjk_bare"] = "error" if lang == "kr" else "warn"
    if mode != "status":
        u.level["eval_terms"] = "skip"
    if lang != "kr":
        u.level["quotes"] = "skip"
    if not have_claims:
        for k in ("unregistered", "estimate_mark", "removed_leak"):
            u.level[k] = "skip"

    hype_hard, hype_soft = terms(lex, "hype_hard", lang), terms(lex, "hype_soft", lang)
    ev, ai = terms(lex, "eval_terms", lang), terms(lex, "ai_tone", lang)
    pt, sc, ub = terms(lex, "pointer", lang), terms(lex, "self_commentary", lang), terms(lex, "user_banned", lang)

    for loc, t in all_txt:
        bs = sorted({ch for ch in bullets if ch in t})
        if bs:
            f["bullets"].append((loc, "%s : %s" % (" ".join(bs), short(t))))
        for m in CJK_RE.finditer(t):
            if t[max(0, m.start() - 1):m.start()] not in CJK_OK_BEFORE:
                f["cjk_bare"].append((loc, m.group(0)))
        for rx in (DATE_FULL, DATE_YM):
            for m in rx.finditer(t):
                f["dates"].append((loc, m.group(0)))
        for w in find_terms(t, hype_hard, lang, False):
            f["hype_hard"].append((loc, w))
        for w in find_terms(strip_corner(t), hype_soft, lang, False):  # 「」 안 공식 이름은 예외
            f["hype_soft"].append((loc, w))
        for w in find_terms(t, ub, lang, True):
            f["user_banned"].append((loc, w))
        ds = [d for d in dash_chars if d in t]
        if ds:
            f["dash"].append((loc, "U+%04X : %s" % (ord(ds[0][0]), short(t))))
        for m in PLACEHOLDER_RE.finditer(t):
            f["placeholder"].append((loc, m.group(0)))

    for loc, t in u.body:
        if mode == "status":
            for w in find_terms(strip_corner(t), ev, lang, True):
                f["eval_terms"].append((loc, w))
        for w in find_terms(t, ai, lang, True):
            f["ai_tone"].append((loc, w))
        for w in find_terms(t, pt, lang, True):
            f["pointer"].append((loc, w))
        for w in find_terms(t, sc, lang, True):
            f["self_commentary"].append((loc, w))
        if lang == "kr":
            s = strip_corner(t)
            s = re.sub(r"\([^)]*\)", "", s)
            s = re.sub("(?<=[A-Za-z])['\u2019](?=[A-Za-z])", "", s)
            qs = [q for q in QUOTE_CHARS if q in s]
            if qs:
                f["quotes"].append((loc, "%s : %s" % (" ".join(qs), short(t))))

    for loc, tb in wb.iter_tables(c):
        cap = short(tb.get("caption", ""), 20)
        h = wb._as_list(tb.get("headers"))
        rows = wb._as_list(tb.get("rows"))
        w = tb.get("widths")
        if len(h) > 5:
            f["table"].append((loc, "열 %d개 > 5 : %s" % (len(h), cap)))
        if not isinstance(w, list) or len(w) != len(h) or sum(x for x in w if isinstance(x, int)) != wb.TABLE_WIDTH:
            f["table"].append((loc, "widths %r (열 %d개, 합 %d 이어야 함) : %s" % (w, len(h), wb.TABLE_WIDTH, cap)))
        if len(rows) > 14:
            f["table"].append((loc, "행 %d개 > 14 : %s" % (len(rows), cap)))
        for r in rows:
            for cell in wb._as_list(r) + []:
                if len(str(cell)) > 60:
                    f["table"].append((loc, "셀 %d자 > 60 : %s" % (len(str(cell)), short(cell, 25))))
        for x in h:
            if len(str(x)) > 60:
                f["table"].append((loc, "머리 %d자 > 60 : %s" % (len(str(x)), short(x, 25))))

    if have_claims:
        markers = wb.EST_MARKERS.get(lang, wb.EST_MARKERS["kr"])
        for loc, t in u.body:
            for v, ctx in wb.significant_numbers(t):
                if v not in reg:
                    f["unregistered"].append((loc, "%s : %s" % (v, short(ctx, 50))))
                elif v in est and not any(mk in ctx.lower() for mk in markers):
                    f["estimate_mark"].append((loc, "%s : %s" % (v, short(ctx, 50))))
            nt = wb.norm_num(t)
            for c2 in removed:
                key = wb.norm_num(str(c2.get("value", "")))
                if key and key in nt:
                    f["removed_leak"].append((loc, "%s (%s)" % (c2.get("id", "?"), key)))


def check_claims(claims, json_mode):
    out = {k: [] for k in CLAIM_ORDER}
    ids = {}
    for src, c in claims:
        if not isinstance(c, dict):
            out["claim_ids"].append((src, "claim 이 dict 가 아님"))
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not cid.strip():
            out["claim_ids"].append((src, "id 없음 : %s" % short(c.get("text", ""), 30)))
        else:
            ids.setdefault(cid, []).append(src)
            if not json_mode and cid.startswith(wb.META_PREFIX):
                out["claim_ids"].append((src, "%s : %s 로 시작하는 id 는 메타 claim 용" % (cid, wb.META_PREFIX)))
        if c.get("status") not in ("verified", "estimate", "removed"):
            out["claim_status"].append((src, "%s : %r" % (cid, c.get("status"))))
        elif c.get("status") == "verified" and not (c.get("url") or c.get("source")):
            out["claim_source"].append((src, "%s : %s" % (cid, short(c.get("text", ""), 30))))
    for cid, srcs in ids.items():
        if len(srcs) > 1:
            out["claim_ids"].append((", ".join(sorted(set(srcs))), "id 중복 %s (%d번)" % (cid, len(srcs))))
    return out


def ledger_sets(claims):
    reg, est, removed = set(), set(), []
    for _, c in claims:
        if not isinstance(c, dict):
            continue
        st = c.get("status")
        if st == "removed":
            removed.append(c)
        elif st in ("verified", "estimate"):
            vals = wb.claim_values(c)
            reg |= vals
            if st == "estimate":
                est |= vals
    return reg, est, removed


def print_items(found, levels, order, errors, warnings, unit_name, strict=False):
    for k in order:
        lv = levels.get(k, "error")
        if strict and lv == "warn":
            lv = "error"
        items = found.get(k, [])
        if lv == "skip":
            print("  -- %s : 검사 안 함" % k)
            continue
        if not items:
            print("  OK %s" % k)
            continue
        mark = "!!" if lv == "error" else "~~"
        shown = "; ".join(("%s : %s" % (loc, d)) if loc else d for loc, d in items[:6])
        more = " ... 외 %d건" % (len(items) - 6) if len(items) > 6 else ""
        print("  %s %s (%d) %s%s" % (mark, k, len(items), shown, more))
        for loc, d in items:
            rec = {"type": k, "loc": ("%s %s" % (unit_name, loc)).strip(), "detail": d, "fix": FIX.get(k, "")}
            (errors if lv == "error" else warnings).append(rec)


def main():
    ap = argparse.ArgumentParser(description="원고 자체 점검기")
    ap.add_argument("modules", nargs="*", help="원고 모듈 이름 또는 .py 경로")
    ap.add_argument("--json", dest="json_path", help="content.json 을 점검")
    ap.add_argument("--claims", help="--json 과 함께 쓸 claims.json")
    ap.add_argument("--mode", choices=["status", "analysis"], default="analysis")
    ap.add_argument("--lang", choices=["kr", "en"], default=None)
    ap.add_argument("--lexicon", default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--strict", action="store_true",
                    help="경고 항목(hype_soft, ai_tone, kr 줄표, cjk_bare en, claim_source)도 오류로 셈")
    a = ap.parse_args()
    if bool(a.modules) == bool(a.json_path):
        ap.error("원고 모듈 이름들 또는 --json content.json 중 하나만 줌")

    lex, lex_path = load_lexicon(a.lexicon)
    units, claims, json_mode = [], [], bool(a.json_path)
    have_claims = True

    if json_mode:
        try:
            with open(a.json_path, encoding="utf-8") as f:
                content = json.load(f)
        except (OSError, ValueError) as e:
            die("content.json 을 읽지 못함 : %s" % e)
        lang = a.lang or (content.get("meta") or {}).get("lang") or "kr"
        units.append(Unit(os.path.basename(a.json_path), content, partial=False))
        cpath = a.claims or os.path.join(os.path.dirname(os.path.abspath(a.json_path)), "claims.json")
        if os.path.isfile(cpath):
            try:
                with open(cpath, encoding="utf-8") as f:
                    led = json.load(f)
            except (OSError, ValueError) as e:
                die("claims.json 을 읽지 못함 : %s" % e)
            claims = [(os.path.basename(cpath), c) for c in (led.get("claims", []) if isinstance(led, dict) else [])]
        else:
            have_claims = False
            print("[안내] claims.json 이 없어 수치 대조(unregistered, estimate_mark, removed_leak)를 건너뜀 : %s" % cpath)
    else:
        lang = a.lang
        for spec in a.modules:
            try:
                m = wb.load_module(spec)
            except Exception as e:  # ImportError, SyntaxError, FileNotFoundError
                die("원고 모듈을 읽지 못함 (%s) : %s: %s" % (spec, type(e).__name__, e))
            meta = getattr(m, "META", None)
            if lang is None and isinstance(meta, dict) and meta.get("lang") in ("kr", "en"):
                lang = meta["lang"]
            content = {"meta": meta, "es": getattr(m, "ES", None), "qa": getattr(m, "QA", None),
                       "chapters": getattr(m, "CHAPTERS", None), "devils": getattr(m, "DEVILS", None),
                       "closing": getattr(m, "CLOSING", None), "references": getattr(m, "REFERENCES", None)}
            units.append(Unit(os.path.splitext(os.path.basename(spec))[0], content, partial=True))
            for attr in ("CLAIMS", "EXTRA"):
                for c in (getattr(m, attr, None) or []):
                    claims.append(("%s.%s" % (units[-1].name, attr), c))
        lang = lang or "kr"
        # 모듈 단위 점검에서도 assemble.py 가 넣을 메타 claim(Z001~Z004)을 같은 규칙으로 더해 대조함
        merged = {"meta": None, "qa": [], "chapters": [], "devils": None, "references": []}
        for u in units:
            cc = u.content
            if merged["meta"] is None and isinstance(cc.get("meta"), dict):
                merged["meta"] = cc["meta"]
            merged["qa"] += [x for x in (cc.get("qa") or []) if isinstance(x, dict)]
            merged["chapters"] += [x for x in (cc.get("chapters") or []) if isinstance(x, dict)]
            if merged["devils"] is None and isinstance(cc.get("devils"), dict):
                merged["devils"] = cc["devils"]
            merged["references"] += [x for x in (cc.get("references") or []) if isinstance(x, dict)]
        d = (merged["meta"] or {}).get("date")
        ymd = wb.parse_date(d) if d else None
        meta_reg = wb.meta_claims(merged, wb.format_date(ymd or wb.today_ymd(), "kr"))
        reg_extra = set()
        for c in meta_reg:
            reg_extra |= wb.claim_values(c)

    reg, est, removed = ledger_sets(claims)
    if not json_mode:
        reg |= reg_extra
    errors, warnings = [], []
    try:
        lex_show = os.path.relpath(lex_path)
    except ValueError:  # 다른 드라이브(Windows)
        lex_show = lex_path
    if lex_show.startswith(".."):
        lex_show = lex_path
    print("selfcheck : mode=%s lang=%s%s lexicon=%s" % (a.mode, lang, " strict" if a.strict else "", lex_show))
    for u in units:
        run_text_checks(u, lex, lang, a.mode, reg, est, removed, have_claims)
        n_chars = sum(len(t) for _, t in u.body)
        n_tab = sum(1 for _ in wb.iter_tables(u.content))
        n_fig = sum(1 for _ in wb.iter_figs(u.content))
        print("[%s] 글자 %s, 표 %d, 그림 %d, 참고 자료 %d" % (u.name, format(n_chars, ","), n_tab, n_fig, len(u.refs)))
        print_items(u.found, u.level, ORDER, errors, warnings, u.name, a.strict)
        for loc, w in u.found.get("_schema_warn", []):
            print("  ~~ schema 경고 : %s" % w)
            warnings.append({"type": "schema", "loc": u.name, "detail": w, "fix": FIX["schema"]})

    cf = check_claims(claims, json_mode)
    st = {k: sum(1 for _, c in claims if isinstance(c, dict) and c.get("status") == k)
          for k in ("verified", "estimate", "removed")}
    print("[claims] 총 %d : verified %d, estimate %d, removed %d" % (len(claims), st["verified"], st["estimate"], st["removed"]))
    lv = {"claim_ids": "error", "claim_status": "error", "claim_source": "warn"}
    if json_mode and not have_claims:
        lv = {k: "skip" for k in CLAIM_ORDER}
    print_items(cf, lv, CLAIM_ORDER, errors, warnings, "claims", a.strict)

    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            json.dump({"pass": not errors, "mode": a.mode, "lang": lang, "errors": errors, "warnings": warnings},
                      f, ensure_ascii=False, indent=2)
        print("  -> %s" % a.report)

    bad = sorted({e["type"] for e in errors}, key=lambda k: (ORDER + CLAIM_ORDER).index(k))
    if errors:
        print("=> 오류 %d건, 고칠 항목 %d개 (%s), 경고 %d건" % (len(errors), len(bad), ", ".join(bad), len(warnings)))
        print("FIX %d" % len(bad))
        sys.exit(1)
    print("=> 오류 0건, 경고 %d건" % len(warnings))
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
