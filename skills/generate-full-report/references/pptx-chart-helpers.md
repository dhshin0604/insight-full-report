# PPTX 시각화 헬퍼 함수 (Chart Helpers)

시각화 데이터가 있는 슬라이드에 사용하는 Python 함수 모음.
`rr()`, `pp()`, `pp_bullet()`, `pp_empty()` 헬퍼는 `pptx-build-pipeline.md` 참조.

---

## 1. 표(Table) — `make_table()`

비교/현황 데이터를 표로 표시. `<p:graphicFrame>` 요소 반환.

```python
def tbl_border(color='C8D0DC'):
    return (f'<a:lnL w="9525"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:lnL>'
            f'<a:lnR w="9525"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:lnR>'
            f'<a:lnT w="9525"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:lnT>'
            f'<a:lnB w="9525"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:lnB>')

def tbl_cell(text, fill=None, text_color='333333', sz=920, bold=False, lang='ko', algn='l'):
    fill_xml = (f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>')
    col_xml  = f'<a:solidFill><a:srgbClr val="{text_color}"/></a:solidFill>'
    b_a      = ' b="1"' if bold else ''
    return (f'<a:tc>'
            f'<a:txBody>'
            f'<a:bodyPr bIns="60960" lIns="91440" rIns="91440" tIns="60960"/>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr algn="{algn}"><a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/></a:pPr>'
            f'<a:r><a:rPr lang="{lang}" sz="{sz}"{b_a} dirty="0">{col_xml}</a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r></a:p>'
            f'</a:txBody>'
            f'<a:tcPr>{tbl_border()}{fill_xml}</a:tcPr>'
            f'</a:tc>')

def make_table(headers, rows, x, y, cx, cy, col_widths=None, lang='ko',
               hdr_color='1A3A6B', hdr_text='FFFFFF',
               row_fill_odd='F0F4FA', row_fill_even='FFFFFF'):
    """
    headers   : 컬럼 헤더 리스트
    rows      : 데이터 행 리스트 (각 행은 헤더와 동일 길이 리스트)
    x, y      : EMU 좌표
    cx, cy    : EMU 크기
    col_widths: 각 컬럼 너비 (합이 cx와 같아야 함, None이면 균등 분배)
    lang      : 'ko' 또는 'en-US'
    """
    n = len(headers)
    if col_widths is None:
        col_widths = [cx // n] * n
        col_widths[-1] = cx - sum(col_widths[:-1])

    grid = ''.join(f'<a:gridCol w="{w}"/>' for w in col_widths)

    n_rows = len(rows)
    body_h = cy - 380000
    row_h  = max(280000, body_h // max(n_rows, 1))
    hdr_h  = 380000

    hdr_cells = ''.join(tbl_cell(h, fill=hdr_color, text_color=hdr_text, sz=1000,
                                  bold=True, lang=lang) for h in headers)
    hdr_row = f'<a:tr h="{hdr_h}">{hdr_cells}</a:tr>'

    data_rows_xml = ''
    for i, row in enumerate(rows):
        fill = row_fill_odd if i % 2 == 0 else row_fill_even
        cells = ''.join(tbl_cell(cell, fill=fill, sz=920, lang=lang) for cell in row)
        data_rows_xml += f'<a:tr h="{row_h}">{cells}</a:tr>'

    return (f'<p:graphicFrame>'
            f'<p:nvGraphicFramePr>'
            f'<p:cNvPr id="30" name="table_chart"/>'
            f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>'
            f'<p:nvPr/>'
            f'</p:nvGraphicFramePr>'
            f'<p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
            f'<a:graphic>'
            f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            f'<a:tbl>'
            f'<a:tblPr firstRow="1" bandRow="1"/>'
            f'<a:tblGrid>{grid}</a:tblGrid>'
            f'{hdr_row}{data_rows_xml}'
            f'</a:tbl>'
            f'</a:graphicData>'
            f'</a:graphic>'
            f'</p:graphicFrame>')
```

### 사용 예시
```python
make_table(
    headers=['시뮬레이터', '개발사', '핵심 특성', '최적 사용 분야'],
    rows=[
        ['Habitat 3.0', 'Meta AI', '포토리얼 렌더링', '실내 Navigation'],
        ['CARLA',       'CVC',     'LiDAR 에뮬레이션', '자율주행'],
        ['Isaac Lab',   'NVIDIA',  'GPU 가속',         'Sim-to-Real'],
    ],
    x=162800, y=1790000, cx=8818500, cy=2860000,
    col_widths=[1700000, 1400000, 3060000, 2658500],
    lang='ko',
)
```

---

## 2. 수평 막대차트 — `make_hbars()`

수치 비교를 수평 막대로 표시. 배경 트랙 + 전경 바 + 레이블로 구성.

```python
def make_hbars(bars, x, y, cx, title='', title_color='1A3A6B', lang='ko'):
    """
    bars = [(label, value_pct, bar_color, note_str), ...]
    value_pct : 0~100 사이의 퍼센트 값
    note_str  : 바 오른쪽에 표시할 추가 메모 (없으면 '')
    """
    label_w    = int(cx * 0.40)   # 40% = 레이블 영역
    bar_area_x = x + label_w + 60000
    bar_max_w  = int(cx * 0.42)   # 42% = 최대 바 너비
    val_x      = bar_area_x + bar_max_w + 60000

    bar_h  = 230000
    gap    = 130000
    title_h = 300000 if title else 0
    top_y  = y + title_h

    shapes = []
    id_base = 40

    if title:
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base}" name="bar_title"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/>'
            f'<a:ext cx="{cx}" cy="{title_h - 60000}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr algn="l"><a:buNone/></a:pPr>'
            f'{rr(title, sz=1300, bold=True, color=title_color, lang=lang)}'
            f'<a:endParaRPr/></a:p>'
            f'</p:txBody></p:sp>'
        )

    for i, (label, value, bar_color, note) in enumerate(bars):
        bar_y  = top_y + i * (bar_h + gap)
        bar_w  = max(60000, int(bar_max_w * value / 100))
        note_str = f'  {note}' if note else ''

        # 배경 트랙
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+i*4+1}" name="bar_bg_{i}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{bar_area_x}" y="{bar_y + bar_h//3}"/>'
            f'<a:ext cx="{bar_max_w}" cy="{bar_h//3}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="E8EDF3"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
        )
        # 전경 바
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+i*4+2}" name="bar_{i}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{bar_area_x}" y="{bar_y + bar_h//3}"/>'
            f'<a:ext cx="{bar_w}" cy="{bar_h//3}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{bar_color}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
        )
        # 레이블 (왼쪽)
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+i*4+3}" name="bar_label_{i}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{bar_y}"/>'
            f'<a:ext cx="{label_w}" cy="{bar_h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="60960" tIns="0" wrap="square"/>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr algn="r"><a:buNone/></a:pPr>'
            f'{rr(label, sz=950, lang=lang)}'
            f'<a:endParaRPr/></a:p>'
            f'</p:txBody></p:sp>'
        )
        # 값 + 노트 (오른쪽)
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+i*4+4}" name="bar_val_{i}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{val_x}" y="{bar_y}"/>'
            f'<a:ext cx="{cx - (val_x - x)}" cy="{bar_h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="45720" rIns="0" tIns="0" wrap="square"/>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr algn="l"><a:buNone/></a:pPr>'
            f'{rr(f"{value}%", sz=1000, bold=True, color=bar_color, lang=lang)}'
            f'{rr(note_str, sz=850, color="666666", lang=lang) if note_str else ""}'
            f'<a:endParaRPr/></a:p>'
            f'</p:txBody></p:sp>'
        )

    return '\n'.join(shapes)
```

### 사용 예시
```python
make_hbars(
    bars=[
        ('Sim-to-Real 성공률', 78, '1A5276', 'Isaac Lab 기반'),
        ('Behavior Cloning', 52, 'AEB6BF', '전통적 방식'),
        ('Domain Randomization', 65, '2E86AB', '증강 데이터'),
    ],
    x=162800, y=1790000, cx=8818500,
    title='전략별 성공률 비교',
    lang='ko',
)
```

---

## 3. 그룹 막대차트 — `make_grouped_bars()`

두 시리즈를 나란히 비교하는 그룹 막대. 범례 자동 생성.

```python
def make_grouped_bars(groups, x, y, cx, title='', lang='ko',
                      color_a='1A5276', color_b='AEB6BF',
                      label_a='', label_b=''):
    """
    groups    : [(row_label, val_a, val_b), ...]
    color_a   : 시리즈 A 색상 (기본 네이비)
    color_b   : 시리즈 B 색상 (기본 회색)
    label_a/b : 범례 레이블
    """
    label_w    = int(cx * 0.30)
    bar_area_x = x + label_w + 50000
    bar_max_w  = int(cx * 0.50)
    val_x      = bar_area_x + bar_max_w + 50000

    bar_h   = 160000
    gap_in  = 40000
    gap_out = 150000
    grp_h   = 2 * bar_h + gap_in
    title_h = 300000 if title else 0
    top_y   = y + title_h

    shapes  = []
    id_base = 60

    # 제목
    if title:
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base}" name="grp_title"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/>'
            f'<a:ext cx="{cx}" cy="{title_h - 60000}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr algn="l"><a:buNone/></a:pPr>'
            f'{rr(title, sz=1300, bold=True, color="1A3A6B", lang=lang)}'
            f'<a:endParaRPr/></a:p>'
            f'</p:txBody></p:sp>'
        )

    # 범례 (Legend)
    leg_y = top_y - 50000
    for li, (lc, lt, lx_off) in enumerate([
        (color_a, label_a, 0),
        (color_b, label_b, 1200000),
    ]):
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+1+li*2}" name="leg_{li}_box"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{bar_area_x + lx_off}" y="{leg_y}"/>'
            f'<a:ext cx="220000" cy="150000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{lc}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
        )
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+2+li*2}" name="leg_{li}_txt"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{bar_area_x + lx_off + 240000}" y="{leg_y - 20000}"/>'
            f'<a:ext cx="900000" cy="200000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="45720" rIns="0" tIns="0" wrap="square"/>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr algn="l"><a:buNone/></a:pPr>'
            f'{rr(lt, sz=850, color=lc, bold=True, lang=lang)}'
            f'<a:endParaRPr/></a:p>'
            f'</p:txBody></p:sp>'
        )

    # 데이터 바
    for i, (label, val_a, val_b) in enumerate(groups):
        gy = top_y + i * (grp_h + gap_out)

        for j, (val, color) in enumerate([(val_a, color_a), (val_b, color_b)]):
            by = gy + j * (bar_h + gap_in)
            bw = max(30000, int(bar_max_w * val / 100))
            shapes.append(
                f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+10+i*10+j*2}" name="g{i}b{j}"/>'
                f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr><a:xfrm><a:off x="{bar_area_x}" y="{by}"/>'
                f'<a:ext cx="{bw}" cy="{bar_h}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
                f'<a:ln><a:noFill/></a:ln></p:spPr>'
                f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
            )
            shapes.append(
                f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+10+i*10+j*2+1}" name="g{i}v{j}"/>'
                f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr><a:xfrm><a:off x="{bar_area_x + bw + 40000}" y="{by}"/>'
                f'<a:ext cx="500000" cy="{bar_h}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
                f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="45720" rIns="0" tIns="0" wrap="square"/>'
                f'<a:lstStyle/>'
                f'<a:p><a:pPr algn="l"><a:buNone/></a:pPr>'
                f'{rr(f"{val}%", sz=900, bold=True, color=color, lang=lang)}'
                f'<a:endParaRPr/></a:p>'
                f'</p:txBody></p:sp>'
            )

        # 행 레이블
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{id_base+10+i*10+9}" name="g{i}_label"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{gy}"/>'
            f'<a:ext cx="{label_w}" cy="{grp_h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="60960" tIns="0" wrap="square"/>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr algn="r"><a:buNone/></a:pPr>'
            f'{rr(label, sz=950, lang=lang)}'
            f'<a:endParaRPr/></a:p>'
            f'</p:txBody></p:sp>'
        )

    return '\n'.join(shapes)
```

### 사용 예시
```python
make_grouped_bars(
    groups=[
        ('Push-T',     95.7, 73.4),
        ('Robomimic',  96.4, 91.8),
        ('Cloth Fold', 78.0, 41.0),
    ],
    x=4680000, y=1790000, cx=4300000,
    title='성능 벤치마크 비교',
    lang='ko',
    color_a='1A5276', color_b='AEB6BF',
    label_a='Diffusion Policy', label_b='Behavior Cloning',
)
```

---

## 시각화 판단 기준

| 데이터 유형 | 함수 |
|-------------|------|
| 4~6개 항목 비교 (속성 여러 개) | `make_table()` |
| 단일 지표 순위/크기 비교 (5~8개) | `make_hbars()` |
| 두 방법론/접근법 성능 비교 | `make_grouped_bars()` |
| 서술적 설명 위주 | `zone_body()` 또는 `zone_body2col()` |

---

## Zone 4 좌표 상수 (참고용)

```python
Z4_TOP  = 1790000   # Zone 4 시작 Y
Z4_H    = 2860000   # Zone 4 높이
Z4_X_L  = 162800    # 좌 시작 X (단일 또는 2단 좌)
Z4_X_R  = 4680000   # 2단 우 시작 X
Z4_CX   = 4300000   # 2단 각 열 너비
Z4_FULL = 8818500   # 단일 전체 너비
```
