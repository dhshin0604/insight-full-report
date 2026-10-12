# -*- coding: utf-8 -*-
"""deck_core.py : 5-Zone 이미지 슬라이드 렌더러 (insight-full-report / image-deck 스킬)

HTML/CSS 로 1920x1080 쪽을 만들고 Playwright(chromium)로 PNG 를 찍음.

- 쪽 함수 : slide_html, cover_html, agenda_html, sublist_html, visual_summary_html,
  implication_html, thanks_html, plain_html  ->  HTML 문서 문자열
- 컴포넌트 함수 : stats, cards, mini_table, flow, chip, callout, note, chart_img,
  hbars, timeline, quadrant, layers  ->  본문(.body)에 넣을 HTML 조각
- 배치 함수 : two_panel, fill, panel_title (컴포넌트 종류 셈에 들어가지 않음)
- render_all(htmls, out_dir) : PNG 렌더 + 쪽 단위·덱 단위 자동 QA + qa_report.json
- check_palette(theme) : WCAG 대비, 의미색 구분(CIE76 dE), 적록색약 모사 검사

문자열 인자는 HTML 로 해석됨(<b>, <br> 사용 가능). 「<」「&」를 글자 그대로 쓰려면 esc() 로 감쌈.
종료코드 : 1 = strict 모드 QA 오류, 2 = 프로필 값 없음, 3 = 의존성(Playwright·chromium) 없음.

사용 예 (spec.py)
    import os, sys
    sys.path.insert(0, "<image-deck/references 폴더>")
    from deck_core import *
    pages = [cover_html("제목", "부제", date="2026.10.12"),
             slide_html(2, "1. 현황", "① 규모", "헤드라인 두 문장",
                        stats([("320명", "현장 인력", "4개 권역 합계")]) + callout("정리 한 줄"),
                        source="가상의 A사 내부 자료(예시)")]
    paths = render_all(pages, "out")          # PNG 경로 목록(list). .report 에 QA 결과
"""
import datetime
import html as _html
import json
import math
import os
import re
import sys
import unicodedata
from pathlib import Path
from string import Template

__version__ = "1.0.0"
HERE = os.path.dirname(os.path.abspath(__file__))
SLIDE_W, SLIDE_H = 1920, 1080
MIN_FONT_PX = 19

__all__ = [
    "THEME", "make_theme", "use_theme", "current_theme", "check_palette",
    "load_profile", "set_profile", "profile_candidates",
    "esc", "strip_tags", "josa_ro",
    "slide_html", "plain_html", "cover_html", "agenda_html", "sublist_html", "thanks_html",
    "visual_summary_html", "implication_html",
    "stats", "cards", "mini_table", "two_panel", "fill", "panel_title", "flow", "chip", "callout", "note",
    "chart_img", "hbars", "timeline", "quadrant", "layers",
    "render_all", "RenderResult", "contrast_ratio",
]

# ---------------------------------------------------------------------------
# 1. 테마 (색·글꼴 토큰)
# ---------------------------------------------------------------------------
THEME = {
    # 의미색 : 덱 전체에서 뜻을 바꾸지 않음
    "accent": "#D42020",    # 섹션 라벨, 위·아래 구분선
    "inside": "#A31D1D",    # 관내 / 강조 (진빨강)
    "outside": "#1A3A6B",   # 관외 / 기준 (네이비)
    "unknown": "#8A8A8A",   # 미확인 (회색)
    "text": "#1A1A1A",      # 본문
    "aux": "#843C0C",       # 보조 강조 (적갈색), 시사점 불릿
    "key": "#C00000",       # 시사점·도해 빨강 (To-Be, 핵심 변화)
    "asis": "#767676",      # As-Is, 기존 요소 (회색, 흰 글자를 얹어도 4.5:1)
    "asis_ink": "#404040",  # As-Is 상자 안 글자
    # 중립색 : 출처·크레딧 회색은 흰 바탕 대비 4.5 이상이 되게 잡음
    "bg": "#FFFFFF",
    "muted": "#6B6B6B",     # 소제목
    "source": "#6B6B6B",    # 출처 줄
    "credit": "#707070",    # 크레딧 줄
    "note": "#555555",      # note() 보조 글
    "line": "#3A3A3A",      # 표 머리, 진한 선
    "grid": "#CFCFCF",      # 표 칸 선, 연한 테두리
    "panel": "#F3F3F3",     # 카드 바탕
    "pg_bg": "#4D4D4D",     # 쪽 번호 삼각형
    "on_dark": "#FFFFFF",   # 진한 바탕 위 글자
    "chip_unknown_bg": "#F2F2F2",
    "chip_unknown_fg": "#4D4D4D",
    "dim": "#B5B5B5",        # 간지에서 일부러 흐리게 한 비활성 행 글자(대비 검사 제외)
    "soft": "#F5F5F5",       # 비활성 행 라벨 바탕, 아주 옅은 면
    "hairline": "#DDDDDD",   # 세부 목차 구분선, 표지 장식 막대
    "quad_name": "#8A8A8A",  # 사분면 이름
    "label_bg": "#D9D9D9",   # 시사점 왼쪽 라벨 상자
    "cell_line": "#C5A9A9",  # 시사점 칸 테두리
    "sublabel": "#595959",   # 시사점·도해 오른쪽 라벨
    "brand_bg": "#5A5A5A",   # 표지 상단 라벨 바탕
    "brand_fg": "#4FD1C5",   # 표지 상단 라벨 글자
    # 글꼴 스택
    "font": "'Noto Sans CJK KR','Noto Sans KR','NanumGothic','Malgun Gothic','Apple SD Gothic Neo',sans-serif",
}
_THEME = dict(THEME)
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# 컴포넌트 color_key 별칭
_ALIASES = {
    "red": "inside", "inside": "inside", "관내": "inside",
    "navy": "outside", "outside": "outside", "관외": "outside",
    "grey": "unknown", "gray": "unknown", "unknown": "unknown", "미확인": "unknown",
    "key": "key", "aux": "aux", "asis": "asis", "accent": "accent", "text": "text",
}


def make_theme(overrides=None, activate=True):
    """기본 THEME 에 overrides 를 덮어쓴 새 테마를 만듦. activate=True 면 바로 적용함.

    예 : make_theme({"inside": "#9C1C1C", "font": "'Pretendard',sans-serif"})
    """
    t = dict(THEME)
    for k, v in (overrides or {}).items():
        if k not in THEME:
            raise KeyError("make_theme: 알 수 없는 토큰 %r (허용 : %s)" % (k, ", ".join(sorted(THEME))))
        if k != "font" and not _HEX_RE.match(str(v)):
            raise ValueError("make_theme: %s 값 %r 은 #RRGGBB 형식이어야 함" % (k, v))
        t[k] = v
    if activate:
        use_theme(t)
    return t


def use_theme(theme):
    """테마 딕셔너리를 현재 테마로 씀(이후 만드는 쪽부터 적용)."""
    global _THEME
    missing = [k for k in THEME if k not in theme]
    if missing:
        raise KeyError("use_theme: 빠진 토큰 %s" % ", ".join(missing))
    _THEME = dict(theme)


def current_theme():
    return dict(_THEME)


def _color(key, theme=None):
    t = theme or _THEME
    if key is None:
        key = "inside"
    k = str(key)
    if k.startswith("#"):
        if not _HEX_RE.match(k):
            raise ValueError("색 %r 은 #RRGGBB 형식이어야 함" % k)
        return k
    if k in _ALIASES:
        return t[_ALIASES[k]]
    if k in t and k != "font":
        return t[k]
    raise ValueError("알 수 없는 color_key %r (inside/red, outside/navy, unknown/grey, key, aux, asis 또는 #RRGGBB)" % key)


# ---------------------------------------------------------------------------
# 2. 색 계산 : WCAG 대비, CIE76 dE, 적록색약 모사
# ---------------------------------------------------------------------------
def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _mix(c1, c2, t):
    """c1 을 t 만큼, c2 를 (1-t) 만큼 섞음."""
    a, b = _rgb(c1), _rgb(c2)
    return _hex([a[i] * t + b[i] * (1 - t) for i in range(3)])


def _lin(c8):
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_luminance(h):
    """WCAG 2.x 상대 휘도."""
    r, g, b = [_lin(c) for c in _rgb(h)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    """WCAG 2.x 대비비 (1~21)."""
    la, lb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _lab_from_linear(r, g, b):
    # sRGB(D65) 선형 값 -> XYZ (IEC 61966-2-1 행렬) -> CIE 1976 L*a*b* (D65 기준 백색)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(v):
        d = 6.0 / 29.0
        return v ** (1.0 / 3.0) if v > d ** 3 else v / (3 * d * d) + 4.0 / 29.0

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def to_lab(h):
    return _lab_from_linear(*[_lin(c) for c in _rgb(h)])


# 적록색약(deuteranopia) 모사 행렬
# 출처 : G. M. Machado, M. M. Oliveira, L. A. F. Fernandes (2009),
#   "A Physiologically-based Model for Simulation of Color Vision Deficiency",
#   IEEE Transactions on Visualization and Computer Graphics 15(6), 1291-1298.
#   저자 공개 페이지의 Deuteranomaly severity 1.0 행렬
#   (https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html).
#   선형 RGB 에 곱함(감마 보정 값이 아님).
_DEUTERANOPIA = (
    (0.367322, 0.860646, -0.227968),
    (0.280085, 0.672501, 0.047413),
    (-0.011820, 0.042940, 0.968881),
)


def simulate_deuteranopia_lab(h):
    v = [_lin(c) for c in _rgb(h)]
    o = [min(1.0, max(0.0, sum(_DEUTERANOPIA[i][j] * v[j] for j in range(3)))) for i in range(3)]
    return _lab_from_linear(*o)


def delta_e76(lab1, lab2):
    return math.sqrt(sum((lab1[i] - lab2[i]) ** 2 for i in range(3)))


def _derived(t):
    """테마 토큰에서 옅은 바탕색 등 파생 색을 만듦(CSS 와 팔레트 검사가 같은 값을 씀)."""
    d = dict(t)
    d["inside_bg"] = _mix(t["inside"], t["bg"], 0.07)
    d["outside_bg"] = _mix(t["outside"], t["bg"], 0.07)
    d["tobe_bg"] = _mix(t["key"], t["bg"], 0.05)
    d["asis_bg"] = _mix(t["asis"], t["bg"], 0.07)
    d["asis_line"] = _mix(t["asis"], t["bg"], 0.55)
    d["aux_bg"] = _mix(t["aux"], t["bg"], 0.06)
    d["quad_bg"] = t["bg"]
    d["quad_hot"] = _mix(t["key"], t["bg"], 0.06)
    return d


# 글자색·바탕색 쌍 : (이름, 글자 토큰, 바탕 토큰, px, 굵게). CSS 에서 실제로 쓰는 조합(가장 작은 크기 기준)
_TEXT_PAIRS = [
    ("섹션 라벨", "accent", "bg", 40, True),
    ("소제목", "muted", "bg", 32, False),
    ("헤드라인", "text", "bg", 36, True),
    ("본문", "text", "bg", 21, False),
    ("출처 줄", "source", "bg", 19, False),
    ("크레딧", "credit", "bg", 18, False),
    ("쪽 번호", "on_dark", "pg_bg", 20, True),
    ("표 머리", "on_dark", "line", 21, True),
    ("표 강조 행", "text", "inside_bg", 21, False),
    ("보조 글(note)", "note", "bg", 19, False),
    ("수치 타일 : 관내", "inside", "bg", 52, True),
    ("수치 타일 : 관외", "outside", "bg", 52, True),
    ("수치 타일 : 미확인", "unknown", "bg", 52, True),
    ("칩 : 관내", "on_dark", "inside", 19, True),
    ("칩 : 관외", "on_dark", "outside", 19, True),
    ("칩 : 미확인", "chip_unknown_fg", "chip_unknown_bg", 19, True),
    ("칩 : 핵심", "on_dark", "key", 19, True),
    ("칩 : 보조", "on_dark", "aux", 19, True),
    ("카드 제목 : 관내", "inside", "panel", 24, True),
    ("카드 제목 : 관외", "outside", "panel", 24, True),
    ("카드 제목 : 미확인", "unknown", "panel", 24, True),
    ("카드 제목 : 핵심", "key", "panel", 24, True),
    ("카드 본문", "text", "panel", 21, False),
    ("단계 상자 강조", "inside", "inside_bg", 23, True),
    ("막대 값", "text", "bg", 21, True),
    ("타임라인 날짜", "inside", "bg", 22, True),
    ("타임라인 강조 카드 날짜", "key", "tobe_bg", 22, True),
    ("사분면 축 끝", "note", "bg", 20, False),
    ("사분면 이름", "quad_name", "quad_bg", 26, True),
    ("사분면 강조 칸 이름", "quad_name", "quad_hot", 26, True),
    ("계층 라벨 : 관외", "on_dark", "outside", 24, True),
    ("계층 라벨 : 관내", "on_dark", "inside", 24, True),
    ("계층 강조 요소", "key", "bg", 22, True),
    ("간지 현재 행", "on_dark", "accent", 26, True),
    ("간지 강조 행 라벨", "text", "label_bg", 26, True),
    ("세부 목차 번호", "on_dark", "line", 22, True),
    ("시사점 제목", "key", "bg", 40, True),
    ("시사점 오른쪽 라벨", "sublabel", "bg", 32, False),
    ("시사점 왼쪽 라벨", "text", "label_bg", 27, True),
    ("시사점 불릿 2단", "aux", "bg", 21, False),
    ("도해 제목", "key", "bg", 52, True),
    ("As-Is 머리 꼬리표", "on_dark", "asis", 24, True),
    ("To-Be 머리 꼬리표", "on_dark", "key", 24, True),
    ("As-Is 상자", "asis_ink", "bg", 23, True),
    ("As-Is 상자 보조 글", "asis_ink", "bg", 19, False),
    ("As-Is 도해 설명", "asis_ink", "asis_bg", 20, False),
    ("To-Be 상자", "text", "bg", 23, True),
    ("To-Be 도해 설명", "text", "tobe_bg", 20, False),
    ("To-Be 핵심 상자 보조 글", "on_dark", "key", 19, False),
    ("보조 강조 상자 보조 글", "aux", "bg", 19, False),
    ("판정 : As-Is", "asis", "bg", 50, True),
    ("판정 : To-Be", "key", "bg", 50, True),
    ("도해 설명", "text", "bg", 24, False),
    ("결론 띠", "on_dark", "key", 26, True),
    ("표지 라벨", "brand_fg", "brand_bg", 30, True),
    ("표지 시리즈", "accent", "bg", 30, True),
    ("표지 부제·날짜", "muted", "bg", 22, False),
]

# 의미색 묶음 : 묶음 안의 색끼리 구분되어야 함
_SEMANTIC_GROUPS = [
    ("관내·관외·미확인", [("관내", "inside"), ("관외", "outside"), ("미확인", "unknown")]),
    ("As-Is·To-Be·보조 강조", [("As-Is", "asis"), ("To-Be", "key"), ("보조 강조", "aux")]),
]


def check_palette(theme=None, verbose=True):
    """팔레트 검사. 반환 : {"contrast": [...], "distinct": [...], "fail": n, "warn": n}

    - 대비 : 24px 미만 글자는 4.5 이상, 24px 이상 굵은 글자는 3.0 이상 (모자라면 FAIL)
      (WCAG 2.x 의 큰 글자 정의보다 보수적으로 24px 이상 굵게만 큰 글자로 봄)
    - 의미색 구분 : 묶음 안 쌍마다 CIE76 dE 20 미만이면 WARN, 적록색약 모사 후 dE 10 미만이면 WARN
    """
    d = _derived(theme or _THEME)
    contrast, distinct = [], []
    for name, fg, bg, px, bold in _TEXT_PAIRS:
        ratio = contrast_ratio(d[fg], d[bg])
        need = 3.0 if (px >= 24 and bold) else 4.5
        contrast.append({"name": name, "fg": d[fg], "bg": d[bg], "px": px, "bold": bold,
                         "ratio": round(ratio, 2), "need": need, "ok": ratio + 1e-9 >= need})
    for gname, members in _SEMANTIC_GROUPS:
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                (na, ka), (nb, kb) = members[i], members[j]
                de = delta_e76(to_lab(d[ka]), to_lab(d[kb]))
                dd = delta_e76(simulate_deuteranopia_lab(d[ka]), simulate_deuteranopia_lab(d[kb]))
                distinct.append({"group": gname, "pair": "%s/%s" % (na, nb), "a": d[ka], "b": d[kb],
                                 "dE": round(de, 1), "dE_deuteranopia": round(dd, 1),
                                 "ok": de >= 20 and dd >= 10})
    fail = sum(1 for c in contrast if not c["ok"])
    warn = sum(1 for c in distinct if not c["ok"])
    res = {"contrast": contrast, "distinct": distinct, "fail": fail, "warn": warn}
    if verbose:
        print("[팔레트 검사] 대비 %d쌍 중 FAIL %d · 의미색 %d쌍 중 WARN %d"
              % (len(contrast), fail, len(distinct), warn))
        for c in contrast:
            if not c["ok"]:
                print("  FAIL 대비 %-14s %s / %s  %.2f < %.1f (%dpx%s)"
                      % (c["name"], c["fg"], c["bg"], c["ratio"], c["need"], c["px"], " 굵게" if c["bold"] else ""))
        low = min(contrast, key=lambda c: c["ratio"] - c["need"])
        print("  대비 여유 최소 쌍 : %s %.2f (기준 %.1f)" % (low["name"], low["ratio"], low["need"]))
        for c in distinct:
            print("  %s 의미색 %-16s dE %5.1f · 적록색약 모사 dE %5.1f"
                  % ("OK  " if c["ok"] else "WARN", c["pair"], c["dE"], c["dE_deuteranopia"]))
    return res


# ---------------------------------------------------------------------------
# 3. 프로필 (작성자 정보)
# ---------------------------------------------------------------------------
PROFILE_KEYS = ["AUTHOR_KR", "AUTHOR_EN", "PHONE_KR", "PHONE_EN", "EMAIL", "BRAND",
                "WORKSPACE_ROOT", "WORKSPACE_DIRNAME"]
DECK_REQUIRED = ("AUTHOR_KR", "AUTHOR_EN", "EMAIL")
DEFAULT_BRAND = "Insight Report"
_PROFILE = None
_PLACEHOLDER_RE = re.compile(r"\{(%s)\}" % "|".join(PROFILE_KEYS))


def profile_candidates():
    """찾는 순서 : 환경변수 PROFILE -> ./profile.json -> 이 스킬 references/profile.json
    -> 형제 스킬 ../generate-full-report/references/profile.json"""
    c = []
    env = os.environ.get("PROFILE")
    if env:
        c.append(("환경변수 PROFILE", env))
    c.append(("작업 폴더 ./profile.json", os.path.join(os.getcwd(), "profile.json")))
    c.append(("image-deck references/profile.json", os.path.join(HERE, "profile.json")))
    c.append(("형제 스킬 generate-full-report", os.path.normpath(
        os.path.join(HERE, "..", "..", "generate-full-report", "references", "profile.json"))))
    return c


def _read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:   # BOM(메모장, PowerShell 5) 허용
            return json.load(f)
    except (OSError, ValueError):
        return None


def _finish_profile(prof, path):
    p = dict(prof)
    p["BRAND"] = p.get("BRAND") or DEFAULT_BRAND
    p["CREDIT"] = "Researched, Written, and Created by %s (%s)" % (p["AUTHOR_EN"], p["EMAIL"])
    p["BRAND_LABEL"] = "[ %s ]" % p["BRAND"]
    p["_path"] = path
    return p


def load_profile(required=DECK_REQUIRED, exit_on_missing=True, quiet=False):
    """작성자 프로필을 읽어 캐시함.

    - 후보 파일을 순서대로 보고 required 키가 모두 찬 첫 파일을 씀
    - 환경변수 PROFILE_<KEY>(예 : PROFILE_AUTHOR_KR)가 있으면 파일 값보다 우선함
    - 모두 비어 있으면 무엇이 비었는지와 해결법을 출력하고 종료코드 2 로 멈춤
      (exit_on_missing=False 면 ValueError)
    반환 딕셔너리 : PROFILE_KEYS + CREDIT(크레딧 줄) + BRAND_LABEL(표지 라벨) + _path
    """
    global _PROFILE
    seen, chosen = [], None
    env_file = os.environ.get("PROFILE")
    if env_file and not os.path.isfile(env_file):
        msg = ("[image-deck] 환경변수 PROFILE 이 가리키는 파일이 없음 : %s\n"
               "  해결 : 경로를 고치거나 PROFILE 을 지우고 작업 폴더에 profile.json 을 둠" % os.path.abspath(env_file))
        if exit_on_missing:
            sys.stderr.write(msg + "\n")
            raise SystemExit(2)
        raise ValueError(msg)
    env_over = {k: os.environ.get("PROFILE_" + k, "").strip() for k in PROFILE_KEYS}
    for label, path in profile_candidates():
        if not os.path.isfile(path):
            seen.append((label, path, "없음", None))
            continue
        data = _read_json(path)
        if data is None:
            seen.append((label, path, "JSON 읽기 실패", None))
            continue
        prof = {k: str(data.get(k, "") or "").strip() for k in PROFILE_KEYS}
        for k, v in env_over.items():
            if v:
                prof[k] = v
        missing = [k for k in required if not prof.get(k)]
        seen.append((label, path, "있음", missing))
        if not missing:
            chosen = (path, prof)
            break
    if chosen is None and all(env_over.get(k) for k in required):
        chosen = ("(환경변수 PROFILE_*)", {k: env_over.get(k, "") for k in PROFILE_KEYS})
    if chosen is None:
        lines = ["[image-deck] 작성자 프로필에 덱에 필요한 값이 비어 있음 : %s" % ", ".join(required),
                 "  확인한 파일(찾는 순서) :"]
        for i, (label, path, state, missing) in enumerate(seen, 1):
            extra = ""
            if missing:
                extra = " · 빈 값 " + ", ".join(missing)
            lines.append("    %d) %s : %s%s" % (i, label, state, extra))
        if not os.environ.get("PROFILE"):
            lines.append("    (환경변수 PROFILE 은 설정되지 않음)")
        lines += ["  해결 : (a) 작업 폴더에 profile.json 을 만들어 AUTHOR_KR, AUTHOR_EN, EMAIL 을 채움",
                  "             (형식은 image-deck/references/profile.json 의 _examples 참고)",
                  "         (b) PROFILE=/경로/profile.json 환경변수로 파일을 지정",
                  "         (c) PROFILE_AUTHOR_KR=... 처럼 값을 환경변수로 직접 넘김"]
        msg = "\n".join(lines)
        if exit_on_missing:
            sys.stderr.write(msg + "\n")
            raise SystemExit(2)
        raise ValueError(msg)
    _PROFILE = _finish_profile(chosen[1], chosen[0])
    env_path = os.environ.get("PROFILE")
    if env_path and os.path.abspath(env_path) != os.path.abspath(chosen[0]):
        sys.stderr.write("[image-deck] 주의 : 환경변수 PROFILE(%s)에 빈 값이 있어 다음 후보를 씀\n" % env_path)
    if not quiet:
        print("[image-deck] 프로필 : %s" % _PROFILE["_path"])
    return dict(_PROFILE)


def set_profile(values):
    """프로필을 직접 넣음(다른 스킬·시험에서 씀). AUTHOR_KR, AUTHOR_EN, EMAIL 필수."""
    global _PROFILE
    prof = {k: str(values.get(k, "") or "").strip() for k in PROFILE_KEYS}
    missing = [k for k in DECK_REQUIRED if not prof[k]]
    if missing:
        raise ValueError("set_profile: 빈 값 %s" % ", ".join(missing))
    _PROFILE = _finish_profile(prof, "(set_profile)")
    return dict(_PROFILE)


def _prof():
    return _PROFILE if _PROFILE is not None else load_profile()


# ---------------------------------------------------------------------------
# 4. 글자 도우미
# ---------------------------------------------------------------------------
def esc(s):
    """글자 그대로 보이게 HTML 이스케이프."""
    return _html.escape(str(s), quote=False)


def _attr(s):
    return _html.escape(str(s), quote=True)


def strip_tags(s):
    return _html.unescape(re.sub(r"<[^>]+>", "", str(s)))


_DIGIT_RO = {"0": "으로", "1": "로", "2": "로", "3": "으로", "4": "로",
             "5": "로", "6": "으로", "7": "로", "8": "로", "9": "로"}


def josa_ro(word):
    """「로/으로」 고르기 : 받침이 없거나 ㄹ 받침이면 로, 그 밖의 받침은 으로."""
    s = strip_tags(word).strip()
    if not s:
        return "로"
    ch = s[-1]
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3:
        jong = (code - 0xAC00) % 28
        return "로" if jong in (0, 8) else "으로"
    if ch in _DIGIT_RO:
        return _DIGIT_RO[ch]
    if ch in "MN":
        return "으로"
    return "로"


def _est_width(text, px):
    """대략적인 글자 폭(px). 한글·전각 1em, 숫자·영문 0.6em, 기타 0.35em."""
    w = 0.0
    for ch in strip_tags(text):
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            w += px
        elif ch.isalnum():
            w += px * 0.6
        else:
            w += px * 0.35
    return w


def _fmt_num(v):
    if isinstance(v, int) or (isinstance(v, float) and v.is_integer()):
        return "{:,}".format(int(v))
    return ("{:,.2f}".format(v)).rstrip("0").rstrip(".")


def _file_uri(path):
    p = str(path)
    if re.match(r"^(https?:|data:|file:)", p):
        return p
    return Path(p).expanduser().resolve().as_uri()


# ---------------------------------------------------------------------------
# 5. CSS
# ---------------------------------------------------------------------------
_CSS = Template(r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;background:$bg}
body{font-family:$font;color:$text;word-break:keep-all;overflow-wrap:break-word;-webkit-font-smoothing:antialiased;font-feature-settings:"halt" 1}
.slide{position:relative;width:1920px;height:1080px;overflow:hidden;background:$bg}
b,strong{font-weight:700}
/* 5-Zone */
.sec{position:absolute;left:80px;right:80px;top:46px;height:60px;display:flex;justify-content:space-between;align-items:flex-end;gap:40px;white-space:nowrap;overflow:hidden}
.sec-title{font-size:40px;font-weight:700;color:$accent;line-height:1.2}
.sec-sub{font-size:32px;color:$muted;line-height:1.2}
.rule{position:absolute;left:80px;right:80px;top:114px;height:3px;background:$accent}
.headline{position:absolute;left:80px;right:80px;top:136px;font-size:36px;font-weight:600;line-height:1.32;color:$text;letter-spacing:-0.6px}
.body{position:absolute;left:80px;top:255px;width:1760px;height:705px;overflow:hidden;font-size:21px;line-height:1.45;color:$text;display:flex;flex-direction:column;gap:18px}
.body>*{flex:0 0 auto}
.fill{display:flex;flex-direction:column;gap:18px}
.body>.fill{flex:1 0 auto}
.tp>.col.colfill{display:flex;flex-direction:column}
.tp>.col>.fill{flex:1 0 auto}
.fill>.grp{flex:0 0 auto}
.grp>div+div,.grp>table+div,.grp>div+table{margin-top:14px}
.source{position:absolute;left:80px;right:80px;bottom:84px;font-size:19px;line-height:1.2;color:$source}
.frule{position:absolute;left:80px;right:80px;top:1008px;height:2px;background:$accent}
.credit{position:absolute;left:0;right:0;top:1024px;text-align:center;font-size:18px;line-height:1.3;color:$credit}
.pgtri{position:absolute;right:0;bottom:0;width:0;height:0;border-left:78px solid transparent;border-bottom:78px solid $pg_bg}
.pgnum{position:absolute;right:10px;bottom:9px;color:$on_dark;font-size:20px;font-weight:700;line-height:1}
/* 배치 */
.tp{display:grid}
.tp>.col{min-width:0}
.tp>.col>div+div,.tp>.col>table+div,.tp>.col>div+table{margin-top:16px}
.ptitle{font-size:24px;font-weight:700;line-height:1.3;padding-bottom:8px;border-bottom:2px solid $line;margin-bottom:14px}
/* stats */
.stats{display:grid;gap:18px}
.stat{border:2px solid $grid;border-top:8px solid var(--c);border-radius:8px;padding:14px 22px 16px;background:$bg}
.stat .v{font-size:52px;font-weight:800;color:var(--c);line-height:1.1;letter-spacing:-1px}
.stat .l{font-size:23px;font-weight:700;margin-top:6px;line-height:1.3}
.stat .s{font-size:19px;color:$note;margin-top:4px;line-height:1.35}
/* cards */
.cards{display:grid;gap:16px}
.card{border:2px solid $grid;border-left:8px solid var(--c);border-radius:8px;background:$panel;padding:14px 22px 16px}
.card .t{font-size:24px;font-weight:700;color:var(--c);line-height:1.3;margin-bottom:6px}
.card ul{list-style:none}
.card li{position:relative;padding-left:22px;margin-top:5px;line-height:1.42}
.card li::before{content:"";position:absolute;left:3px;top:.6em;width:9px;height:9px;background:var(--c)}
.card .cb{line-height:1.42}
.card .cb>div+div{margin-top:8px}
/* table */
table.mt{width:100%;border-collapse:collapse;font-size:21px;line-height:1.38}
table.mt th{background:$line;color:$on_dark;font-weight:700;text-align:left;padding:10px 14px;border:1px solid $line}
table.mt td{border:1px solid $grid;padding:9px 14px;vertical-align:middle}
table.mt tr.em td{background:$inside_bg}
table.mt .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
table.mt.tall td{height:var(--rh)}
/* flow */
.flow{display:flex;align-items:stretch}
.flow .step{flex:1;min-width:0;border:2px solid $line;border-radius:8px;padding:14px 18px;background:$bg}
.flow .step .t{font-weight:700;font-size:23px;line-height:1.3}
.flow .step .d{font-size:20px;margin-top:6px;line-height:1.4}
.flow .step.on{border-color:var(--c);background:$inside_bg;box-shadow:inset 0 6px 0 var(--c)}
.flow .step.on .t{color:var(--c)}
.flow .arr{flex:0 0 46px;display:flex;align-items:center;justify-content:center}
.flow .arr svg{width:20px;height:34px}
.flow .arr path{fill:none;stroke:$line;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
/* chip, callout, note */
.chip{display:inline-block;border-radius:16px;padding:1px 13px;font-size:19px;font-weight:700;line-height:1.5;margin:2px 6px 2px 0;vertical-align:middle;white-space:nowrap}
.chip.unknown{background:$chip_unknown_bg;color:$chip_unknown_fg;border:2px dashed $unknown;padding:0 11px}
.chip.hollow{background:$bg;color:$text;border:2px solid $text;padding:0 11px}
.callout{font-size:23px;font-weight:600;line-height:1.42;color:$text;padding-left:40px;position:relative}
.callout .mk{position:absolute;left:0;top:0;color:$key}
.note{font-size:19px;color:$note;line-height:1.4}
.fig{display:flex;align-items:center;justify-content:center}
.fig img{max-width:100%;max-height:100%;object-fit:contain}
.figcap{font-size:19px;color:$note;text-align:center;margin-top:6px}
/* hbars */
.hbars{display:grid;grid-template-columns:var(--lw) 1fr;column-gap:16px;align-items:center}
.hbars .hl{font-size:21px;font-weight:600;text-align:right;line-height:1.25}
.hbars .ht{display:flex;align-items:center;gap:12px;height:var(--bh);border-left:2px solid $line}
.hbars .hb{flex:0 1 auto;height:100%;border-radius:0 5px 5px 0;min-width:4px}
.hbars .hv{flex:0 0 auto;font-size:21px;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
.hbars .hcap{grid-column:1/-1;font-size:20px;font-weight:700;margin-bottom:4px}
/* timeline */
.tline{display:grid;grid-template-rows:auto auto auto}
.tline .tl-date{grid-row:1;align-self:end;text-align:center;font-size:22px;font-weight:800;line-height:1.2;padding-bottom:4px;white-space:nowrap}
.tline .tl-rail{grid-row:2;grid-column:1/-1;position:relative;height:56px}
.tline .tl-rail::before{content:"";position:absolute;left:0;right:14px;top:26px;height:4px;background:$line;border-radius:2px}
.tline .tl-rail::after{content:"";position:absolute;right:0;top:18px;border-left:18px solid $line;border-top:10px solid transparent;border-bottom:10px solid transparent}
.tline .tl-dot{position:absolute;top:28px;width:24px;height:24px;margin-left:-12px;margin-top:-12px;border-radius:50%;background:var(--c);border:4px solid $bg;box-shadow:0 0 0 2px var(--c)}
.tline .tl-dot.em{width:32px;height:32px;margin-left:-16px;margin-top:-16px}
.tline .tl-stem{position:absolute;width:2px;margin-left:-1px;height:14px;background:var(--c)}
.tline .tl-stem.up{top:0}.tline .tl-stem.dn{top:42px}
.tline .tl-card{margin:0 6px;min-width:0;border:2px solid $grid;border-top:5px solid var(--c);border-radius:8px;background:$bg;padding:10px 16px 12px}
.tline .tl-card.up{grid-row:1;align-self:end}.tline .tl-card.dn{grid-row:3;align-self:stretch}
.tline .tl-card.em{border-color:var(--c);background:$tobe_bg}
.tline .tl-card .dt{font-size:22px;font-weight:800;color:var(--c);line-height:1.25}
.tline .tl-card .t{font-size:23px;font-weight:700;line-height:1.3}
.tline .tl-card .d{font-size:20px;line-height:1.38;margin-top:4px}
.tline.alt .tl-card.dn{align-self:start}
.tline .tl-phase{grid-row:4;margin:14px 6px 0;border-radius:6px;font-size:22px;font-weight:700;line-height:1.3;padding:9px 16px;text-align:center}
/* quadrant */
.qd{display:grid;grid-template-columns:64px 1fr;overflow:hidden}
.qd-y{position:relative}
.qd-y .ye{position:absolute;left:0;right:10px;text-align:center;font-size:20px;color:$note;line-height:1.2}
.qd-y .ye.top{top:6px}.qd-y .ye.bot{bottom:6px}
.qd-y .rot{position:absolute;left:calc(50% - 5px);top:50%;transform:translate(-50%,-50%) rotate(-90deg);font-size:22px;font-weight:700;color:$text;white-space:nowrap;line-height:1.2}
.qd-x{grid-column:2;display:flex;justify-content:space-between;align-items:center;font-size:20px;color:$note;padding:0 6px;white-space:nowrap}
.qd-x b{font-size:22px;color:$text}
.qd-plot{position:relative;border:2px solid $line;background:$quad_bg}
.qd-q{position:absolute;width:50%;height:50%}
.qd-q.hot{background:$quad_hot}
.qd-ax{position:absolute;background:transparent}
.qd-ax.v{left:50%;top:0;bottom:0;border-left:2px dashed $grid}
.qd-ax.h{top:50%;left:0;right:0;border-top:2px dashed $grid}
.qd-name{position:absolute;font-size:26px;font-weight:800;color:$quad_name;line-height:1.2;white-space:nowrap}
.qd-name.qn-tl{left:18px;top:14px}.qd-name.qn-tr{right:18px;top:14px}.qd-name.qn-bl{left:18px;bottom:14px}.qd-name.qn-br{right:18px;bottom:14px}
.qd-pt{position:absolute;width:0;height:0}
.qd-dot{position:absolute;left:-12px;top:-12px;width:24px;height:24px;border-radius:50%;background:var(--c);border:3px solid $bg;box-shadow:0 0 0 2px var(--c)}
.qd-lab{position:absolute;white-space:nowrap;font-size:21px;font-weight:700;line-height:1.25;color:$text;padding:0 2px;text-shadow:0 0 3px $bg,0 0 3px $bg,0 0 4px $bg}
.qd-lab.pos-r{left:20px;top:0;transform:translateY(-50%)}
.qd-lab.pos-l{right:20px;top:0;transform:translateY(-50%)}
.qd-lab.pos-t{left:0;bottom:18px;transform:translateX(-50%)}
.qd-lab.pos-b{left:0;top:18px;transform:translateX(-50%)}
.qd-lab.pos-tr{left:12px;bottom:12px}
.qd-lab.pos-br{left:12px;top:12px}
.qd-lab.pos-tl{right:12px;bottom:12px}
.qd-lab.pos-bl{right:12px;top:12px}
/* layers */
.layers{display:flex;flex-direction:column;gap:12px}
.layer{display:grid;grid-template-columns:var(--lw) 1fr;gap:14px;min-height:92px}
.layers.even .layer{flex:1 1 0;min-height:0}
.layers.withnote .layer{grid-template-columns:var(--lw) 1fr var(--nw)}
.layer .ln{background:var(--c);font-weight:700;font-size:24px;border-radius:8px;display:flex;align-items:center;justify-content:center;text-align:center;padding:10px 16px;line-height:1.3}
.layer .li{display:flex;flex-wrap:wrap;gap:10px;align-items:center;align-content:center;border:2px solid var(--c);border-radius:8px;padding:12px 16px;background:$bg}
.layer .it{flex:1 1 auto;text-align:center;border:1.5px solid $grid;border-radius:6px;padding:9px 18px;font-size:22px;background:$panel;line-height:1.35}
.layer .it.on{border:2px solid $key;color:$key;font-weight:700;background:$bg}
.layer .lnote{display:flex;align-items:center;font-size:20px;color:$note;line-height:1.35;padding-left:4px}
/* 비주얼 요약 */
.vs{position:absolute;left:0;top:0;width:1920px;height:1080px}
.vs-top{position:absolute;left:80px;right:80px;top:30px;height:84px;display:flex;align-items:flex-end;justify-content:space-between;gap:40px}
.vs-title{flex:1 1 auto;min-width:0;font-size:52px;font-weight:800;color:$key;letter-spacing:-1px;line-height:1.3;white-space:nowrap;overflow:hidden;padding-bottom:4px}
.vs-sub{flex:0 0 auto;font-size:30px;color:$sublabel;line-height:1.3;white-space:nowrap;padding-bottom:10px}
.vs-rule{position:absolute;left:80px;right:80px;top:120px;height:3px;background:$key}
.vs-col{position:absolute;top:146px;width:800px}
.vs-col.l{left:80px}.vs-col.r{left:1040px}
.vs-head{height:62px;border-radius:10px 10px 0 0;display:flex;align-items:center;gap:16px;padding:0 24px;color:$on_dark;font-size:28px;font-weight:700;white-space:nowrap;overflow:hidden}
.vs-head .tag{font-size:24px;font-weight:800;letter-spacing:.5px;border:2px solid $on_dark;border-radius:6px;padding:0 10px;line-height:1.3}
.vs-col.l .vs-head{background:$asis}.vs-col.r .vs-head{background:$key}
.vs-panel{position:relative;height:378px;border:2px solid;border-top:none;border-radius:0 0 10px 10px;overflow:hidden}
.vs-col.l .vs-panel{border-color:$asis_line;background:$asis_bg}
.vs-col.r .vs-panel{border-color:$key;background:$tobe_bg}
.vs-dg{position:absolute;left:24px;top:22px;width:748px;height:330px}
.vs-dg svg.wire{position:absolute;left:0;top:0;width:748px;height:330px;overflow:visible}
.nd{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-radius:10px;font-size:23px;font-weight:700;line-height:1.28;padding:6px 12px;border:2.5px solid;background:$bg;overflow:hidden}
.nd .s{display:block;font-size:19px;font-weight:500;margin-top:2px;line-height:1.3}
.nd.a{border-color:$asis_line;color:$asis_ink}
.nd.b{border-color:$key;color:$text}
.nd.k{border-color:$key;background:$key;color:$on_dark}
.nd.x{border-color:$aux;color:$aux}
.nd.c{border-width:3px}
.cap{position:absolute;font-size:20px;line-height:1.3;display:flex;align-items:center}
.cap.a{color:$asis_ink}.cap.b{color:$text}
.vs-mid{position:absolute;left:880px;width:160px;top:208px;height:378px;display:flex;align-items:center;justify-content:center}
.vs-mid svg{width:104px;height:84px}
.vs-verdict{position:absolute;left:80px;top:600px;width:1760px;height:84px;display:grid;grid-template-columns:800px 160px 800px;align-items:center;font-size:50px;font-weight:800;white-space:nowrap;overflow:hidden;letter-spacing:-1px}
.vs-verdict>div{text-align:center;overflow:hidden}
.vs-verdict .a{color:$asis}.vs-verdict .op{color:$text;font-size:1.1em}.vs-verdict .b{color:$key}
.vs-verdict.one{display:flex;justify-content:center;color:$text}
.vs-desc{position:absolute;top:694px;width:800px;height:170px;overflow:hidden;list-style:none}
.vs-desc.l{left:80px;--c:$asis}.vs-desc.r{left:1040px;--c:$key}
.vs-desc li{position:relative;padding-left:30px;font-size:24px;line-height:1.38;margin-bottom:10px}
.vs-desc li::before{content:"";position:absolute;left:4px;top:.5em;width:12px;height:12px;background:var(--c)}
.vs-band{position:absolute;left:80px;width:1760px;top:880px;height:104px;background:$key;color:$on_dark;border-radius:10px;display:flex;align-items:center;justify-content:center;text-align:center;padding:0 48px;font-size:32px;font-weight:700;line-height:1.35;overflow:hidden}
/* 시사점 3축 표 */
.imp-title{color:$key !important}
.imp-sub{color:$sublabel !important}
.slide.k-implication .rule{background:$key}
.imp{display:grid;grid-template-columns:250px 1fr 1fr;grid-template-rows:56px;grid-auto-rows:auto;column-gap:14px;row-gap:12px;height:100%;align-content:stretch}
.imp .ch{font-size:26px;font-weight:700;color:$text;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:8px;display:flex;align-items:center;justify-content:center;text-align:center;white-space:nowrap}
.imp .lb{background:$label_bg;color:$text;font-size:27px;font-weight:700;display:flex;align-items:center;justify-content:center;text-align:center;padding:12px 18px;line-height:1.35}
.imp .cl{border:1.5px solid $cell_line;background:$bg;padding:18px 28px;display:flex;flex-direction:column;justify-content:center;min-width:0}
.imp .ld{font-size:27px;font-weight:700;line-height:1.36;color:$text;letter-spacing:-0.3px}
.imp ul{list-style:none;margin-top:12px}
.imp li{position:relative;color:$aux;font-size:23px;line-height:1.42;margin-top:6px;padding-left:30px}
.imp li::before{content:"";position:absolute;left:4px;top:.5em;width:12px;height:12px;border-radius:50%;background:$aux}
.imp li.l2{padding-left:62px;font-size:21px}
.imp li.l2::before{left:34px;width:11px;height:11px;background:transparent;border:2px solid $aux}
/* 표지, 목차, 감사 */
.brand{position:absolute;left:80px;top:62px;background:$brand_bg;color:$brand_fg;font-size:30px;font-weight:700;padding:8px 24px;line-height:1.3;letter-spacing:.5px}
.cv-logo{position:absolute;right:80px;top:56px;max-height:72px;max-width:360px}
.cv-main{position:absolute;left:80px;top:286px;width:1180px}
.cv-series{font-size:30px;font-weight:700;color:$accent;line-height:1.3}
.cv-title{font-size:68px;font-weight:900;line-height:1.22;letter-spacing:-1.5px;margin-top:22px}
.cv-subtitle{font-size:31px;color:$muted;line-height:1.4;margin-top:26px}
.cv-bar{width:120px;height:6px;background:$accent;margin-top:40px}
.cv-author{font-size:34px;font-weight:700;margin-top:30px;line-height:1.3}
.cv-date{font-size:28px;color:$muted;margin-top:6px;line-height:1.3}
.cv-note{position:absolute;left:80px;right:80px;top:950px;font-size:22px;color:$muted;line-height:1.35}
.cv-hero{position:absolute;left:1330px;top:250px;width:510px;height:580px}
.ag-title{position:absolute;left:80px;top:70px;font-size:40px;font-weight:700;border-left:8px solid $accent;padding-left:18px;line-height:1}
.ag-rows{position:absolute;left:220px;right:220px}
.ag-row{display:grid;grid-template-columns:260px 1fr;align-items:center;border-top:2px dashed $unknown}
.ag-row:last-child{border-bottom:2px dashed $unknown}
.ag-lab{font-weight:700;text-align:center;border-radius:6px}
.ag-tit{font-weight:700;padding-left:40px}
.ag-row.on .ag-lab{background:$label_bg;color:$text}.ag-row.on .ag-tit{color:$text}
.ag-row.off .ag-lab{background:$soft;color:$dim}.ag-row.off .ag-tit{color:$dim}
.ag-row.cur .ag-lab{background:$accent;color:$on_dark}
.sl-rows{position:absolute;left:140px;right:140px;top:210px}
.sl-rows.one{top:160px;bottom:110px;display:flex;flex-direction:column;justify-content:center}
.sl-it{display:flex;align-items:center;gap:22px;border-bottom:1px solid $hairline}
.sl-no{width:46px;height:46px;border-radius:50%;background:$line;color:$on_dark;font-weight:700;font-size:22px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}
.sl-rows.one .sl-no{width:54px;height:54px;font-size:25px}
.sl-tx{font-weight:500}
.tk-big{position:absolute;left:0;right:0;top:250px;text-align:center;font-size:84px;font-weight:900;line-height:1.2}
.tk-lines{position:absolute;left:0;right:0;top:420px;text-align:center;font-size:30px;line-height:1.6;color:$text}
.tk-who{position:absolute;left:0;right:0;top:672px;text-align:center}
.tk-name{font-size:36px;font-weight:700;line-height:1.3;margin-bottom:10px}
.tk-c{font-size:28px;line-height:1.45;color:$text}
""")


def _css():
    return _CSS.substitute(_derived(_THEME))


# 쪽 안에서 도는 스크립트 : 글꼴 준비 뒤 제목 글자 맞춤(data-fit-min), 사분면 이름 겹침 피하기
_PAGE_JS = r"""
(function(){
  function over(el){if(el.scrollWidth>el.clientWidth+1||el.scrollHeight>el.clientHeight+1)return true;
    var kids=el.querySelectorAll('*');for(var i=0;i<kids.length;i++){var c=kids[i];if(getComputedStyle(c).overflow!=='visible'&&(c.scrollWidth>c.clientWidth+1||c.scrollHeight>c.clientHeight+1))return true;}return false;}
  function fit(el){var min=parseFloat(el.getAttribute('data-fit-min')||'20');var fs=parseFloat(getComputedStyle(el).fontSize);var f0=fs;var g=0;
    while(over(el)&&fs>min&&g++<80){fs-=1;el.style.fontSize=fs+'px';}
    if(fs<f0)el.setAttribute('data-qa-warn','글자 자동 축소 ['+(el.getAttribute('data-qa')||'')+'] '+f0+'px → '+fs+'px : 문장을 줄이면 원래 크기로 보임');}
  function rel(r,b){return {l:r.left-b.left,t:r.top-b.top,r:r.right-b.left,b:r.bottom-b.top};}
  function hit(a,b){return !(a.r<=b.l||b.r<=a.l||a.b<=b.t||b.b<=a.t);}
  function declutter(plot){var B=plot.getBoundingClientRect();var placed=[];
    plot.querySelectorAll('.qd-dot,.qd-name').forEach(function(d){placed.push(rel(d.getBoundingClientRect(),B));});
    plot.querySelectorAll('.qd-pt').forEach(function(pt){var lab=pt.querySelector('.qd-lab');if(!lab)return;
      var pref=pt.getAttribute('data-pos')||'r';var order=[pref,'r','l','t','b','tr','br','tl','bl'];var ok=false;
      for(var i=0;i<order.length;i++){lab.className='qd-lab pos-'+order[i];var r=rel(lab.getBoundingClientRect(),B);
        var inside=r.l>=8&&r.t>=6&&r.r<=B.width-8&&r.b<=B.height-6;
        if(inside&&!placed.some(function(q){return hit(q,r);})){placed.push(r);ok=true;break;}}
      if(!ok){lab.className='qd-lab pos-'+pref;placed.push(rel(lab.getBoundingClientRect(),B));
        lab.setAttribute('data-qa-warn','사분면 점 이름 겹침 : '+lab.textContent);}});}
  function srcRoom(){var s=document.querySelector('.source'),b=document.querySelector('.body');if(!s||!b)return;
    var st=s.getBoundingClientRect().top,br=b.getBoundingClientRect();
    if(st-8<br.bottom){b.style.height=Math.max(120,Math.floor(st-8-br.top))+'px';b.setAttribute('data-shrunk','1');}}
  function run(){srcRoom();document.querySelectorAll('[data-fit-min]').forEach(fit);document.querySelectorAll('.qd-plot').forEach(declutter);window.__deckReady=true;}
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(run);}else{window.addEventListener('load',run);}
})();
"""


def _page(no, inner, kind, part="", footer=True, pgnum=True, extra_class=""):
    foot = ""
    if footer:
        foot += '<div class="frule"></div><div class="credit">%s</div>' % esc(_prof()["CREDIT"])
    if pgnum and no is not None and str(no) != "":
        foot += '<div class="pgtri"></div><div class="pgnum">%s</div>' % esc(no)
    cls = ("slide k-%s %s" % (kind, extra_class)).strip()
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            '<meta name="generator" content="image-deck %s"><style>%s</style></head><body>'
            '<div class="%s" data-kind="%s" data-part="%s">%s%s</div><script>%s</script></body></html>'
            % (__version__, _css(), cls, _attr(kind), _attr(strip_tags(part or "")), inner, foot, _PAGE_JS))


# ---------------------------------------------------------------------------
# 6. 쪽 함수
# ---------------------------------------------------------------------------
def slide_html(no, sec_title, sec_sub, headline, body, source=None, kind="content", part=None):
    """5-Zone 쪽. kind="content" 가 기본, 다른 값이면 body 를 쪽 전체에 그대로 둠(plain).

    no 쪽 번호 · sec_title 섹션 라벨(왼쪽 빨강) · sec_sub 소제목(오른쪽 회색, 「① …」)
    headline 헤드라인 2줄 이내 · body 컴포넌트 HTML · source 출처(「※ Source : 」 뒤에 붙음)
    part 덱 QA 의 섹션 묶음 이름(생략하면 sec_title)
    """
    part = strip_tags(sec_title) if part is None else part
    if kind == "content":
        inner = ('<div class="sec"><div class="sec-title">%s</div><div class="sec-sub">%s</div></div>'
                 '<div class="rule"></div><div class="headline">%s</div><div class="body">%s</div>'
                 % (sec_title, sec_sub or "", headline, body))
    else:
        inner = body
    if source:
        inner += '<div class="source">※ Source : %s</div>' % source
    return _page(no, inner, kind, part=part)


def plain_html(no, inner, footer=True, part=""):
    """전면 이미지 등 자유 배치 쪽(크레딧·쪽 번호 유지). 예 : 이미지 한 장을 쪽 전체에."""
    return _page(no, inner, "plain", part=part, footer=footer)


def _hero_default():
    """표지 오른쪽 기본 장식 : 테마 색 막대 묶음(데이터 느낌, 내용 없음)."""
    t = _derived(_THEME)
    hs = [0.34, 0.52, 0.44, 0.68, 0.58, 0.86, 1.0]
    w, gap, H = 50, 22, 520
    bars = []
    for i, h in enumerate(hs):
        col = t["accent"] if i == len(hs) - 1 else (t["outside"] if i == 3 else t["hairline"])
        bh = int(H * h)
        bars.append('<div style="position:absolute;left:%dpx;bottom:40px;width:%dpx;height:%dpx;background:%s;border-radius:4px 4px 0 0"></div>'
                    % (i * (w + gap), w, bh, col))
    base = '<div style="position:absolute;left:0;right:0;bottom:34px;height:6px;background:%s"></div>' % t["line"]
    return "".join(bars) + base


def cover_html(title, subtitle="", series="", date="", note="", logo=None, hero=None, author=None, no=None):
    """표지. 좌상단 [ BRAND ] 라벨(프로필 BRAND, 기본 Insight Report), 시리즈 줄, 제목, 부제,
    작성자(프로필 AUTHOR_KR), 날짜(YYYY.MM.DD), 아래 안내 줄.

    logo : 로고 이미지 경로(오른쪽 위). hero : None 이면 기본 장식, False 면 없음,
    문자열이면 HTML, .png/.jpg/.svg 경로면 그 이미지.
    """
    p = _prof()
    who = p["AUTHOR_KR"] if author is None else author
    parts = ['<div class="brand">%s</div>' % esc(p["BRAND_LABEL"])]
    if logo:
        parts.append('<img class="cv-logo" src="%s" alt="">' % _attr(_file_uri(logo)))
    main = ""
    if series:
        main += '<div class="cv-series">%s</div>' % series
    main += '<div class="cv-title">%s</div>' % title
    if subtitle:
        main += '<div class="cv-subtitle">%s</div>' % subtitle
    main += '<div class="cv-bar"></div>'
    if who:
        main += '<div class="cv-author">%s</div>' % who
    if date:
        main += '<div class="cv-date">(%s)</div>' % date
    parts.append('<div class="cv-main">%s</div>' % main)
    if hero is None:
        parts.append('<div class="cv-hero">%s</div>' % _hero_default())
    elif hero:
        h = str(hero)
        if re.search(r"\.(png|jpe?g|svg|webp)$", h, re.I):
            parts.append('<div class="cv-hero fig"><img src="%s" alt=""></div>' % _attr(_file_uri(h)))
        else:
            parts.append('<div class="cv-hero">%s</div>' % h)
    if note:
        parts.append('<div class="cv-note">%s</div>' % note)
    return _page(no, "".join(parts), "cover", footer=False, pgnum=False)


def agenda_html(rows, active=None, title="목차", no=None):
    """목차(간지). rows = [("1부", "제목"), ...] 또는 ["제목", ...].
    active=None 이면 모든 행을 같은 굵기로, 정수면 그 행만 강조하고 나머지는 흐리게(간지)."""
    norm = []
    for i, r in enumerate(rows):
        if isinstance(r, (list, tuple)):
            norm.append((r[0], r[1]))
        else:
            norm.append(("%02d" % (i + 1), r))
    n = len(norm)
    if not 1 <= n <= 7:
        raise ValueError("agenda_html: 행은 1~7개")
    lab_fs, tit_fs, pad = (34, 38, 20) if n <= 4 else ((30, 33, 14) if n <= 5 else (26, 29, 9))
    top = 230 if n <= 4 else 200
    out = []
    for i, (a, b) in enumerate(norm):
        state = "on" if (active is None or active == i) else "off"
        if active is not None and active == i:
            state += " cur"
        out.append('<div class="ag-row %s" style="padding:%dpx 0"><div class="ag-lab" style="font-size:%dpx;padding:%dpx 0">%s</div>'
                   '<div class="ag-tit" style="font-size:%dpx">%s</div></div>'
                   % (state, pad, lab_fs, pad + 2, a, tit_fs, b))
    inner = ('<div class="ag-title">%s</div><div class="ag-rows" style="top:%dpx">%s</div>'
             % (title, top, "".join(out)))
    return _page(no, inner, "agenda")


def sublist_html(items, title, no=None):
    """세부 목차. 6개 이하는 한 열(글자를 키우고 위아래 가운데), 7개 이상은 두 열."""
    n = len(items)
    if not 1 <= n <= 24:
        raise ValueError("sublist_html: 항목은 1~24개")
    two = n > 6
    half = (n + 1) // 2 if two else n
    if two:
        fs, pad = (28, 12) if n <= 14 else ((25, 8) if n <= 20 else (22, 5))
    else:
        fs, pad = 32, 20

    def col(its, start):
        return "".join('<div class="sl-it" style="padding:%dpx 0"><div class="sl-no">%d</div>'
                       '<div class="sl-tx" style="font-size:%dpx">%s</div></div>' % (pad, start + j + 1, fs, t)
                       for j, t in enumerate(its))
    if two:
        inner = ('<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 70px"><div>%s</div><div>%s</div></div>'
                 % (col(items[:half], 0), col(items[half:], half)))
    else:
        inner = '<div style="width:1240px">%s</div>' % col(items, 0)
    return _page(no, '<div class="ag-title">%s</div><div class="sl-rows%s">%s</div>'
                 % (title, "" if two else " one", inner), "sublist")


def thanks_html(no=None, title="감사합니다.", lines=None):
    """감사 쪽. 프로필 AUTHOR_KR / PHONE_KR(비면 줄 생략) / EMAIL 을 한 줄씩."""
    p = _prof()
    if lines is None:
        lines = ["이 자료는 지속적으로 업데이트되어 공개될 예정입니다.",
                 "사례 연구나 협업에 관심 있는 기업 및 기관의 연락을 환영합니다.",
                 "보고서, 출판, 강연 문의는 편하게 연락 주세요."]
    contact = "".join('<div class="tk-c">%s</div>' % esc(x) for x in (p.get("PHONE_KR", ""), p["EMAIL"]) if x)
    inner = ('<div class="brand">%s</div><div class="tk-big">%s</div><div class="tk-lines">%s</div>'
             '<div class="tk-who"><div class="tk-name">%s</div>%s</div>'
             % (esc(p["BRAND_LABEL"]), title, "<br>".join(lines), esc(p["AUTHOR_KR"]), contact))
    return _page(no, inner, "thanks")


# ---- 비주얼 요약 -----------------------------------------------------------
_DG_W, _DG_H = 748, 330


_EMPH_KEYS = ("key", "aux")


def _is_emph(v):
    return v is None or v is True or v is False or (isinstance(v, str) and v in _EMPH_KEYS)


def _norm_node(it):
    """도해 요소 : "글" | ("글", 강조) | ("글", "보조 글") | ("글", "보조 글", 강조) | {"t":..,"s":..,"e":..}
    강조 : None | "key" 또는 True(빨강 채움, To-Be 열) | "aux"(적갈색 테두리)
    두 칸 튜플의 둘째 값이 강조 값(None, True, False, "key", "aux")이 아니면 보조 글로 읽음."""
    if isinstance(it, dict):
        return it.get("t", ""), it.get("s", ""), it.get("e")
    if isinstance(it, (list, tuple)):
        if len(it) == 1:
            return it[0], "", None
        if len(it) == 2:
            if _is_emph(it[1]):
                return it[0], "", it[1]
            return it[0], it[1], None
        return it[0], it[1], it[2]
    return it, "", None


def _node(x, y, w, h, text, sub, emph, side, extra=""):
    cls = "a" if side == "l" else "b"
    if emph in ("key", True) and side == "r":
        cls = "k"
    elif emph == "aux":
        cls = "x"
    s = '<span class="s">%s</span>' % sub if sub else ""
    return ('<div class="nd %s %s qa-fit" data-qa="도해 상자" data-fit-min="19" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s%s</div>'
            % (cls, extra, x, y, w, h, text, s))


def _wire(x1, y1, x2, y2, color, arrow=True, dash=False):
    d = ' stroke-dasharray="8 7"' if dash else ""
    m = ' marker-end="url(#ah-%s)"' % color.lstrip("#") if arrow else ""
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3"%s%s/>'
            % (x1, y1, x2, y2, color, d, m))


def _marker(color):
    return ('<marker id="ah-%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0 0 L10 5 L0 10 z" fill="%s"/></marker>' % (color.lstrip("#"), color))


def _vs_diagram(spec, side):
    """비주얼 요약 한 열의 작은 도해. mode = flow | list | hub, 또는 html 로 직접."""
    if spec.get("html"):
        return spec["html"]
    t = _derived(_THEME)
    wire_c = t["asis"] if side == "l" else t["key"]
    mode = spec.get("mode", "flow")
    items = [_norm_node(x) for x in spec.get("items", [])]
    n = len(items)
    nodes, wires, markers = [], [], set()

    def emph_color(e):
        if e == "aux":
            return t["aux"]
        return wire_c

    if mode == "flow":
        if not 1 <= n <= 5:
            raise ValueError("visual_summary: flow 는 요소 1~5개")
        direction = spec.get("direction") or ("h" if n <= 3 else "v")
        if direction == "h":
            aw = 64
            w = int((_DG_W - (n - 1) * aw) / n)
            h = 150 if not any(s for _, s, _ in items) else 176
            y = int((_DG_H - h) / 2)
            for i, (tx, sb, e) in enumerate(items):
                x = i * (w + aw)
                nodes.append(_node(x, y, w, h, tx, sb, e, side))
                if i:
                    c = emph_color(e)
                    markers.add(c)
                    wires.append(_wire(x - aw + 8, y + h // 2, x - 8, y + h // 2, c))
        else:
            gap = 30 if n == 4 else 22
            h = int((_DG_H - (n - 1) * gap) / n)
            has_cap = any(s for _, s, _ in items)
            w = 330 if has_cap else 460
            x0 = 30 if has_cap else int((_DG_W - w) / 2)
            for i, (tx, sb, e) in enumerate(items):
                y = i * (h + gap)
                nodes.append(_node(x0, y, w, h, tx, "", e, side))
                if sb:
                    nodes.append('<div class="cap %s qa-fit" data-qa="도해 설명" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</div>'
                                 % ("a" if side == "l" else "b", x0 + w + 26, y, _DG_W - (x0 + w + 26), h, sb))
                if i:
                    c = emph_color(e)
                    markers.add(c)
                    wires.append(_wire(x0 + w // 2, y - gap + 3, x0 + w // 2, y - 4, c))
    elif mode == "list":
        if not 1 <= n <= 9:
            raise ValueError("visual_summary: list 는 요소 1~9개")
        cols = {1: 1, 2: 2, 3: 3, 4: 2}.get(n, 3)
        rows = int(math.ceil(n / float(cols)))
        gx, gy = 18, 18
        w = int((_DG_W - (cols - 1) * gx) / cols)
        h = int((_DG_H - (rows - 1) * gy) / rows)
        for i, (tx, sb, e) in enumerate(items):
            r, c = divmod(i, cols)
            nodes.append(_node(c * (w + gx), r * (h + gy), w, h, tx, sb, e, side))
    elif mode == "hub":
        if not 1 <= n <= 6:
            raise ValueError("visual_summary: hub 는 주변 요소 1~6개")
        cx, cy = _DG_W // 2, _DG_H // 2
        cw, ch = 220, 86
        sw, sh = 196, 64
        # 주변 요소 자리(상자 왼쪽 위 좌표). 가운데 상자와 60px 이상 떨어지게 고정 배치, 시계 방향
        slot = {"T": (276, 0), "TL": (56, 4), "TR": (496, 4), "L": (0, 133), "R": (552, 133),
                "BL": (56, 262), "BR": (496, 262), "B": (276, 266)}
        order = {1: ["R"], 2: ["L", "R"], 3: ["T", "BR", "BL"], 4: ["TL", "TR", "BR", "BL"],
                 5: ["T", "R", "BR", "BL", "L"], 6: ["TL", "TR", "R", "BR", "BL", "L"]}[n]
        ctext, csub, ce = _norm_node(spec.get("center", ""))
        for (tx, sb, e), key in zip(items, order):
            x, y = slot[key]
            c = emph_color(e)
            wires.append(_wire(cx, cy, x + sw // 2, y + sh // 2, c, arrow=False, dash=(side == "l")))
            nodes.append(_node(x, y, sw, sh, tx, sb, e, side))
        nodes.append(_node(cx - cw // 2, cy - ch // 2, cw, ch, ctext, csub,
                           ce if ce is not None else ("key" if side == "r" else None), side, extra="c"))
    else:
        raise ValueError("visual_summary: mode 는 flow, list, hub 중 하나")
    svg = ('<svg class="wire" viewBox="0 0 %d %d"><defs>%s</defs>%s</svg>'
           % (_DG_W, _DG_H, "".join(_marker(c) for c in sorted(markers)), "".join(wires)))
    return svg + "".join(nodes)


def visual_summary_html(no, title, asis, tobe, verdict, conclusion, sub=None, part="", arrow=True):
    """「비주얼 요약」 전면 도해형 쪽 (kind="visual").

    asis, tobe : {"tag": "As-Is", "title": "열 제목", "mode": "flow"|"list"|"hub",
                  "items": [...], "center": "hub 가운데", "direction": "h"|"v", "desc": [설명 3줄]}
    verdict    : ("기존 A", "<", "새 B") 이면 열에 맞춰 A·부호·B, 문자열이면 한 줄 가운데
    conclusion : 맨 아래 결론 띠 문장(빨강 바탕, 흰 글씨)
    헤드라인 문단과 Source 줄은 없음. 크레딧과 쪽 번호는 유지.
    """
    t = _derived(_THEME)
    parts = ['<div class="vs-top"><div class="vs-title qa-fit" data-qa="도해 제목" data-fit-min="40">%s</div>%s</div>'
             % (title, ('<div class="vs-sub">%s</div>' % sub) if sub else ""),
             '<div class="vs-rule"></div>']
    for side, spec in (("l", asis), ("r", tobe)):
        tag = spec.get("tag", "As-Is" if side == "l" else "To-Be")
        parts.append('<div class="vs-col %s"><div class="vs-head qa-fit" data-qa="열 머리" data-fit-min="22"><span class="tag">%s</span><span>%s</span></div>'
                     '<div class="vs-panel qa-fit" data-qa="도해 칸"><div class="vs-dg">%s</div></div></div>'
                     % (side, esc(tag), spec.get("title", ""), _vs_diagram(spec, side)))
        desc = spec.get("desc", [])
        if len(desc) > 3:
            raise ValueError("visual_summary: 열 설명은 3줄 이하")
        parts.append('<ul class="vs-desc %s qa-fit" data-qa="열 설명">%s</ul>' % (side, "".join("<li>%s</li>" % d for d in desc)))
    if arrow:
        parts.append('<div class="vs-mid"><svg viewBox="0 0 104 84"><path d="M0 28 H58 V6 L102 42 L58 78 V56 H0 Z" fill="%s"/></svg></div>' % t["key"])
    if isinstance(verdict, (list, tuple)) and len(verdict) == 3:
        a, op, b = verdict
        parts.append('<div class="vs-verdict qa-fit" data-qa="판정" data-fit-min="34"><div class="a">%s</div><div class="op">%s</div><div class="b">%s</div></div>'
                     % (esc(a), esc(op), esc(b)))
    else:
        parts.append('<div class="vs-verdict one qa-fit" data-qa="판정" data-fit-min="34">%s</div>' % esc(verdict))
    parts.append('<div class="vs-band qa-fit" data-qa="결론 띠" data-fit-min="26">%s</div>' % conclusion)
    return _page(no, '<div class="vs qa-scope">%s</div>' % "".join(parts), "visual", part=part)


# ---- 시사점 3축 표 ----------------------------------------------------------
def _imp_cell(cell):
    """칸 : ("리드 A → B", ["1단 불릿", ("2단 불릿", 2)]) 또는 {"lead":.., "bullets":[..]}"""
    if isinstance(cell, dict):
        lead, bullets = cell.get("lead", ""), cell.get("bullets", [])
    else:
        lead, bullets = cell[0], (cell[1] if len(cell) > 1 else [])
    lis = []
    for b in bullets:
        if isinstance(b, (list, tuple)):
            txt, lvl = b[0], (b[1] if len(b) > 1 else 1)
        else:
            txt, lvl = b, 1
        lis.append('<li class="l%d">%s</li>' % (2 if lvl == 2 else 1, txt))
    warn = ' data-qa-warn="시사점 칸 불릿 %d개 : 2개 이하 권장"' % len(lis) if len(lis) > 2 else ""
    return '<div class="cl"%s><div class="ld">%s</div>%s</div>' % (warn, lead, "<ul>%s</ul>" % "".join(lis) if lis else "")


def implication_html(no, title, headline, rows, sub="① 개요", topic=None, col_titles=None, part=None):
    """「시사점」 3축 표 쪽 (kind="implication", 5-Zone 변형).

    title : 「N. {주제} 시사점」(빨강 굵게) · sub : 오른쪽 회색 라벨 · headline : 검정 2문장
    rows  : [(관점 라벨, 가운데 칸, 오른쪽 칸), ...] 3행. 칸 = (리드, [불릿 ≤2])
    col_titles : 열 제목 3개. 없으면 ("관점", "{topic}로 바뀔 때 함께 오는 변화", "요구 사항")
    하단 ☞ 줄·※ 단서 줄·Source 줄 없음.
    """
    if col_titles is None:
        mid = "%s%s 바뀔 때 함께 오는 변화" % (topic, josa_ro(topic)) if topic else "바뀔 때 함께 오는 변화"
        col_titles = ("관점", mid, "요구 사항")
    if len(col_titles) != 3:
        raise ValueError("implication_html: col_titles 는 3개")
    if not 1 <= len(rows) <= 4:
        raise ValueError("implication_html: 행은 3개 권장(1~4)")
    cells = ['<div class="ch">%s</div>' % c for c in col_titles]
    for r in rows:
        cells.append('<div class="lb">%s</div>' % r[0])
        cells.append(_imp_cell(r[1]))
        cells.append(_imp_cell(r[2]))
    body = '<div class="imp" data-c="implication">%s</div>' % "".join(cells)
    inner = ('<div class="sec"><div class="sec-title imp-title">%s</div><div class="sec-sub imp-sub">%s</div></div>'
             '<div class="rule"></div><div class="headline">%s</div><div class="body" style="height:725px">%s</div>'
             % (title, sub or "", headline, body))
    return _page(no, inner, "implication", part=strip_tags(title) if part is None else part)


# ---------------------------------------------------------------------------
# 7. 컴포넌트 (본문 조각)
# ---------------------------------------------------------------------------
def stats(items, cols=None):
    """수치 타일. items = [(값, 라벨, 보조, color_key), ...] (보조·color_key 생략 가능, 기본 inside)"""
    items = list(items)
    if not items:
        return ""
    cols = cols or min(len(items), 5)
    cells = []
    for it in items:
        v, l = it[0], it[1]
        s = it[2] if len(it) > 2 else ""
        c = _color(it[3] if len(it) > 3 else "inside")
        cells.append('<div class="stat" style="--c:%s"><div class="v">%s</div><div class="l">%s</div>%s</div>'
                     % (c, v, l, ('<div class="s">%s</div>' % s) if s else ""))
    return '<div class="stats" data-c="stats" style="grid-template-columns:repeat(%d,minmax(0,1fr))">%s</div>' % (cols, "".join(cells))


def cards(items, cols=3):
    """카드 격자. items = [(제목, 본문, color_key), ...]
    본문이 목록이면 줄마다 네모 불릿, 문자열이면 불릿 없이 그대로(칩·막대 같은 컴포넌트를 카드 안에 넣을 때)."""
    out = []
    for it in items:
        t, lines = it[0], it[1]
        c = _color(it[2] if len(it) > 2 and it[2] else "inside")
        if isinstance(lines, str):
            inner = '<div class="cb">%s</div>' % lines
        else:
            inner = "<ul>%s</ul>" % "".join("<li>%s</li>" % x for x in lines)
        out.append('<div class="card" style="--c:%s"><div class="t">%s</div>%s</div>' % (c, t, inner))
    return '<div class="cards" data-c="cards" style="grid-template-columns:repeat(%d,minmax(0,1fr))">%s</div>' % (cols, "".join(out))


def mini_table(headers, rows, widths=None, num_cols=(), em_rows=(), row_height=None):
    """표. widths = ["20%", ...] 또는 px 정수. num_cols = 오른쪽 정렬할 열 번호. em_rows = 옅은 빨강 행.
    row_height = 칸 높이(px). 행이 적어 쪽 아래가 비면 키워서 채움(글자 크기는 그대로)."""
    rows = [list(r) for r in rows]
    for i, r in enumerate(rows):
        if len(r) != len(headers):
            raise ValueError("mini_table: %d번째 행 칸 수 %d 이 머리 %d칸과 다름" % (i + 1, len(r), len(headers)))
    warn = ' data-qa-warn="표 %d행 : 8행 이하 권장"' % len(rows) if len(rows) > 8 else ""
    cg = ""
    if widths:
        cg = "<colgroup>%s</colgroup>" % "".join('<col style="width:%s">' % (("%dpx" % w) if isinstance(w, int) else w) for w in widths)
    nc = set(num_cols or ())
    head = "<tr>%s</tr>" % "".join('<th%s>%s</th>' % (' class="num"' if j in nc else "", h) for j, h in enumerate(headers))
    body = "".join('<tr%s>%s</tr>' % (' class="em"' if i in set(em_rows or ()) else "",
                                       "".join('<td%s>%s</td>' % (' class="num"' if j in nc else "", c) for j, c in enumerate(r)))
                   for i, r in enumerate(rows))
    style = (' style="--rh:%dpx"' % int(row_height)) if row_height else ""
    return '<table class="mt%s" data-c="mini_table"%s%s>%s%s%s</table>' % (" tall" if row_height else "", warn, style, cg, head, body)


def two_panel(left, right, ratio="1fr 1fr", gap=28, align="start"):
    """두 칸 배치(레이아웃, 컴포넌트 종류 셈에 들어가지 않음). align = start | center | end | stretch"""
    if align not in ("start", "center", "end", "stretch"):
        raise ValueError("two_panel: align 은 start, center, end, stretch 중 하나")

    def col(h):
        return '<div class="col%s">%s</div>' % (" colfill" if 'class="fill"' in h else "", h)
    return ('<div class="tp" data-l="two_panel" style="grid-template-columns:%s;gap:%dpx;align-items:%s">%s%s</div>'
            % (ratio, gap, align, col(left), col(right)))


def fill(*groups, **kw):
    """본문(.body)의 남는 높이를 차지하고 그 안에서 묶음(group)들 사이 간격을 고르게 나눔(레이아웃).
    본문 바로 아래 단계에서만 씀. 묶음 하나 = 함께 붙어 있어야 할 조각들을 이은 문자열.

    two_panel(align="stretch") 의 한쪽 칸 안에서 쓰면 그 칸을 옆 칸 높이에 맞춰 채움.

    예 : fill(cards(...), panel_title("흐름") + flow(...))   # 카드 묶음과 흐름 묶음 사이를 고르게 벌림
    align = evenly(위·사이·아래 같은 간격, 기본) | between(첫 묶음은 위, 끝 묶음은 아래) | center | start | end
    """
    align = kw.pop("align", "evenly")
    if kw:
        raise TypeError("fill: 알 수 없는 인자 %s" % ", ".join(kw))
    jc = {"center": "center", "start": "flex-start", "end": "flex-end", "between": "space-between",
          "evenly": "space-evenly"}.get(align)
    if jc is None:
        raise ValueError("fill: align 은 between, evenly, center, start, end 중 하나")
    inner = "".join('<div class="grp">%s</div>' % g for g in groups if g)
    return '<div class="fill" data-l="fill" style="justify-content:%s">%s</div>' % (jc, inner)


def panel_title(t):
    """칸 위 작은 제목(두 칸 배치 안에서 씀)."""
    return '<div class="ptitle">%s</div>' % t


def flow(steps, active=None, color_key="inside"):
    """단계 화살표. steps = [(제목, 설명), ...] 또는 ["제목", ...]. active = 강조할 단계 번호(0부터)."""
    if isinstance(active, int):
        act = {active}
    else:
        act = set(active or ())
    out = []
    for i, st in enumerate(steps):
        if isinstance(st, (list, tuple)):
            t, d = st[0], (st[1] if len(st) > 1 else "")
        else:
            t, d = st, ""
        if i:
            out.append('<div class="arr"><svg viewBox="0 0 20 34"><path d="M3 3 L17 17 L3 31"/></svg></div>')
        out.append('<div class="step%s"><div class="t">%s</div>%s</div>'
                   % (" on" if i in act else "", t, ('<div class="d">%s</div>' % d) if d else ""))
    return '<div class="flow" data-c="flow" style="--c:%s">%s</div>' % (_color(color_key), "".join(out))


_CHIP_KIND = {"": "inside", "red": "inside", "inside": "inside", "관내": "inside",
              "navy": "outside", "outside": "outside", "관외": "outside",
              "grey": "unknown", "gray": "unknown", "unknown": "unknown", "미확인": "unknown",
              "hollow": "hollow", "key": "key", "aux": "aux"}


def chip(t, kind=""):
    """관내(빨강)·관외(네이비)·미확인(회색 점선) 등 꼬리표. kind = ""|red|navy|grey|hollow|key|aux"""
    k = _CHIP_KIND.get(kind)
    if k is None:
        raise ValueError("chip: kind %r 은 red, navy, grey, hollow, key, aux 중 하나" % kind)
    if k in ("unknown", "hollow"):
        return '<span class="chip %s" data-c="chip">%s</span>' % (k, t)
    bg = _color(k)
    fg = _THEME["on_dark"] if contrast_ratio(_THEME["on_dark"], bg) >= 4.5 else _THEME["text"]
    return '<span class="chip" data-c="chip" style="background:%s;color:%s">%s</span>' % (bg, fg, t)


def callout(t):
    """☞ 정리 줄(쪽 절반 이상에 한 줄씩)."""
    return '<div class="callout" data-c="callout"><span class="mk">☞</span>%s</div>' % t


def note(t):
    """작은 보조 글(19px 회색)."""
    return '<div class="note" data-c="note">%s</div>' % t


def chart_img(path, height=560, caption=None):
    """그림 파일(PNG·SVG·JPG)을 높이 height 칸에 맞춰 넣음. 경로는 어디서 실행해도 되게 절대 URI 로 바꿈."""
    cap = '<div class="figcap">%s</div>' % caption if caption else ""
    return ('<div data-c="chart_img"><div class="fig" style="height:%dpx"><img src="%s" alt=""></div>%s</div>'
            % (height, _attr(_file_uri(path)), cap))


def hbars(items, unit="", max_value=None, color_key="inside", label_width=None, bar_height=None, title=None,
          height=None):
    """CSS 가로 막대. items = [(라벨, 값[, color_key[, 표시 글]]), ...]

    값이 문자열(예 "1,234")이면 그대로 표시하고 쉼표를 뺀 수로 길이를 정함.
    max_value 를 주면 여러 막대 묶음의 눈금을 맞출 수 있음. 음수는 쓰지 않음.
    bar_height 를 생략하면 막대 수에 맞춤(4개 이하 46px, 6개 이하 38px, 그 밖 30px).
    height 를 주면 그 높이 안에 막대를 위아래로 고르게 벌려 놓음(옆 칸과 높이를 맞출 때).
    """
    norm = []
    for it in items:
        label, raw = it[0], it[1]
        ck = it[2] if len(it) > 2 and it[2] else color_key
        disp = it[3] if len(it) > 3 and it[3] is not None else None
        if isinstance(raw, str):
            v = float(raw.replace(",", ""))
            disp = disp if disp is not None else raw + unit
        else:
            v = float(raw)
            disp = disp if disp is not None else _fmt_num(raw) + unit
        if v < 0:
            raise ValueError("hbars: 음수 값 %r 은 쓰지 않음" % raw)
        norm.append((label, v, _color(ck), disp))
    if not norm:
        return ""
    mx = float(max_value) if max_value else max(v for _, v, _, _ in norm)
    mx = mx or 1.0
    vw = int(max(_est_width(d, 21) for _, _, _, d in norm) + 16)
    lw = label_width or int(min(420, max(140, max(_est_width(l, 21) for l, _, _, _ in norm) + 10)))
    n = len(norm)
    if bar_height is None:
        bar_height = 46 if n <= 4 else (38 if n <= 6 else 30)
    rg = 24 if n <= 4 else (18 if n <= 6 else (12 if n <= 8 else 9))
    warn = []
    if n > 10:
        warn.append("막대 %d개 : 10개 이하 권장" % n)
    rows = []
    for label, v, c, d in norm:
        frac = v / mx
        if frac > 1.0:
            warn.append("막대 값 %s 이 max_value 를 넘음" % d)
            frac = 1.0
        rows.append('<div class="hl">%s</div><div class="ht"><div class="hb" style="width:calc((100%% - %dpx) * %.4f);background:%s"></div>'
                    '<div class="hv">%s</div></div>' % (label, vw, frac, c, d))
    cap = '<div class="hcap">%s</div>' % title if title else ""
    w = ' data-qa-warn="%s"' % _attr("; ".join(warn)) if warn else ""
    hcss = (";height:%dpx;align-content:space-between" % int(height)) if height else ""
    return ('<div class="hbars qa-fit" data-qa="가로 막대" data-c="hbars"%s style="--lw:%dpx;--bh:%dpx;row-gap:%dpx%s">%s%s</div>'
            % (w, lw, bar_height, rg, hcss, cap, "".join(rows)))


def timeline(events, color_key="inside", alternate=None, phases=None):
    """가로 타임라인. events = [(날짜, 제목, 한 줄 설명[, 강조]), ...] 2~8개.
    6개 이하는 날짜가 선 위, 카드가 선 아래 한 줄. 7개 이상(또는 alternate=True)은 카드가 위·아래 번갈아 놓임.
    강조 = True(빨강 #C00000) 또는 color_key. 높이는 내용에 맞춰 정해짐.
    phases = [(첫 사건 번호, 끝 사건 번호, "시기 이름", color_key), ...] : 카드 아래 시기 띠(번호는 0부터)."""
    ev = []
    for e in events:
        d, t = e[0], e[1]
        ds = e[2] if len(e) > 2 else ""
        em = e[3] if len(e) > 3 else False
        ev.append((d, t, ds, em))
    n = len(ev)
    if not 2 <= n <= 8:
        raise ValueError("timeline: 사건은 2~8개")
    base = _color(color_key)
    alt = (n >= 7) if alternate is None else bool(alternate)
    slot = 100.0 / n

    def col_of(em):
        if em is True:
            return _color("key")
        if em:
            return _color(em)
        return base

    out, rail = [], []
    for i, (d, t, ds, em) in enumerate(ev):
        c = col_of(em)
        cx = (i + 0.5) * slot
        emc = " em" if em else ""
        desc = ('<div class="d">%s</div>' % ds) if ds else ""
        rail.append('<div class="tl-dot%s" style="left:%.3f%%;--c:%s"></div>' % (emc, cx, c))
        if not alt:
            rail.append('<div class="tl-stem dn" style="left:%.3f%%;--c:%s"></div>' % (cx, c))
            out.append('<div class="tl-date" style="grid-column:%d;color:%s">%s</div>' % (i + 1, c, d))
            out.append('<div class="tl-card dn%s" style="grid-column:%d;--c:%s"><div class="t">%s</div>%s</div>'
                       % (emc, i + 1, c, t, desc))
        else:
            up = (i % 2 == 0)
            a, b = max(1, 2 * i), min(2 * n + 1, 2 * i + 4)
            rail.append('<div class="tl-stem %s" style="left:%.3f%%;--c:%s"></div>' % ("up" if up else "dn", cx, c))
            out.append('<div class="tl-card %s%s" style="grid-column:%d/%d;--c:%s"><div class="dt">%s</div><div class="t">%s</div>%s</div>'
                       % ("up" if up else "dn", emc, a, b, c, d, t, desc))
    for ph in phases or ():
        a, b, label = int(ph[0]), int(ph[1]), ph[2]
        c = _color(ph[3] if len(ph) > 3 and ph[3] else "outside")
        if not (0 <= a <= b < n):
            raise ValueError("timeline: phases 의 사건 번호 (%d, %d) 가 0~%d 범위 밖" % (a, b, n - 1))
        span = (2 * a + 1, 2 * b + 3) if alt else (a + 1, b + 2)
        fg = _THEME["on_dark"] if contrast_ratio(_THEME["on_dark"], c) >= 4.5 else _THEME["text"]
        out.append('<div class="tl-phase" style="grid-column:%d/%d;background:%s;color:%s">%s</div>'
                   % (span[0], span[1], c, fg, label))
    cols = 2 * n if alt else n
    return ('<div class="tline%s qa-fit" data-qa="타임라인" data-c="timeline" style="grid-template-columns:repeat(%d,minmax(0,1fr))">'
            '%s<div class="tl-rail">%s</div></div>' % (" alt" if alt else "", cols, "".join(out), "".join(rail)))


def quadrant(x_label, y_label, points, quadrant_names=("", "", "", ""), x_ends=("낮음", "높음"),
             y_ends=("낮음", "높음"), height=600, hot=1):
    """2x2 포지셔닝. points = [(이름, x, y[, color_key[, 이름 위치]]), ...], x·y 는 0~1.
    quadrant_names = (왼쪽 위, 오른쪽 위, 왼쪽 아래, 오른쪽 아래). hot = 옅은 빨강으로 칠할 칸 번호(None 이면 없음).
    이름 위치 r·l·t·b(기본 r). 겹치면 렌더 때 자동으로 다른 자리로 옮기고, 못 피하면 QA 경고."""
    if len(quadrant_names) != 4:
        raise ValueError("quadrant: quadrant_names 는 4개 (왼쪽 위, 오른쪽 위, 왼쪽 아래, 오른쪽 아래)")
    H = int(height)
    xh = 52
    ph = H - xh
    cells = []
    pos = [("left:0;top:0", "qn-tl"), ("left:50%;top:0", "qn-tr"), ("left:0;top:50%", "qn-bl"), ("left:50%;top:50%", "qn-br")]
    for i, (css, nm) in enumerate(pos):
        cells.append('<div class="qd-q%s" style="%s"></div>' % (" hot" if hot == i else "", css))
    names = "".join('<div class="qd-name %s">%s</div>' % (pos[i][1], quadrant_names[i]) for i in range(4) if quadrant_names[i])
    pts = []
    for p in points:
        name, x, y = p[0], float(p[1]), float(p[2])
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise ValueError("quadrant: %s 의 좌표 (%s, %s) 는 0~1 이어야 함" % (strip_tags(name), x, y))
        c = _color(p[3] if len(p) > 3 and p[3] else "inside")
        lp = p[4] if len(p) > 4 and p[4] else "r"
        pts.append('<div class="qd-pt" data-pos="%s" style="left:%.3f%%;top:%.3f%%;--c:%s"><div class="qd-dot"></div>'
                   '<div class="qd-lab pos-%s">%s</div></div>' % (lp, x * 100, (1 - y) * 100, c, lp, name))
    ye = ""
    if y_ends and y_ends[1]:
        ye += '<div class="ye top">%s</div>' % y_ends[1]
    if y_ends and y_ends[0]:
        ye += '<div class="ye bot">%s</div>' % y_ends[0]
    ylab = '<div class="qd-y">%s<div class="rot">%s →</div></div>' % (ye, y_label)
    plot = ('<div class="qd-plot">%s<div class="qd-ax v"></div><div class="qd-ax h"></div>%s%s</div>'
            % ("".join(cells), names, "".join(pts)))
    xe = x_ends or ("", "")
    xlab = '<div class="qd-x"><span>%s</span><b>%s →</b><span>%s</span></div>' % (xe[0], x_label, xe[1])
    return ('<div class="qd qa-fit" data-qa="사분면" data-c="quadrant" style="height:%dpx;grid-template-rows:%dpx %dpx">%s%s%s</div>'
            % (H, ph, xh, ylab, plot, xlab))


def layers(rows, label_width=280, note_width=250, height=None):
    """적층 박스(계층·생태계 구조). 위 행이 위층.
    rows = [(층 이름, [요소, ...], color_key[, 오른쪽 메모]), ...]. 요소 = "글" 또는 ("글", True=강조)
    height 를 주면 그 높이를 층들이 똑같이 나눠 채움."""
    norm = []
    for r in rows:
        if isinstance(r, dict):
            norm.append((r.get("name", ""), r.get("items", []), r.get("color") or "outside", r.get("note", "")))
        else:
            norm.append((r[0], r[1], (r[2] if len(r) > 2 and r[2] else "outside"), (r[3] if len(r) > 3 else "")))
    any_note = any(nt for _, _, _, nt in norm)
    out = []
    for name, items, ck, nt in norm:
        c = _color(ck)
        fg = _THEME["on_dark"] if contrast_ratio(_THEME["on_dark"], c) >= 4.5 else _THEME["text"]
        its = []
        for it in items:
            if isinstance(it, (list, tuple)):
                its.append('<span class="it%s">%s</span>' % (" on" if len(it) > 1 and it[1] else "", it[0]))
            else:
                its.append('<span class="it">%s</span>' % it)
        noteh = ('<div class="lnote">%s</div>' % nt) if any_note else ""
        out.append('<div class="layer" style="--c:%s"><div class="ln" style="color:%s">%s</div><div class="li">%s</div>%s</div>'
                   % (c, fg, name, "".join(its), noteh))
    hcss = (";height:%dpx" % int(height)) if height else ""
    return ('<div class="layers%s%s qa-fit" data-qa="계층" data-c="layers" style="--lw:%dpx;--nw:%dpx%s">%s</div>'
            % (" withnote" if any_note else "", " even" if height else "", label_width, note_width, hcss, "".join(out)))


# ---------------------------------------------------------------------------
# 8. 렌더와 자동 QA
# ---------------------------------------------------------------------------
_QA_JS = r"""
() => {
  const out = {errors: [], warnings: [], comps: [], kind: '', part: '', text: '', hl: 0, src: 0, gap: null};
  const sl = document.querySelector('.slide');
  if (sl) { out.kind = sl.getAttribute('data-kind') || ''; out.part = sl.getAttribute('data-part') || ''; }
  out.comps = Array.from(document.querySelectorAll('[data-c]')).map(e => e.getAttribute('data-c'));
  const nlines = el => { const cs = getComputedStyle(el); let lh = parseFloat(cs.lineHeight); if (!lh) lh = parseFloat(cs.fontSize) * 1.2; return Math.round(el.scrollHeight / lh); };
  const body = document.querySelector('.body');
  if (body) {
    const oh = body.scrollHeight - body.clientHeight, ow = body.scrollWidth - body.clientWidth;
    if (oh > 2) out.errors.push('본문 넘침 ' + oh + 'px');
    if (ow > 2) out.errors.push('본문 가로 넘침 ' + ow + 'px');
  }
  const over = el => { let m = Math.max(el.scrollHeight - el.clientHeight, el.scrollWidth - el.clientWidth);
    el.querySelectorAll('*').forEach(c => { if (c.classList.contains('qa-fit')) return; const ov = getComputedStyle(c).overflow;
      if (ov !== 'visible') m = Math.max(m, c.scrollHeight - c.clientHeight, c.scrollWidth - c.clientWidth); });
    return m; };
  document.querySelectorAll('.qa-fit').forEach(el => {
    const m = over(el);
    if (m > 2) out.errors.push('넘침 [' + (el.getAttribute('data-qa') || el.className) + '] ' + m + 'px : 「' + el.textContent.trim().slice(0, 18) + '」');
  });
  const srcEl = document.querySelector('.source');
  if (srcEl && body) {
    let bottom = 0; const top = body.getBoundingClientRect().top;
    body.querySelectorAll('*').forEach(c => { const r = c.getBoundingClientRect(); if (r.height > 0 && r.bottom > bottom) bottom = r.bottom; });
    const st = srcEl.getBoundingClientRect().top;
    if (bottom > st + 1) out.errors.push('출처 줄과 본문 겹침 ' + Math.round(bottom - st) + 'px');
  }
  const sec = document.querySelector('.sec');
  if (sec && sec.scrollWidth - sec.clientWidth > 2) out.errors.push('섹션 라벨과 소제목이 한 줄에 들어가지 않음');
  const h = document.querySelector('.headline');
  if (h && h.textContent.trim()) { out.hl = nlines(h); if (out.hl >= 3) out.errors.push('헤드라인 ' + out.hl + '줄 (2줄 이내)'); }
  const s = document.querySelector('.source');
  if (s) { out.src = nlines(s); if (out.src > 2) out.errors.push('출처 ' + out.src + '줄 (2줄 이내)'); }
  Array.from(document.images).forEach(img => { if (!img.complete || img.naturalWidth === 0) out.errors.push('이미지 로드 실패 : ' + (img.getAttribute('src') || '').slice(-80)); });
  const small = [];
  document.querySelectorAll('.body, .qa-scope').forEach(sc => {
    const w = document.createTreeWalker(sc, NodeFilter.SHOW_TEXT); let n;
    while ((n = w.nextNode())) {
      if (!n.nodeValue.trim()) continue;
      const el = n.parentElement; const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const fs = parseFloat(cs.fontSize);
      if (fs < 18.95) small.push([fs, n.nodeValue.trim().slice(0, 16)]);
    }
  });
  if (small.length) { small.sort((a, b) => a[0] - b[0]); out.errors.push('19px 미만 글자 ' + small.length + '곳 (최소 ' + small[0][0] + 'px : 「' + small[0][1] + '」)'); }
  let clip = 0, sample = '';
  document.querySelectorAll('.slide *').forEach(el => {
    let has = false; el.childNodes.forEach(c => { if (c.nodeType === 3 && c.nodeValue.trim()) has = true; });
    if (!has) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (r.right > 1921 || r.bottom > 1081 || r.left < -1 || r.top < -1) { clip++; if (!sample) sample = el.textContent.trim().slice(0, 16); }
  });
  if (clip) out.errors.push('쪽 밖으로 나간 글자 ' + clip + '곳 (「' + sample + '」)');
  if (body && out.kind === 'content' && body.clientHeight > 0) {
    const bt = body.getBoundingClientRect(); let bottom = bt.top;
    body.querySelectorAll('*').forEach(c => { if (c.classList.contains('fill')) return; const r = c.getBoundingClientRect();
      if (r.width > 0 && r.height > 0 && r.bottom > bottom) bottom = r.bottom; });
    out.gap = Math.max(0, Math.round(bt.bottom - bottom));
    if (out.gap > body.clientHeight * 0.3) out.warnings.push('본문 아래 빈 공간 ' + out.gap + 'px (본문 높이의 ' + Math.round(out.gap * 100 / body.clientHeight) + '%) : 컴포넌트를 키우거나 더함');
    body.querySelectorAll('.fill').forEach(f => {
      const fr = f.getBoundingClientRect(); let prev = fr.top, big = 0;
      Array.from(f.children).forEach(g => { const r = g.getBoundingClientRect(); if (r.height > 0) { big = Math.max(big, r.top - prev); prev = r.bottom; } });
      big = Math.max(big, fr.bottom - prev);
      if (big > body.clientHeight * 0.22) out.warnings.push('fill 묶음 사이 빈 공간 ' + Math.round(big) + 'px : 내용을 더하거나 컴포넌트를 키움');
    });
  }
  if (body) {
    let prose = 0;
    body.querySelectorAll('*').forEach(el => { let t = ''; el.childNodes.forEach(c => { if (c.nodeType === 3) t += c.nodeValue; }); if (t.trim().length > 160) prose++; });
    if (prose) out.warnings.push('긴 문장 덩어리 ' + prose + '곳 (산문 대신 컴포넌트로)');
  }
  document.querySelectorAll('[data-qa-warn]').forEach(el => out.warnings.push(el.getAttribute('data-qa-warn')));
  out.text = document.body ? document.body.innerText : '';
  return out;
}
"""

_FONT_JS = r"""
(fams) => {
  const c = document.createElement('canvas').getContext('2d'); const txt = '한글 글꼴 확인 Wg 0123';
  const res = {};
  for (const f of fams) {
    let found = false;
    for (const base of ['monospace', 'serif']) {
      c.font = '40px ' + base; const w0 = c.measureText(txt).width;
      c.font = '40px "' + f + '", ' + base; const w1 = c.measureText(txt).width;
      if (Math.abs(w1 - w0) > 0.5) { found = true; break; }
    }
    res[f] = found;
  }
  return res;
}
"""

_DECOR = {"callout", "note", "chip"}
_DATE_HYPHEN = re.compile(r"(?<!\d)(?:19|20)\d{2}-\d{1,2}-\d{1,2}(?!\d)")
_EMDASH = "\u2014"


class RenderResult(list):
    """render_all 반환값. list 처럼 PNG 경로를 담고, QA 결과를 속성으로 가짐.
    .report(딕셔너리) .report_path .errors .warnings .ok"""
    report = None
    report_path = ""
    errors = 0
    warnings = 0
    ok = True


def _safe_stdout():
    """콘솔·파이프 인코딩이 cp949 등이어도 출력이 멈추지 않게 UTF-8 로 맞춤."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_safe_stdout()  # import 할 때 한 번 : spec.py 가 render_all 전에 출력해도 멈추지 않게


def _need_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return sync_playwright
    except ImportError:
        sys.stderr.write(
            "[image-deck] Playwright 가 없음. 아래 두 줄을 실행한 뒤 다시 시도함\n"
            "    python3 -m pip install playwright\n"
            "    python3 -m playwright install chromium\n")
        raise SystemExit(3)


def _font_families():
    fams = [f.strip().strip("'\"") for f in _THEME["font"].split(",")]
    return [f for f in fams if f and f.lower() not in ("sans-serif", "serif", "monospace", "system-ui")]


def _find_lexicon(lexicon):
    if lexicon in (None, False):
        return None
    if lexicon not in ("auto", True):
        return lexicon if os.path.isfile(lexicon) else None
    for c in (os.path.join(HERE, "lexicon.json"),
              os.path.join(HERE, "..", "..", "generate-full-report", "references", "lexicon.json"),
              os.path.join(HERE, "..", "..", "report-harness", "references", "lexicon.json")):
        if os.path.isfile(c):
            return os.path.normpath(c)
    return None


def _lexicon_hits(text, lex, mode):
    """lexicon.json 의 금지어 확인(경고만). 「」 안 인용은 hype_soft·eval_terms 검사에서 뺌."""
    hits = []
    unq = re.sub(r"「[^」]*」", "", text)
    groups = [("과장", "hype_hard", text), ("과장(약)", "hype_soft", unq),
              ("AI 티 문형", "ai_tone", text), ("가리킴", "pointer", text), ("자기 해설", "self_commentary", text),
              ("사용자 금지어", "user_banned", text)]
    if mode == "status":
        groups.append(("평가어(현황 모드)", "eval_terms", unq))
    for label, key, src in groups:
        entry = lex.get(key) or {}
        words = list(entry.get("kr", [])) + list(entry.get("en", []))
        found = sorted({w for w in words if w and w in src})
        if found:
            hits.append("%s : %s" % (label, ", ".join(found[:6])))
    return hits


def _dwidth(s):
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def _pad(s, w):
    s = str(s)
    return s + " " * max(0, w - _dwidth(s))


def _cut(s, w):
    s = str(s)
    out, cur = "", 0
    for ch in s:
        cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if cur + cw > w - 1:
            return out + "…"
        out += ch
        cur += cw
    return out


def render_all(htmls, out_dir, prefix="s", strict=False, palette=True, lexicon="auto", mode="analysis",
               timeout_ms=4000):
    """HTML 목록을 PNG 로 렌더하고 자동 QA 를 함.

    htmls   : 쪽 함수가 돌려준 HTML 문자열 목록(또는 .html 파일 경로)
    out_dir : {prefix}NN.html / .png 와 qa_report.json 을 쓰는 폴더. 같은 이름 규칙의 예전 파일은 지움
    strict  : True 면 오류가 있을 때 보고서를 쓴 뒤 종료코드 1 로 멈춤
    palette : 시작할 때 check_palette 결과를 출력
    lexicon : "auto"(형제 스킬의 lexicon.json 을 찾아 금지어 경고) | 경로 | None
    mode    : "analysis"(기본) | "status"(현황편 : 평가어도 경고)
    반환    : RenderResult(PNG 경로 list, .report .errors .warnings .ok .report_path)
    """
    _safe_stdout()
    sync_playwright = _need_playwright()
    os.makedirs(out_dir, exist_ok=True)
    pal = check_palette(verbose=palette)
    width = max(2, len(str(len(htmls))))
    stale = re.compile(r"^%s\d{2,}\.(png|html)$" % re.escape(prefix))
    for fn in os.listdir(out_dir):
        if stale.match(fn):
            try:
                os.remove(os.path.join(out_dir, fn))
            except OSError:
                pass
    lex_path = _find_lexicon(lexicon)
    lex = _read_json(lex_path) if lex_path else None
    if lexicon and not lex:
        print("[image-deck] 금지어 사전(lexicon.json)을 찾지 못해 금지어 검사를 건너뜀 "
              "(형제 스킬 generate-full-report 또는 report-harness 와 함께 설치하면 켜짐)")
    pages, paths = [], RenderResult()
    fonts = {}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # chromium 미설치, 시스템 라이브러리 부족 등
            sys.stderr.write("[image-deck] chromium 을 실행하지 못함 : %s\n"
                             "    python3 -m playwright install chromium\n"
                             "    (Linux 에서 라이브러리가 없다고 나오면 : python3 -m playwright install --with-deps chromium)\n"
                             % str(e).splitlines()[0])
            raise SystemExit(3)
        pg = browser.new_page(viewport={"width": SLIDE_W, "height": SLIDE_H}, device_scale_factor=1)
        for i, h in enumerate(htmls, 1):
            if isinstance(h, str) and h.lower().endswith(".html") and os.path.isfile(h):
                with open(h, encoding="utf-8") as f:
                    h = f.read()
            stem = "%s%0*d" % (prefix, width, i)
            hp = os.path.join(out_dir, stem + ".html")
            with open(hp, "w", encoding="utf-8") as f:
                f.write(h)
            pg.goto(Path(hp).resolve().as_uri(), wait_until="load")
            try:
                pg.wait_for_function("window.__deckReady === true", timeout=timeout_ms)
            except Exception:
                pg.evaluate("() => document.fonts ? document.fonts.ready : null")
            if i == 1:
                fonts = pg.evaluate(_FONT_JS, _font_families())
            r = pg.evaluate(_QA_JS)
            errs, warns = list(r["errors"]), list(r["warnings"])
            if r["kind"] in ("visual", "implication"):
                if "callout" in r["comps"]:
                    warns.append("%s 쪽에 ☞ 줄 : 이 쪽 양식에는 ☞ 결론 줄을 두지 않음" % r["kind"])
                if '<div class="source">' in h:
                    warns.append("%s 쪽에 Source 줄 : 이 쪽 양식에는 출처 줄을 두지 않음" % r["kind"])
            ph = sorted(set(_PLACEHOLDER_RE.findall(h)))
            if ph:
                errs.append("프로필 플레이스홀더 남음 : " + ", ".join("{%s}" % x for x in ph))
            text = r.get("text", "")
            if _EMDASH in text:
                warns.append("줄표(U+2014) 사용 : 콜론·쉼표·괄호로 바꿈")
            dh = _DATE_HYPHEN.findall(text)
            if dh:
                warns.append("하이픈 날짜 %s : 덱 날짜는 2026.10.12 형식" % ", ".join(sorted(set(dh))[:3]))
            if lex:
                warns += ["금지어 " + x for x in _lexicon_hits(text, lex, mode)]
            pp = os.path.join(out_dir, stem + ".png")
            pg.screenshot(path=pp, clip={"x": 0, "y": 0, "width": SLIDE_W, "height": SLIDE_H})
            paths.append(pp)
            comps = sorted(set(r["comps"]))
            pages.append({"index": i, "file": stem + ".png", "kind": r["kind"] or "?", "part": r["part"],
                          "components": comps, "headline_lines": r["hl"], "source_lines": r["src"],
                          "body_gap_px": r.get("gap"), "errors": errs, "warnings": warns,
                          "text": re.sub(r"\s+", " ", text).strip()[:1500]})
        browser.close()

    # 덱 전체 검사 (경고)
    deck_warn = []
    run = []
    for pgi in pages:
        core = set(pgi["components"]) - _DECOR
        if pgi["kind"] == "content" and core == {"mini_table"}:
            run.append(pgi["index"])
            if len(run) == 3:
                deck_warn.append("표만 있는 쪽 3장 연속 : %s쪽" % ", ".join(str(x) for x in run))
        else:
            run = []
    groups = {}
    for pgi in pages:
        if pgi["part"] and pgi["kind"] in ("content", "visual", "implication"):
            groups.setdefault(pgi["part"], []).append(pgi)
    for part, plist in groups.items():
        if sum(1 for x in plist if x["kind"] == "content") < 2:
            continue
        kinds = set()
        for x in plist:
            kinds |= set(x["components"]) - _DECOR
        if len(kinds) < 3:
            deck_warn.append("섹션 「%s」 컴포넌트 %d종(%s) : 3종 이상 권장" % (part, len(kinds), ", ".join(sorted(kinds)) or "없음"))
    content = [x for x in pages if x["kind"] == "content"]
    if content:
        with_call = sum(1 for x in content if "callout" in x["components"])
        if with_call * 2 < len(content):
            deck_warn.append("☞ 정리 줄이 있는 쪽 %d/%d : 본문 쪽 절반 이상 권장" % (with_call, len(content)))
    kr_fonts = [f for f, ok in fonts.items() if ok]
    if fonts and not kr_fonts:
        deck_warn.append("한글 글꼴을 찾지 못함 (%s) : Noto Sans CJK KR 등을 설치" % ", ".join(fonts))
    deck_err = ["팔레트 대비 미달 : %s %s / %s %.2f < %.1f" % (c["name"], c["fg"], c["bg"], c["ratio"], c["need"])
                for c in pal["contrast"] if not c["ok"]]

    n_err = sum(len(x["errors"]) for x in pages) + len(deck_err)
    n_warn = sum(len(x["warnings"]) for x in pages) + len(deck_warn)

    # 표 출력
    print("[image-deck QA] %d쪽 · 오류 %d · 경고 %d%s" % (len(pages), n_err, n_warn,
                                                   " · 글꼴 %s" % kr_fonts[0] if kr_fonts else ""))
    print("  %s %s %s %s %s %s" % (_pad("쪽", 4), _pad("파일", 9), _pad("종류", 12), _pad("섹션", 22),
                                    _pad("컴포넌트", 34), "판정"))
    for x in pages:
        state = "오류" if x["errors"] else ("경고" if x["warnings"] else "OK")
        print("  %s %s %s %s %s %s" % (_pad(x["index"], 4), _pad(x["file"], 9), _pad(x["kind"], 12),
                                        _pad(_cut(x["part"] or "-", 22), 22),
                                        _pad(_cut(", ".join(x["components"]) or "-", 34), 34), state))
        for e in x["errors"]:
            print("       ! %s" % e)
        for w in x["warnings"]:
            print("       ? %s" % w)
    for e in deck_err:
        print("  [덱] ! %s" % e)
    for w in deck_warn:
        print("  [덱] ? %s" % w)

    report = {
        "tool": "image-deck/deck_core.py", "version": __version__,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "out_dir": os.path.abspath(out_dir), "mode": mode,
        "lexicon": os.path.basename(lex_path) if lex_path else None,
        "fonts": fonts, "palette": pal, "pages": pages, "deck_errors": deck_err, "deck_warnings": deck_warn,
        "summary": {"pages": len(pages), "errors": n_err, "warnings": n_warn, "ok": n_err == 0},
    }
    rp = os.path.join(out_dir, "qa_report.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("  보고서 : %s" % rp)
    paths.report, paths.report_path = report, rp
    paths.errors, paths.warnings, paths.ok = n_err, n_warn, n_err == 0
    if strict and n_err:
        sys.stderr.write("[image-deck] QA 오류 %d건 (strict)\n" % n_err)
        raise SystemExit(1)
    return paths


# ---------------------------------------------------------------------------
# 9. 명령행 : 팔레트 검사와 프로필 확인
# ---------------------------------------------------------------------------
def _main(argv=None):
    import argparse
    _safe_stdout()
    ap = argparse.ArgumentParser(description="image-deck deck_core : 팔레트 검사, 프로필 확인")
    ap.add_argument("--palette", action="store_true", help="기본(또는 --theme JSON) 팔레트 검사 결과 출력")
    ap.add_argument("--theme", help="토큰을 덮어쓸 JSON 파일(make_theme 형식)")
    ap.add_argument("--which-profile", action="store_true", help="쓰게 될 profile.json 경로와 빈 값 확인")
    a = ap.parse_args(argv)
    if a.theme:
        with open(a.theme, encoding="utf-8") as f:
            make_theme(json.load(f))
    if a.which_profile:
        p = load_profile(quiet=True)
        print(p["_path"])
        print("  AUTHOR_KR=%s AUTHOR_EN=%s EMAIL=%s PHONE_KR=%s BRAND=%s"
              % (p["AUTHOR_KR"], p["AUTHOR_EN"], p["EMAIL"], p["PHONE_KR"] or "(생략)", p["BRAND"]))
    if a.palette or not a.which_profile:
        res = check_palette()
        return 1 if res["fail"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(_main())
