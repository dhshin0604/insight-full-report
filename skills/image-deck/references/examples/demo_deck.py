# -*- coding: utf-8 -*-
"""demo_deck.py : image-deck 데모(가상의 내용, 15쪽)

모든 컴포넌트와 쪽 종류를 한 번 이상 씀. 회사·도시·공급사 이름과 수치는 모두 가상의 예시임.

    python3 demo_deck.py --out <폴더>                     # 프로필은 PROFILE 등 정해진 순서로 찾음
    python3 demo_deck.py --out <폴더> --example-profile   # profile.json 의 _examples(가상 값)로 바로 시험
    python3 demo_deck.py --out <폴더> --samples <폴더>    # README 용 960x540 견본 4장도 저장

끝에 render_all(QA) -> bundle(PDF, PPTX, PNG zip)까지 함. QA 오류가 있으면 종료코드 1.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.dirname(HERE)
sys.path.insert(0, REF)

from deck_core import (  # noqa: E402
    agenda_html, callout, cards, chart_img, chip, cover_html, current_theme, fill, flow, hbars, implication_html,
    layers, load_profile, mini_table, note, panel_title, quadrant, render_all, set_profile, slide_html, stats,
    sublist_html, thanks_html, timeline, two_panel, visual_summary_html,
)
from bundle import bundle  # noqa: E402

DATE = "2026.10.12"
SRC = "가상의 A사 운영 자료(예시)"
AGENDA = [("1부", "현황 : 센터 3곳의 규모와 공급사"),
          ("2부", "비교 : 연혁, 위치, 구조, 흐름"),
          ("3부", "비주얼 요약 : 무엇이 바뀌는가"),
          ("4부", "시사점 : 통합 관제로 바뀔 때")]


def wait_chart_svg(path):
    """chart_img 시연용 SVG 막대 그림(단계별 1건당 평균 대기 시간, 가상). 글자는 22px 이상."""
    t = current_theme()
    data = [("입고", 4), ("보관", 2), ("피킹", 11), ("포장", 5), ("출고", 3)]
    W, H, left, base, top = 860, 340, 70, 286, 40
    bw, gap = 104, 54
    mx = 12.0
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="%s">'
             % (W, H, W, H, t["font"].replace('"', "'"))]
    for v in (0, 4, 8, 12):
        y = base - (base - top) * v / mx
        parts.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#E2E2E2" stroke-width="2"/>' % (left, y, W - 20, y))
        parts.append('<text x="%d" y="%.1f" font-size="22" fill="#555555" text-anchor="end">%d</text>' % (left - 12, y + 8, v))
    for i, (lab, v) in enumerate(data):
        x = left + 40 + i * (bw + gap)
        h = (base - top) * v / mx
        col = t["key"] if lab == "피킹" else "#B8B8B8"
        parts.append('<rect x="%d" y="%.1f" width="%d" height="%.1f" rx="4" fill="%s"/>' % (x, base - h, bw, h, col))
        parts.append('<text x="%d" y="%.1f" font-size="26" font-weight="700" fill="%s" text-anchor="middle">%d분</text>'
                     % (x + bw // 2, base - h - 12, t["key"] if lab == "피킹" else "#1A1A1A", v))
        parts.append('<text x="%d" y="%d" font-size="24" font-weight="700" fill="#1A1A1A" text-anchor="middle">%s</text>'
                     % (x + bw // 2, base + 36, lab))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#3A3A3A" stroke-width="3"/>' % (left, base, W - 20, base))
    parts.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    return path


def build_pages(asset_dir):
    pages = []
    S1, S2 = "1. 현황", "2. 비교"

    # 1 표지
    pages.append(cover_html(
        "가상의 A사<br>창고 자동화 전환",
        subtitle="예시 도시 B시 물류센터 3곳의 현황, 비교, 시사점",
        series="Image Deck 데모 · 가상 데이터",
        date=DATE,
        note="이 덱의 회사, 도시, 공급사 이름과 모든 수치는 기능 시연을 위한 가상의 예시임"))

    # 2 목차
    pages.append(agenda_html(AGENDA, active=None, no=2))

    # 3 현황 ① 규모 : stats + cards
    pages.append(slide_html(
        3, S1, "① 규모",
        "가상의 A사는 예시 도시 B시에 물류센터 3곳을 두고 하루 4만 2천 상자를 처리함. 자동화 설비 비중은 센터마다 "
        "18%에서 61%까지 벌어져 있어, 한 회사 안에서 세 가지 운영 방식이 함께 돌아가는 구조임.",
        fill(
            stats([("3곳", "물류센터", "모두 예시 도시 B시 안", "inside"),
                   ("4.2만", "하루 처리 상자", "3곳 합계, 평일 평균", "inside"),
                   ("18~61%", "자동화 설비 비중", "센터별 하한과 상한", "outside"),
                   ("미확인", "외부 위탁 물량", "이번 자료 범위에서 문서 미발견", "grey")]),
            cards([("북부센터 (2019년 개장)", ["하루 1만 3천 상자", "자동화 설비 비중 18%", "작업자 170명, 수작업 중심"], "outside"),
                   ("중앙센터 (2021년 개장)", ["하루 1만 9천 상자", "자동화 설비 비중 61%", "작업자 130명, 통합 관제 시범"], "inside"),
                   ("남부센터 (2022년 개장)", ["하루 1만 상자", "자동화 설비 비중 34%", "작업자 110명, 북부 방식 이식"], "outside")]),
            panel_title("세 센터가 같은 주문을 처리하는 방식")
            + flow([("주문 접수", "센터마다 다른 시스템 3개"), ("작업 배정", "북부와 남부는 관리자가 직접"),
                    ("설비 가동", "중앙만 관제 화면에서 조정"), ("출고 집계", "센터별로 하루 1회")], active=2))
        + callout("세 센터의 차이는 설비 대수보다 「사람과 설비가 일을 나누는 방식」에서 생김"),
        source=SRC))

    # 4 현황 ② 공급사 : mini_table + chip + note
    inside, outside, unknown = chip("B시 안", "red"), chip("B시 밖", "navy"), chip("미확인", "grey")
    ok, nd = "문서 확인", "문서 미발견"
    pages.append(slide_html(
        4, S1, "② 공급사",
        "A사 설비 공급사 7곳 가운데 B시 안에 있는 곳은 3곳, 밖은 3곳, 소재 미확인 1곳임. 유지보수 계약은 7곳 중 "
        "4곳만 문서로 확인되어, 설비 목록과 관리 범위가 서로 맞지 않는 상태임.",
        mini_table(["공급사(가상)", "공급 품목", "소재", "유지보수 계약", "첫 납품"],
                   [["공급사 가", "자동 분류기", inside, ok, "2021년"],
                    ["공급사 나", "이동형 로봇", outside, ok, "2024년"],
                    ["공급사 다", "컨베이어", inside, ok, "2019년"],
                    ["공급사 라", "창고 관리 소프트웨어", outside, nd, "2021년"],
                    ["공급사 마", "바코드 스캐너", inside, ok, "2022년"],
                    ["공급사 바", "포장 설비", outside, nd, "2022년"],
                    ["공급사 사", "랙과 선반", unknown, nd, "2019년"]],
                   widths=["18%", "27%", "17%", "20%", "18%"], em_rows=(3, 5, 6), row_height=62)
        + callout("유지보수 문서가 없는 3곳(라, 바, 사)이 통합 관제를 넓힐 때 먼저 확인할 대상임")
        + note("「미확인」「문서 미발견」은 이번 자료 범위에서 문서를 찾지 못했다는 뜻이며, 계약이 없다는 뜻이 아님"),
        source=SRC + ", 공급 계약 목록(가상)"))

    # 5 현황 ③ 처리량 : hbars 두 묶음
    pages.append(slide_html(
        5, S1, "③ 처리량",
        "센터별 하루 처리량은 중앙센터 1만 9천 상자, 북부 1만 3천, 남부 1만 상자 순임. 작업자 1인 기준으로 다시 보면 "
        "자동화 비중 61%인 중앙센터가 146상자로 북부센터(76상자)의 1.9배임.",
        fill(
            two_panel(
                panel_title("하루 처리량 (상자)")
                + hbars([("중앙센터", 19000), ("북부센터", 13000), ("남부센터", 10000)], bar_height=56, height=290),
                panel_title("작업자 1인 하루 처리량 (상자)")
                + hbars([("중앙센터", 146), ("업계 평균(가상)", 110, "navy"), ("남부센터", 91), ("북부센터", 76)],
                        bar_height=48, height=290),
                gap=72),
            stats([("1.9배", "1인 처리량 격차", "중앙 146상자 ÷ 북부 76상자", "inside"),
                   ("410명", "현장 작업자", "북부 170, 중앙 130, 남부 110", "outside"),
                   ("2곳", "업계 평균 아래", "남부 91상자, 북부 76상자", "grey")]))
        + callout("처리량 순서(중앙, 북부, 남부)와 1인 처리량 순서(중앙, 남부, 북부)가 달라, 북부센터는 규모에 비해 "
                  "사람 손이 많이 드는 구조임")
        + note("1인 하루 처리량 = 하루 처리량 ÷ 현장 작업자 수(소수점 아래 버림). 업계 평균은 비교를 위한 가상의 값"),
        source=SRC))

    # 6 간지 : 2부, 7 세부 목차
    pages.append(agenda_html(AGENDA, active=1, no=6))
    pages.append(sublist_html(["연혁 : 7년 동안의 전환점 6개", "위치 : 설비 비중과 데이터 연결의 2축",
                               "구조 : 현장, 설비, 데이터, 관제의 4계층", "흐름 : 출고까지 5단계와 대기 시간",
                               "한눈에 보기 : 연혁, 위치, 생산성"], "2부 세부 목차", no=7))

    # 8 비교 ① 연혁 : timeline (6개, 위아래 번갈아)
    pages.append(slide_html(
        8, S2, "① 연혁",
        "A사의 자동화는 2019년 북부센터 개장 뒤 7년 동안 6번의 전환점을 거침. 설비 투자는 중앙센터에 몰렸고, "
        "2025년 통합 관제 시범부터는 설비보다 운영 방식을 바꾸는 쪽으로 무게가 옮겨 가는 중임.",
        fill(
            timeline([("2019.03", "북부센터 개장", "수작업 중심, 컨베이어 2라인"),
                      ("2021.07", "중앙센터 개장", "자동 분류기 1대 도입"),
                      ("2022.11", "남부센터 개장", "북부센터 방식을 그대로 이식"),
                      ("2024.05", "중앙센터 2차 투자", "이동형 로봇 40대 추가"),
                      ("2025.09", "통합 관제 시범", "중앙센터 1곳에서 시작", True),
                      ("2026.10", "3곳 통합 검토", "관제 일원화 여부 결정 예정")],
                     phases=[(0, 3, "2019~2024 : 설비를 더한 시기 (센터 3곳 개장, 설비 투자 4번)", "outside"),
                             (4, 5, "2025~ : 흐름을 묶는 시기", "key")]),
            stats([("4번", "설비 투자 결정", "2019~2024, 센터 단위", "outside"),
                   ("2번", "운영 방식 결정", "2025~2026, 3곳 전체 단위", "key"),
                   ("61%", "중앙센터 자동화 비중", "3곳 중 상한, 북부는 18%", "inside")]))
        + callout("2024년까지는 「설비를 더하는」 결정, 2025년부터는 「흐름을 묶는」 결정이 이어짐"),
        source="가상의 A사 연혁 자료(예시)"))

    # 9 비교 ② 위치 : quadrant + cards
    pages.append(slide_html(
        9, S2, "② 위치",
        "자동화 설비 비중과 데이터 연결 수준 두 축에 놓으면 A사 3곳은 모두 「통합 운영」 칸 밖에 있음. 가상의 경쟁사 "
        "2곳 중 1곳은 이미 그 칸에 들어가 있어, 설비보다 연결이 다음 투자의 기준이 됨.",
        two_panel(
            quadrant("자동화 설비 비중", "데이터 연결 수준",
                     [("북부센터", 0.18, 0.22), ("남부센터", 0.34, 0.36), ("중앙센터", 0.61, 0.42),
                      ("가상 경쟁사 C", 0.80, 0.80, "navy"), ("가상 경쟁사 D", 0.74, 0.20, "navy"),
                      ("업계 평균(가상)", 0.47, 0.57, "grey", "l")],
                     ("연결 먼저", "통합 운영", "수작업 중심", "설비 먼저"), height=640),
            cards([("「통합 운영」 칸의 조건", ["자동화 설비 비중 50% 이상", "3곳 이상의 기록을 한 화면에서 봄",
                                          "작업 배분을 규칙으로 정함"], "key"),
                   ("A사 3곳의 위치", ["중앙센터 : 설비 조건은 넘었고 연결은 못 미침", "북부, 남부센터 : 두 축 모두 못 미침"], "inside"),
                   ("가상의 경쟁사 2곳", ["C : 두 축 모두 조건을 넘음", "D : 설비 74%, 연결은 북부센터 수준"], "navy")], cols=1)
            + callout("다음 투자의 기준은 설비 비중이 아니라 「데이터 연결 수준」임"),
            ratio="1.12fr 1fr", gap=36),
        source=SRC + ", 점 위치는 0~1 로 맞춘 가상의 값"))

    # 10 비교 ③ 구조 : layers
    pages.append(slide_html(
        10, S2, "③ 구조",
        "A사 물류센터의 운영 구조는 현장, 설비, 데이터, 관제의 4개 계층으로 나뉨. 아래 2개 계층은 3곳 모두 갖췄지만 "
        "데이터 계층이 센터마다 따로 있어, 관제 계층은 중앙센터 1곳에 머무는 구조임.",
        layers([("관제 계층", ["통합 관제 화면", "수요 예측", ("작업 배분 자동화", True)], "inside", "중앙센터 1곳만 시범 운영"),
                ("데이터 계층", ["재고 기록", "설비 상태 기록", "작업자 동선 기록"], "navy", "센터마다 따로 저장"),
                ("설비 계층", ["자동 분류기", "이동형 로봇 40대", "컨베이어", "포장 설비"], "navy", "공급사 7곳"),
                ("현장 계층", ["입고", "보관", "피킹", "포장", "출고"], "navy", "작업자 410명")], height=620)
        + callout("관제를 넓히는 일은 설비 추가가 아니라 「데이터 계층을 하나로 묶는」 일임"),
        source=SRC))

    # 11 비교 ④ 흐름 : flow + chart_img + mini_table
    svg = wait_chart_svg(os.path.join(asset_dir, "fig_wait.svg"))
    pages.append(slide_html(
        11, S2, "④ 흐름",
        "출고까지 5단계 가운데 대기 시간이 긴 단계는 피킹으로, 3곳 평균 1건당 11분이 걸림. 피킹 대기가 전체 대기 "
        "25분의 44%를 차지해, 설비를 늘리기보다 작업 배분 순서를 바꾸는 일이 먼저임.",
        flow([("입고", "트럭 하차와 검수"), ("보관", "랙 1만 2천 칸에 적치"), ("피킹", "주문별로 꺼내 모음"),
              ("포장", "상자 크기에 맞춰 포장"), ("출고", "하루 4회 마감")], active=2)
        + two_panel(
            chart_img(svg, height=400, caption="단계별 1건당 평균 대기 시간 (분, 3곳 평균, 가상)"),
            panel_title("센터별 피킹 대기")
            + mini_table(["센터", "피킹 대기(분)", "자동화 비중"],
                         [["북부센터", "14", "18%"], ["남부센터", "12", "34%"], ["중앙센터", "7", "61%"],
                          ["3곳 단순 평균", "11", "38%"]], num_cols=(1, 2), em_rows=(2,), row_height=58)
            + callout("중앙센터의 피킹 대기는 북부의 절반이라, 배분 규칙만 옮겨도 대기를 줄일 여지가 있음"),
            ratio="1fr 1fr", gap=48)
        + note("대기 시간 = 앞 단계를 마친 뒤 다음 단계가 시작될 때까지 걸린 시간(주문 1건 기준, 가상의 예시 값)"),
        source=SRC))

    # 12 비교 ⑤ 한눈에 : timeline + quadrant + hbars
    pages.append(slide_html(
        12, S2, "⑤ 한눈에 보기",
        "A사의 7년은 설비를 더한 시기와 흐름을 묶기 시작한 시기로 나뉨. 연혁, 위치, 생산성을 한 장에 놓으면 중앙센터만 "
        "앞서 있고 나머지 2곳은 같은 길을 2~3년 늦게 따라가는 구조임.",
        timeline([("2019.03", "북부센터 개장", "수작업 중심으로 시작"),
                  ("2021.07", "중앙센터 개장", "자동 분류기 1대 도입"),
                  ("2024.05", "로봇 40대 추가", "중앙센터 2차 투자"),
                  ("2025.09", "통합 관제 시범", "중앙센터 1곳에서 시작", True)])
        + two_panel(
            quadrant("설비 비중", "데이터 연결",
                     [("북부", 0.18, 0.22), ("남부", 0.34, 0.36), ("중앙", 0.61, 0.42),
                      ("경쟁사 C(가상)", 0.80, 0.80, "navy")],
                     ("연결 먼저", "통합 운영", "수작업 중심", "설비 먼저"), height=490),
            panel_title("작업자 1인 하루 처리량 (상자)")
            + hbars([("중앙센터", 146), ("업계 평균(가상)", 110, "navy"), ("남부센터", 91), ("북부센터", 76)],
                    bar_height=50, height=340)
            + callout("투자 시점, 위치, 생산성 세 가지가 모두 「중앙센터 방식의 확산」을 가리킴"),
            ratio="1fr 1fr", gap=56),
        source=SRC))

    # 13 비주얼 요약
    pages.append(visual_summary_html(
        13, "자동화의 기준 : 「설비 대수」에서 「흐름 관리」로",
        asis={"tag": "As-Is", "title": "센터마다 따로 도는 설비", "mode": "flow",
              "items": [("주문 접수", "센터별 시스템 3개"), ("작업자 배정", "관리자가 경험으로 배정"),
                        ("설비 가동", "설비마다 따로 제어"), ("출고 집계", "센터 단위로 하루 1회")],
              "desc": ["센터 3곳이 각자 시스템과 기록을 가짐", "작업 배분은 관리자의 경험에 기댐",
                       "설비를 늘려도 피킹 대기 11분은 그대로 남음"]},
        tobe={"tag": "To-Be", "title": "하나의 관제로 묶인 흐름", "mode": "hub",
              "center": ("통합 관제", "작업 배분 자동화"),
              "items": ["북부센터", "중앙센터", "남부센터", ("수요 예측", "aux"), ("설비 상태", "aux"), "작업자 동선"],
              "desc": ["3곳의 기록을 한곳에 모아 배분을 자동화", "수요 예측과 설비 상태가 배분 순서를 정함",
                       "설비는 그대로 두고 대기 시간부터 줄임"]},
        verdict=("설비 대수", "<", "흐름 관리"),
        conclusion="다음 투자의 첫 순서는 설비 추가가 아니라 세 센터의 흐름을 하나로 묶는 관제입니다",
        sub="3. 비주얼 요약"))

    # 14 시사점 3축 표
    pages.append(implication_html(
        14, "4. 통합 관제 시사점",
        "통합 관제는 설비를 늘리는 투자와 다르게 센터 사이의 흐름을 바꾸는 일임. 기록이 한곳에 모이고 배분이 "
        "자동으로 바뀌면서, 관리의 기준이 「센터별 처리량」에서 「전체 대기 시간」으로 옮겨 갈 것임.",
        [("일을 나누는 주체",
          ("관리자의 경험 → 관제 규칙", ["주문이 들어오면 규칙이 작업자와 설비를 함께 배정",
                                    ("관리자는 예외 처리와 규칙 조정을 맡음", 2)]),
          ("배분 기준을 「문서」로 남기는 일이 먼저", ["센터마다 다른 수기 배정 기준을 하나로 맞춤",
                                          ("규칙을 바꾼 이력과 이유를 함께 기록", 2)])),
         ("일의 형태",
          ("센터 단위 작업 → 3곳을 오가는 작업", ["가까운 센터보다 대기가 짧은 센터로 주문이 감",
                                         ("센터 사이 이동 물량이 새로 생김", 2)]),
          ("하루 1회 집계 → 15분 단위 공유", ["3곳의 재고와 설비 상태를 같은 기준으로 기록",
                                       ("유지보수 문서가 없는 공급사 3곳부터 정리", 2)])),
         ("관리",
          ("센터별 처리량 → 전체 대기 시간", ["주문 1건이 출고까지 기다린 시간을 봄",
                                       ("피킹 대기 11분이 첫 번째 관리 대상", 2)]),
          ("센터별 목표 → 하나의 공동 목표", ["성과 지표를 「전체 대기 시간」 하나로 묶음",
                                        ("센터장 평가 기준도 같은 지표로 맞춤", 2)]))],
        sub="① 개요", topic="통합 관제"))

    # 15 감사
    pages.append(thanks_html(no=15))
    return pages


def save_samples(png_paths, sample_dir, picks=(1, 13, 14, 12), size=(960, 540), max_kb=300):
    """README 견본 : 표지, 비주얼 요약, 시사점, 가로 막대·타임라인·사분면 쪽을 960x540 으로 줄여
    deck-sample-1.png ~ deck-sample-4.png 로 저장."""
    from PIL import Image
    os.makedirs(sample_dir, exist_ok=True)
    out = []
    for n, page in enumerate(picks, 1):
        src = png_paths[page - 1]
        dst = os.path.join(sample_dir, "deck-sample-%d.png" % n)
        with Image.open(src) as im:
            small = im.convert("RGB").resize(size, Image.LANCZOS)
        small.save(dst, optimize=True)
        if os.path.getsize(dst) > max_kb * 1024:
            small.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE).save(dst, optimize=True)
        out.append((dst, os.path.getsize(dst)))
        print("  견본 %d : %d쪽 -> %s (%.0f KB)" % (n, page, dst, os.path.getsize(dst) / 1024.0))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="image-deck 데모 덱(가상의 내용)")
    ap.add_argument("--out", required=True, help="PNG·HTML·qa_report.json·PDF·PPTX·zip 을 쓸 폴더")
    ap.add_argument("--example-profile", action="store_true",
                    help="references/profile.json 의 _examples(가상 값)를 프로필로 씀")
    ap.add_argument("--samples", default=None, help="README 견본 4장(960x540)을 저장할 폴더")
    ap.add_argument("--name", default="image_deck_demo", help="묶음 기본 이름")
    a = ap.parse_args(argv)

    if a.example_profile:
        with open(os.path.join(REF, "profile.json"), encoding="utf-8") as f:
            set_profile(json.load(f)["_examples"])
        print("[demo] 가상의 예시 프로필을 씀")
    else:
        load_profile()

    out = os.path.abspath(a.out)
    asset_dir = os.path.join(out, "assets")
    os.makedirs(asset_dir, exist_ok=True)
    pages = build_pages(asset_dir)
    paths = render_all(pages, out)
    if not paths.ok:
        print("[demo] QA 오류 %d건 : PNG 를 확인하고 고친 뒤 다시 실행" % paths.errors)
        return 1
    bundle(paths, a.name, out, formats=("pdf", "pptx", "zip"),
           alt_texts=[p.get("text", "") for p in paths.report["pages"]] if paths.report else None)
    if a.samples:
        save_samples(paths, a.samples)
    return 0


if __name__ == "__main__":
    sys.exit(main())
