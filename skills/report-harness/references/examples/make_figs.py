#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_figs.py : 예시 원고용 그림 3장을 다시 그림 (시험용 가상 데이터)

사용 : python3 make_figs.py [--out figs]
  figs/cover.png, figs/fig_timeband.png, figs/fig_repairs.png 를 만듦(이미 들어 있는 파일을 덮어씀).
  저장소에 렌더된 PNG 가 함께 들어 있으므로 예시를 돌릴 때 이 스크립트를 꼭 실행할 필요는 없음.

그림 규격은 briefs/BRIEF_FIG.md 를 따름 : HTML → PNG(Playwright chromium), 폭 2000px, 흰 바탕,
그림 안에 제목과 출처 줄 없음(Word 캡션이 대신함), 숫자는 원고 값 그대로, 세로 ≤ 가로 × 0.75.
준비 : pip install playwright && python3 -m playwright install chromium
"""
import argparse
import html
import os
import sys

FONT = "'Noto Sans CJK KR','Noto Sans KR','NanumGothic','Malgun Gothic','Apple SD Gothic Neo',sans-serif"
RED, NAVY, GREY, LIGHT, INK = "#A31D1D", "#1A3A6B", "#8A8A8A", "#BDBDBD", "#1A1A1A"
esc = lambda s: html.escape(str(s), quote=False)


def page(body, w, h):
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'><style>"
            "*{box-sizing:border-box;margin:0;padding:0}"
            "body{width:%dpx;height:%dpx;background:#fff;font-family:%s;color:%s}"
            "</style></head><body>%s</body></html>" % (w, h, FONT, INK, body))


def hbars(rows, w, h, unit_fmt):
    """rows = [(라벨, 값, 표시 문자열, 색)] : 가로 막대. 라벨 열 + 막대 + 값 라벨."""
    vmax = max(v for _, v, _, _ in rows)
    row_h = int((h - 120) / len(rows))
    out = []
    for label, v, shown, color in rows:
        pct = 100.0 * v / vmax
        out.append(
            "<div style='display:flex;align-items:center;height:%dpx'>"
            "<div style='width:560px;font-size:46px;font-weight:700;text-align:right;padding-right:36px'>%s</div>"
            "<div style='flex:1;display:flex;align-items:center'>"
            "<div style='height:%dpx;width:%.1f%%;background:%s;border-radius:6px'></div>"
            "<div style='font-size:48px;font-weight:800;color:%s;padding-left:24px;white-space:nowrap'>%s</div>"
            "</div></div>" % (row_h, esc(label), int(row_h * 0.56), pct * 0.74, color, color, esc(unit_fmt(shown))))
    return "<div style='padding:60px 80px 60px 40px'>%s</div>" % "".join(out)


def cover(w, h):
    cards = [
        ("이용 규모", "1,284,300건", "2025년 대여", "16.5% 증가", RED),
        ("시간대", "45.2%", "출퇴근 두 시간대", "주말 31.6%", RED),
        ("정류소와 운영", "412곳", "자전거 3,150대", "도심 대여 44.6%", NAVY),
        ("고장과 정비", "9,860건", "고장 신고", "중복 제외 건수 미기재", GREY),
    ]
    cells = []
    for i, (t, big, sub, foot, color) in enumerate(cards):
        if i:
            cells.append("<div style='width:70px;display:flex;align-items:center;justify-content:center;"
                         "font-size:64px;color:#3A3A3A'>&#8594;</div>")
        cells.append(
            "<div style='flex:1;min-width:0;border:4px solid #3A3A3A;border-radius:12px;padding:36px 20px;text-align:center'>"
            "<div style='font-size:46px;font-weight:700;color:%s;margin-bottom:26px'>%s</div>"
            "<div style='font-size:60px;font-weight:900;color:%s;line-height:1.1;white-space:nowrap'>%s</div>"
            "<div style='font-size:42px;font-weight:700;margin-top:18px'>%s</div>"
            "<div style='font-size:38px;color:#555;margin-top:26px;border-top:2px dashed #BDBDBD;padding-top:22px'>%s</div>"
            "</div>" % (color, esc(t), color, esc(big), esc(sub), esc(foot)))
    legend = ("<div style='display:flex;gap:56px;justify-content:center;font-size:38px;color:#444;margin-top:56px'>"
              "<span><b style='color:%s'>&#9632;</b> 늘어난 것, 몰린 것</span>"
              "<span><b style='color:%s'>&#9632;</b> 배치와 운영</span>"
              "<span><b style='color:%s'>&#9632;</b> 아직 확인되지 않은 것</span></div>" % (RED, NAVY, GREY))
    return ("<div style='height:%dpx;padding:0 60px;display:flex;flex-direction:column;justify-content:center'>"
            "<div style='display:flex;align-items:stretch'>%s</div>%s</div>" % (h, "".join(cells), legend))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs"))
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright 가 없음 : pip install playwright && python3 -m playwright install chromium")
    os.makedirs(a.out, exist_ok=True)
    figs = {
        "cover.png": (2000, 860, cover(2000, 860)),
        "fig_timeband.png": (2000, 1200, hbars([
            ("새벽 (7시 이전)", 3.9, "3.9", GREY),
            ("출근 (7시부터 9시)", 23.8, "23.8", RED),
            ("낮 (9시부터 17시)", 30.6, "30.6", NAVY),
            ("퇴근 (17시부터 19시)", 21.4, "21.4", RED),
            ("저녁 (19시 이후)", 20.3, "20.3", NAVY),
        ], 2000, 1200, lambda s: s + "%")),
        "fig_repairs.png": (2000, 1150, hbars([
            ("타이어", 3421, "3,421건 (34.7%)", RED),
            ("체인", 2179, "2,179건 (22.1%)", NAVY),
            ("잠금장치", 1864, "1,864건 (18.9%)", NAVY),
            ("단말기", 1282, "1,282건 (13.0%)", NAVY),
            ("기타", 1114, "1,114건 (11.3%)", GREY),
        ], 2000, 1150, lambda s: s)),
    }
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, (w, h, body) in figs.items():
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg.set_content(page(body, w, h))
            pg.wait_for_timeout(200)
            path = os.path.join(a.out, name)
            pg.screenshot(path=path, full_page=False)
            pg.close()
            print("  %s (%dx%d)" % (path, w, h))
        b.close()


if __name__ == "__main__":
    main()
