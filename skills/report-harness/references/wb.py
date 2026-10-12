# -*- coding: utf-8 -*-
"""wb.py : Word 원고 헬퍼 (report-harness)

원고 모듈(content_front.py, content_ch1.py ...)이 블록을 만들 때 쓰는 함수 모음임.
블록과 문서 스키마는 content-schema.md 를 따름.

원고 모듈 예
    from wb import *
    CHAPTERS = [
        chapter("장 제목", [
            sec("절 제목", "KEY MESSAGE 한두 문장", [
                P("단락"),
                TBL("표 캡션", ["구분", "값"], [["A", "35"]], W(1, 2), source="출처"),
            ]),
        ]),
    ]
    CLAIMS = [claim("C101", "본문에 나온 사실 한 줄", "numeric", "35", "출처", "https://...")]

selfcheck.py 와 assemble.py 가 이 파일이 있는 폴더를 import 경로에 넣으므로
작업 폴더에 wb.py 를 복사하지 않아도 원고 모듈이 import 됨.

파일 아래쪽(「도구용」 표시)은 selfcheck.py, assemble.py 가 함께 쓰는 함수임.
`from wb import *` 로는 원고 모듈에 들어가지 않음.
"""
import datetime
import importlib
import importlib.util
import os
import re
import sys

TABLE_WIDTH = 9026  # A4 본문 폭(twip). 표 widths 합은 이 값이어야 함

__all__ = ["P", "FIG", "TBL", "BOX", "QUOTE", "NOTE", "W", "chapter", "sec", "claim", "TABLE_WIDTH"]


# ─── 원고용 블록 헬퍼 ─────────────────────────────────────────────────────────

def P(text):
    """본문 단락 하나."""
    return {"type": "p", "text": text}


def FIG(img, caption, source=None):
    """그림. img 는 PNG 경로(content.json 이 놓일 폴더 기준 상대 경로 권장)."""
    b = {"type": "fig", "img": img, "caption": caption}
    if source:
        b["source"] = source
    return b


def W(*ratios):
    """표 열 폭. 비율을 받아 합이 정확히 9026 인 정수 목록을 돌려줌. W(1, 2, 2) 또는 W([1, 2, 2])."""
    if len(ratios) == 1 and isinstance(ratios[0], (list, tuple)):
        ratios = tuple(ratios[0])
    if not ratios or any((not isinstance(r, (int, float))) or isinstance(r, bool) or r <= 0 for r in ratios):
        raise ValueError("W() 에는 양수 비율을 하나 이상 넣어야 함")
    total = float(sum(ratios))
    out = [int(TABLE_WIDTH * r / total) for r in ratios]
    out[-1] += TABLE_WIDTH - sum(out)
    return out


def TBL(caption, headers, rows, widths=None, source=None):
    """표. widths 를 비우면 열 폭을 똑같이 나눔(합 9026)."""
    b = {"type": "table", "caption": caption, "headers": list(headers),
         "rows": [list(r) for r in rows],
         "widths": list(widths) if widths else W(*([1] * max(1, len(headers))))}
    if source:
        b["source"] = source
    return b


def BOX(title, paras):
    """제목이 있는 박스. paras 는 문자열 또는 문자열 목록."""
    return {"type": "box", "title": title, "paras": [paras] if isinstance(paras, str) else list(paras)}


def QUOTE(text, sub=None):
    """인용. text 는 「」로 감싸 쓰는 것을 권장, sub 는 인용 출처 한 줄."""
    b = {"type": "quote", "text": text}
    if sub:
        b["sub"] = sub
    return b


def NOTE(text):
    """작은 회색 주석 한 줄(기준일, 집계 범위 등)."""
    return {"type": "note", "text": text}


def chapter(title, sections, intro=None):
    """장. 제목에 번호를 쓰지 않음(빌드가 「1. 」을 붙임)."""
    return {"title": title, "intro": [intro] if isinstance(intro, str) else list(intro or []),
            "sections": list(sections)}


def sec(title, key_message, blocks):
    """절. 제목에 번호를 쓰지 않음(빌드가 「1.1 」을 붙임). key_message 는 KEY MESSAGE 박스 문장."""
    return {"title": title, "key_message": key_message, "blocks": list(blocks)}


def claim(cid, text, kind, value, source, url="", status="verified", method="web", note=""):
    """Claims Ledger 한 줄. status 는 verified, estimate, removed 셋 중 하나."""
    return {"id": cid, "text": text, "kind": kind, "value": value, "source": source, "url": url,
            "status": status, "method": method, "note": note}


# ─── 도구용 : 원고 모듈 불러오기 ──────────────────────────────────────────────

def load_module(spec):
    """'content_ch1' 같은 모듈 이름(작업 폴더에서 찾음) 또는 'path/to/content_ch1.py' 경로를 불러옴."""
    is_path = spec.endswith(".py") or os.sep in spec or "/" in spec
    if is_path:
        path = os.path.abspath(spec if spec.endswith(".py") else spec + ".py")
        if not os.path.isfile(path):
            raise FileNotFoundError("원고 모듈 파일 없음: %s" % path)
        name = os.path.splitext(os.path.basename(path))[0]
        folder = os.path.dirname(path)
        if folder not in sys.path:
            sys.path.insert(0, folder)
        sp = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(sp)
        sys.modules[name] = mod
        sp.loader.exec_module(mod)
        return mod
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    return importlib.import_module(spec)


# ─── 도구용 : 날짜 ────────────────────────────────────────────────────────────

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
_DATE_KR = re.compile(r"^\s*(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*$")
_DATE_NUM = re.compile(r"^\s*(\d{4})\s*[-./]\s*(\d{1,2})\s*[-./]\s*(\d{1,2})\s*\.?\s*$")
_DATE_EN = re.compile(r"^\s*([A-Za-z]+)\.?\s+(\d{1,2}),\s*(\d{4})\s*$")


def parse_date(s):
    """「2026년 10월 12일」, 2026-10-12, 2026.10.12, 「October 12, 2026」 을 (y, m, d) 로. 못 읽으면 None."""
    if not isinstance(s, str):
        return None
    m = _DATE_KR.match(s) or _DATE_NUM.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = _DATE_EN.match(s)
        if not m:
            return None
        names = [x.lower() for x in MONTHS_EN]
        key = m.group(1).lower()
        hit = [i for i, n in enumerate(names) if n == key or (len(key) >= 3 and n.startswith(key))]
        if not hit:
            return None
        y, mo, d = int(m.group(3)), hit[0] + 1, int(m.group(2))
    try:
        datetime.date(y, mo, d)
    except ValueError:
        return None
    return y, mo, d


def format_date(ymd, lang):
    """Word 표기 : kr 「2026년 10월 12일」, en 「October 12, 2026」. build_docx.js 와 같은 규칙."""
    y, m, d = ymd
    if lang == "en":
        return "%s %d, %d" % (MONTHS_EN[m - 1], d, y)
    return "%d년 %d월 %d일" % (y, m, d)


def today_ymd():
    t = datetime.date.today()
    return t.year, t.month, t.day


# ─── 도구용 : 수치 규칙 (generate-full-report/references/verify_claims.py 와 같게 유지) ──

NUM_RE = re.compile(r"\d[\d,]*\.?\d*")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")
PHONE_RE = re.compile(r"(\+?82|010)[-\d]{8,}")
EST_MARKERS = {"kr": ["추정", "전망치", "외삽"], "en": ["est.", "estimate", "projected", "extrapolat"]}


def norm_num(s):
    return s.replace(",", "").rstrip(".")


def number_tokens(text):
    """문장 안의 모든 수(쉼표 뺀 정규화 값) 집합."""
    return {norm_num(x) for x in NUM_RE.findall(text or "")}


def is_significant_token(v):
    """verify_claims 가 등록을 요구하는 값인지 : 연도 단독 아님, 12 이하 정수 아님(소수는 모두 해당)."""
    if YEAR_RE.match(v):
        return False
    try:
        f = float(v)
    except ValueError:
        return False
    return not (f <= 12 and "." not in v)


def significant_numbers(text):
    """verify_claims.significant_numbers 와 같은 규칙. [(값, 앞뒤 30자 문맥)]"""
    text = PHONE_RE.sub(" ", text or "")
    out = []
    for m in NUM_RE.finditer(text):
        v = norm_num(m.group(0))
        if YEAR_RE.match(v):
            continue
        try:
            f = float(v)
        except ValueError:
            continue
        if f <= 12 and "." not in v and "%" not in text[m.end():m.end() + 1]:
            continue
        out.append((v, text[max(0, m.start() - 30): m.end() + 30]))
    return out


def claim_values(c):
    """claim 하나가 등록하는 값 집합(value 와 text 안의 수, 연도 제외). verify_claims 와 같은 규칙."""
    vals = NUM_RE.findall(str(c.get("value", ""))) + NUM_RE.findall(str(c.get("text", "")))
    return {norm_num(v) for v in vals if not YEAR_RE.match(norm_num(v))}


# ─── 도구용 : 문서 훑기 ───────────────────────────────────────────────────────

def _as_list(v):
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    return [v]


def iter_texts(c):
    """빌드가 본문에 그대로 찍는 작성자 문자열을 (위치, 문자열) 로 돌려줌.
    meta.date 와 references 는 빼고 돌려줌(각각 Z001, Z004 메타 claim 이 맡음)."""
    meta = c.get("meta") or {}
    for i, t in enumerate(_as_list(meta.get("title_lines")), 1):
        yield ("표지 제목%d" % i, t)
    if meta.get("subtitle"):
        yield ("표지 부제", meta["subtitle"])
    es = c.get("es") or {}
    for k in ("key_message", "background"):
        if es.get(k):
            yield ("ES %s" % k, es[k])
    for i, f in enumerate(_as_list(es.get("flow")), 1):
        if isinstance(f, (list, tuple)):
            for j, part in enumerate(f):
                yield ("ES 흐름%d %s" % (i, "라벨" if j == 0 else "문장"), part)
    for k in ("next", "outlook"):
        if es.get(k):
            yield ("ES %s" % k, es[k])
    for i, qa in enumerate(_as_list(c.get("qa")), 1):
        if isinstance(qa, dict):
            yield ("Q%d 질문" % i, qa.get("q", ""))
            yield ("Q%d 답변" % i, qa.get("a", ""))
    for ci, ch in enumerate(_as_list(c.get("chapters")), 1):
        if not isinstance(ch, dict):
            continue
        yield ("장%d 제목" % ci, ch.get("title", ""))
        for k, t in enumerate(_as_list(ch.get("intro")), 1):
            yield ("장%d 도입%d" % (ci, k), t)
        for si, s in enumerate(_as_list(ch.get("sections")), 1):
            if not isinstance(s, dict):
                continue
            sl = "장%d 절%d" % (ci, si)
            yield (sl + " 제목", s.get("title", ""))
            if s.get("key_message"):
                yield (sl + " KEY MESSAGE", s["key_message"])
            for bi, b in enumerate(_as_list(s.get("blocks")), 1):
                if not isinstance(b, dict):
                    continue
                bl = "%s 블록%d(%s)" % (sl, bi, b.get("type"))
                t = b.get("type")
                if t in ("p", "note"):
                    yield (bl, b.get("text", ""))
                elif t == "quote":
                    yield (bl, b.get("text", ""))
                    if b.get("sub"):
                        yield (bl + " 출처줄", b["sub"])
                elif t == "fig":
                    yield (bl + " 캡션", b.get("caption", ""))
                    if b.get("source"):
                        yield (bl + " 출처줄", b["source"])
                elif t == "table":
                    yield (bl + " 캡션", b.get("caption", ""))
                    for h in _as_list(b.get("headers")):
                        yield (bl + " 머리", str(h))
                    for ri, r in enumerate(_as_list(b.get("rows")), 1):
                        for cell in _as_list(r):
                            yield ("%s %d행" % (bl, ri), str(cell))
                    if b.get("source"):
                        yield (bl + " 출처줄", b["source"])
                elif t == "box":
                    yield (bl + " 제목", b.get("title", ""))
                    for k, t2 in enumerate(_as_list(b.get("paras")), 1):
                        yield ("%s 단락%d" % (bl, k), t2)
    dv = c.get("devils")
    if isinstance(dv, dict):
        yield ("반론 장 제목", dv.get("title", ""))
        for k, t in enumerate(_as_list(dv.get("intro")), 1):
            yield ("반론 도입%d" % k, t)
        for i, it in enumerate(_as_list(dv.get("items")), 1):
            if isinstance(it, dict):
                yield ("반론%d 주장" % i, it.get("claim", ""))
                yield ("반론%d 검토" % i, it.get("counter", ""))
    cl = c.get("closing")
    if isinstance(cl, dict):
        if cl.get("title"):
            yield ("맺음말 제목", cl["title"])
        if cl.get("key_sentence"):
            yield ("맺음말 핵심 문장", cl["key_sentence"])
        for k, t in enumerate(_as_list(cl.get("paras")), 1):
            yield ("맺음말 단락%d" % k, t)
        for k, pv in enumerate(_as_list(cl.get("perspectives")), 1):
            if isinstance(pv, (list, tuple)):
                for j, part in enumerate(pv):
                    yield ("맺음말 관점%d %s" % (k, "라벨" if j == 0 else "문장"), part)
        for k, kw in enumerate(_as_list(cl.get("keywords")), 1):
            yield ("맺음말 키워드%d" % k, kw)


def iter_ref_texts(c):
    for i, r in enumerate(_as_list(c.get("references")), 1):
        if isinstance(r, dict) and r.get("text"):
            yield ("참고 자료%d" % i, r["text"])


def iter_tables(c):
    for ci, ch in enumerate(_as_list(c.get("chapters")), 1):
        if not isinstance(ch, dict):
            continue
        for si, s in enumerate(_as_list(ch.get("sections")), 1):
            if not isinstance(s, dict):
                continue
            for bi, b in enumerate(_as_list(s.get("blocks")), 1):
                if isinstance(b, dict) and b.get("type") == "table":
                    yield ("장%d 절%d 블록%d" % (ci, si, bi), b)


def iter_figs(c):
    meta = c.get("meta") or {}
    if meta.get("cover_img"):
        yield ("표지 그림", meta["cover_img"])
    for ci, ch in enumerate(_as_list(c.get("chapters")), 1):
        if not isinstance(ch, dict):
            continue
        for si, s in enumerate(_as_list(ch.get("sections")), 1):
            if not isinstance(s, dict):
                continue
            for bi, b in enumerate(_as_list(s.get("blocks")), 1):
                if isinstance(b, dict) and b.get("type") == "fig" and b.get("img"):
                    yield ("장%d 절%d 블록%d" % (ci, si, bi), b["img"])


def render_plan(c):
    """build_docx.js 가 붙이는 번호를 그대로 셈 : 장과 절 번호, 그림과 표 번호, 질문 번호, 참고 자료 번호."""
    chapters = [ch for ch in _as_list(c.get("chapters")) if isinstance(ch, dict)]
    plan = {"headings": [], "chapters": len(chapters), "sections": 0, "figures": 0, "tables": 0,
            "questions": len([q for q in _as_list(c.get("qa")) if isinstance(q, dict)]),
            "references": len([r for r in _as_list(c.get("references")) if isinstance(r, dict) and r.get("text")]),
            "devils": isinstance(c.get("devils"), dict)}
    for i, ch in enumerate(chapters, 1):
        plan["headings"].append(str(i))
        for j, s in enumerate([s for s in _as_list(ch.get("sections")) if isinstance(s, dict)], 1):
            plan["headings"].append("%d.%d" % (i, j))
            plan["sections"] += 1
            for b in _as_list(s.get("blocks")):
                if isinstance(b, dict) and b.get("type") == "fig":
                    plan["figures"] += 1
                elif isinstance(b, dict) and b.get("type") == "table":
                    plan["tables"] += 1
    if plan["devils"]:
        plan["headings"].append(str(len(chapters) + 1))
    return plan


META_PREFIX = "Z"  # 메타 claim id 접두어. 원고 담당은 쓰지 않음


def _num_list(n):
    return ", ".join(str(i) for i in range(1, n + 1))


def meta_claims(content, date_text):
    """빌드가 찍는 수를 claim 으로 만듦 (verify_claims 가 미등록 수치로 잡지 않게).
    Z001 작성일과 조사 기준일 / Z002 헤딩 번호 / Z003 그림, 표, 질문 번호 / Z004 참고 자료 번호와 서지 정보 안의 수.
    번호 규칙은 build_docx.js 와 같아야 함 (render_plan)."""
    plan = render_plan(content)
    meta = content.get("meta") or {}
    dates = [date_text]
    base = meta.get("base_date")
    if isinstance(base, str) and base.strip():
        ymd = parse_date(base)
        dates.append(format_date(ymd, "kr") if ymd else base.strip())
    base_note = ", 조사 기준일" if len(dates) > 1 else ""
    out = [{
        "id": "Z001", "text": "작성일%s %s" % (base_note, " / ".join(dates)), "kind": "meta",
        "value": " / ".join(dates), "source": "assemble 메타 claim : 표지 날짜와 META.base_date", "url": "",
        "status": "verified", "method": "build",
        "note": "본문 사실이 아님. 날짜의 월, 일이 미등록 수치로 잡히지 않게 등록함"}, {
        "id": "Z002", "text": "헤딩 번호 (빌드가 붙이는 장, 절 번호)", "kind": "meta",
        "value": ", ".join(plan["headings"]),
        "source": "assemble 메타 claim : build_docx.js 자동 번호", "url": "", "status": "verified",
        "method": "build", "note": "1.1 같은 절 번호는 소수로 읽혀 미등록 수치가 되므로 등록함"}]
    parts = []
    if plan["figures"]:
        parts.append("그림 %s" % _num_list(plan["figures"]))
    if plan["tables"]:
        parts.append("표 %s" % _num_list(plan["tables"]))
    if plan["questions"]:
        parts.append("질문 %s" % _num_list(plan["questions"]))
    if parts:
        out.append({
            "id": "Z003", "text": "그림, 표, 질문 번호 (빌드가 붙이는 캡션과 Q 번호)", "kind": "meta",
            "value": " / ".join(parts), "source": "assemble 메타 claim : build_docx.js 자동 번호",
            "url": "", "status": "verified", "method": "build",
            "note": "12 를 넘는 캡션 번호가 미등록 수치로 잡히지 않게 등록함"})
    if plan["references"]:
        nums = set()
        for _, t in iter_ref_texts(content):
            nums |= {v for v in number_tokens(t) if not YEAR_RE.match(v)}

        def _key(x):
            try:
                return (0, float(x), x)
            except ValueError:
                return (1, 0.0, x)
        value = "번호 %s" % _num_list(plan["references"])
        if nums:
            value += " / 서지 정보 안의 수 %s" % ", ".join(sorted(nums, key=_key))
        out.append({
            "id": "Z004", "text": "참고 자료 %d건 (번호와 서지 정보 안의 수)" % plan["references"], "kind": "meta",
            "value": value, "source": "assemble 메타 claim : 참고 자료 목록", "url": "",
            "status": "verified", "method": "build",
            "note": "발행일, 권호 같은 서지 정보의 수. 본문 사실의 근거가 아님"})
    return out


# ─── 도구용 : 스키마 검사 (content-schema.md 와 같은 규칙) ─────────────────────

BLOCK_REQUIRED = {
    "p": ["text"],
    "fig": ["img", "caption"],
    "table": ["caption", "headers", "rows"],
    "box": ["title", "paras"],
    "quote": ["text"],
    "note": ["text"],
}


def _is_text(v):
    return isinstance(v, str) and v.strip() != ""


def _cell_ok(v):
    return isinstance(v, (str, int, float)) and not isinstance(v, bool)


def validate_block(b, loc, errs, warns):
    if not isinstance(b, dict):
        errs.append("%s: 블록이 dict 가 아님" % loc)
        return
    t = b.get("type")
    if t not in BLOCK_REQUIRED:
        errs.append("%s: 알 수 없는 블록 type %r (p, fig, table, box, quote, note 만 씀)" % (loc, t))
        return
    for k in BLOCK_REQUIRED[t]:
        if k not in b or b[k] in (None, "", []):
            errs.append("%s(%s): %s 없음" % (loc, t, k))
    if t == "fig":
        img = b.get("img")
        if isinstance(img, str) and not img.lower().endswith(".png"):
            errs.append("%s(fig): img 는 PNG 만 씀 (%s)" % (loc, img))
    if t == "table":
        headers, rows, widths = b.get("headers"), b.get("rows"), b.get("widths")
        if not isinstance(headers, list) or not all(_cell_ok(h) for h in headers):
            errs.append("%s(table): headers 는 문자열 목록이어야 함" % loc)
            return
        if not isinstance(rows, list):
            errs.append("%s(table): rows 는 목록이어야 함" % loc)
            return
        for i, r in enumerate(rows):
            if not isinstance(r, list) or not all(_cell_ok(x) for x in r):
                errs.append("%s(table): rows[%d] 는 문자열 목록이어야 함" % (loc, i))
            elif len(r) != len(headers):
                errs.append("%s(table): rows[%d] 칸 수 %d 가 headers %d 와 다름" % (loc, i, len(r), len(headers)))
        if widths is not None:
            if (not isinstance(widths, list) or len(widths) != len(headers)
                    or not all(isinstance(w, int) and not isinstance(w, bool) and w > 0 for w in widths)):
                errs.append("%s(table): widths 는 열 수와 같은 개수의 양의 정수 목록이어야 함 %r" % (loc, widths))
            elif sum(widths) != TABLE_WIDTH:
                errs.append("%s(table): widths 합 %d 가 %d 이 아님 (W() 헬퍼 사용)" % (loc, sum(widths), TABLE_WIDTH))
    if t == "box":
        paras = b.get("paras")
        if not isinstance(paras, list) or not all(isinstance(x, str) for x in paras):
            errs.append("%s(box): paras 는 문자열 목록이어야 함" % loc)


def validate_chapters(chapters, tag, errs, warns):
    if not isinstance(chapters, list):
        errs.append("%s: CHAPTERS 는 목록이어야 함" % tag)
        return
    for ci, ch in enumerate(chapters, 1):
        loc = "%s 장%d" % (tag, ci)
        if not isinstance(ch, dict):
            errs.append("%s: 장이 dict 가 아님" % loc)
            continue
        if not _is_text(ch.get("title")):
            errs.append("%s: title 없음" % loc)
        intro = ch.get("intro", [])
        if not isinstance(intro, list) or not all(isinstance(x, str) for x in intro):
            errs.append("%s: intro 는 문자열 목록이어야 함" % loc)
        secs = ch.get("sections")
        if not isinstance(secs, list):
            errs.append("%s: sections 는 목록이어야 함" % loc)
            continue
        if not secs:
            warns.append("%s: 절이 없음" % loc)
        for si, s in enumerate(secs, 1):
            sl = "%s 절%d" % (loc, si)
            if not isinstance(s, dict):
                errs.append("%s: 절이 dict 가 아님" % sl)
                continue
            if not _is_text(s.get("title")):
                errs.append("%s: title 없음" % sl)
            if not _is_text(s.get("key_message")):
                warns.append("%s: key_message 없음 (KEY MESSAGE 박스가 빠짐)" % sl)
            blocks = s.get("blocks")
            if not isinstance(blocks, list):
                errs.append("%s: blocks 는 목록이어야 함" % sl)
                continue
            for bi, b in enumerate(blocks, 1):
                validate_block(b, "%s 블록%d" % (sl, bi), errs, warns)


def validate_meta(meta, errs, warns):
    if not isinstance(meta, dict):
        errs.append("META: dict 가 아님")
        return
    tl = meta.get("title_lines")
    if isinstance(tl, str):
        tl = [tl]
    if not isinstance(tl, list) or not (1 <= len(tl) <= 2) or not all(_is_text(x) for x in tl):
        errs.append("META.title_lines: 1~2줄 문자열 목록이어야 함")
    if meta.get("lang", "kr") not in ("kr", "en"):
        errs.append("META.lang: kr 또는 en")
    for k in ("date", "base_date"):
        d = meta.get(k)
        if d not in (None, "") and parse_date(d) is None:
            errs.append("META.%s: 날짜를 읽을 수 없음 %r (「2026년 10월 12일」 또는 2026-10-12)" % (k, d))
    ci = meta.get("cover_img")
    if ci not in (None, "") and (not isinstance(ci, str) or not ci.lower().endswith(".png")):
        errs.append("META.cover_img: PNG 경로여야 함")


def validate_es(es, errs, warns):
    if not isinstance(es, dict):
        errs.append("ES: dict 가 아님")
        return
    for k in ("key_message", "background"):
        if not _is_text(es.get(k)):
            errs.append("ES.%s 없음" % k)
    flow = es.get("flow")
    if (not isinstance(flow, list) or not flow
            or not all(isinstance(x, (list, tuple)) and len(x) == 2 and _is_text(x[0]) and _is_text(x[1]) for x in flow)):
        errs.append("ES.flow: [[라벨, 문장], ...] 목록이어야 함")
    elif len(flow) != 4:
        warns.append("ES.flow: %d개 (4개 권장)" % len(flow))
    if not (_is_text(es.get("next")) or _is_text(es.get("outlook"))):
        errs.append("ES.next(또는 outlook) 없음")


def validate_qa(qa, errs, warns):
    if not isinstance(qa, list):
        errs.append("QA: 목록이어야 함")
        return
    if not qa:
        warns.append("QA 비어 있음 (핵심 질문과 답변 쪽이 빠짐)")
    for i, x in enumerate(qa, 1):
        if not isinstance(x, dict) or not _is_text(x.get("q")) or not _is_text(x.get("a")):
            errs.append("QA[%d]: {q, a} 둘 다 있어야 함" % i)


def validate_devils(dv, errs, warns):
    if dv is None:
        return
    if not isinstance(dv, dict) or not _is_text(dv.get("title")):
        errs.append("DEVILS: {title, items} 형식이어야 함")
        return
    items = dv.get("items")
    if not isinstance(items, list) or not items:
        errs.append("DEVILS.items: 목록이어야 함")
        return
    for i, x in enumerate(items, 1):
        if not isinstance(x, dict) or not _is_text(x.get("claim")) or not _is_text(x.get("counter")):
            errs.append("DEVILS.items[%d]: {claim, counter} 둘 다 있어야 함" % i)


def validate_closing(cl, errs, warns):
    if not isinstance(cl, dict):
        errs.append("CLOSING: dict 가 아님")
        return
    if not _is_text(cl.get("key_sentence")):
        errs.append("CLOSING.key_sentence 없음")
    paras = cl.get("paras", [])
    if not isinstance(paras, list) or not all(isinstance(x, str) for x in paras):
        errs.append("CLOSING.paras: 문자열 목록이어야 함")
    kw = cl.get("keywords", [])
    if not isinstance(kw, list) or not all(isinstance(x, str) for x in kw):
        errs.append("CLOSING.keywords: 문자열 목록이어야 함")
    elif not kw:
        warns.append("CLOSING.keywords 비어 있음")
    pv = cl.get("perspectives")
    if pv is not None and (not isinstance(pv, list) or not all(
            isinstance(x, (list, tuple)) and len(x) == 2 and _is_text(x[0]) and _is_text(x[1]) for x in pv)):
        errs.append("CLOSING.perspectives: [[관점, 문장], ...] 목록이어야 함")


def validate_references(refs, errs, warns):
    if not isinstance(refs, list):
        errs.append("REFERENCES: 목록이어야 함")
        return
    for i, r in enumerate(refs, 1):
        if not isinstance(r, dict) or not _is_text(r.get("text")):
            errs.append("REFERENCES[%d]: {text, url} 형식이어야 함" % i)
        elif r.get("url") not in (None, "") and not str(r.get("url")).startswith(("http://", "https://")):
            warns.append("REFERENCES[%d]: url 이 http 로 시작하지 않음" % i)


def validate_document(c, partial=False):
    """content 전체 검사. (errors, warnings). partial=True 면 없는 부분(META, ES 등)은 건너뜀(모듈 단위 점검용)."""
    errs, warns = [], []
    if not isinstance(c, dict):
        return ["content 가 dict 가 아님"], []
    if not partial or c.get("meta") is not None:
        validate_meta(c.get("meta"), errs, warns)
    if not partial or c.get("es") is not None:
        validate_es(c.get("es"), errs, warns)
    if not partial or c.get("qa") is not None:
        validate_qa(c.get("qa", []), errs, warns)
    chs = c.get("chapters")
    if partial:
        if chs is not None:
            validate_chapters(chs, "chapters", errs, warns)
    elif not isinstance(chs, list) or not chs:
        errs.append("chapters: 장이 하나 이상 있어야 함")
    else:
        validate_chapters(chs, "chapters", errs, warns)
    validate_devils(c.get("devils"), errs, warns)
    if not partial or c.get("closing") is not None:
        validate_closing(c.get("closing"), errs, warns)
    if c.get("references") is not None:
        validate_references(c.get("references"), errs, warns)
    return errs, warns
