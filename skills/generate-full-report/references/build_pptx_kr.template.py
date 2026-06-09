#!/usr/bin/env python3
"""Build Korean PPTX slides — canonical 신동형 인사이트 정본 템플릿.

이 파일은 build_pptx.sh 오케스트레이터에서 호출된다. unpack/pack/strip 등은
오케스트레이터가 처리하므로, 이 스크립트는 슬라이드 XML 파일만 작성한다.

환경변수 TARGET_UNPACKED 가 unpack된 디렉터리(예: 'unpacked_kr') 를 가리킨다.
오케스트레이터를 사용하지 않을 때는 TARGET_UNPACKED=unpacked_kr python3 build_pptx_kr.py 로 실행.
"""
import os

TARGET = os.environ.get('TARGET_UNPACKED', 'unpacked_kr')
SLIDES = f'{TARGET}/ppt/slides'

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" '
      'xmlns:p15="http://schemas.microsoft.com/office/powerpoint/2012/main"')

LANG = 'ko'

def esc(t): return str(t).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def rr(text, sz=None, bold=False, color=None, lang='ko', u='none'):
    # u='none' 기본값: slideLayout5의 defRPr u="sng" 상속 차단
    sz_a  = f' sz="{sz}"' if sz else ''
    b_a   = ' b="1"' if bold else ''
    u_a   = f' u="{u}"' if u else ''
    col   = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if color else ''
    return f'<a:r><a:rPr lang="{lang}"{sz_a}{b_a}{u_a} dirty="0">{col}</a:rPr><a:t>{esc(text)}</a:t></a:r>'

def pp(*runs, algn='l', spc_bef=80, spc_aft=80):
    return (f'<a:p><a:pPr algn="{algn}"><a:spcBef><a:spcPts val="{spc_bef}"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="{spc_aft}"/></a:spcAft><a:buNone/></a:pPr>'
            f'{"".join(runs)}<a:endParaRPr/></a:p>')

def pp_b(*runs, spc=70):
    return (f'<a:p><a:pPr marL="200000" indent="-200000"><a:spcBef><a:spcPts val="{spc}"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="{spc}"/></a:spcAft><a:buChar char="▸"/></a:pPr>'
            f'{"".join(runs)}<a:endParaRPr/></a:p>')

def pp_e():
    return '<a:p><a:pPr><a:spcBef><a:spcPts val="100"/></a:spcBef><a:spcAft><a:spcPts val="0"/></a:spcAft><a:buNone/></a:pPr><a:endParaRPr/></a:p>'

def sld(spTree):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<p:sld {NS}>
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
{spTree}
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''

# Zone helpers
# ⚠️ NO <p:ph> elements in any zone — they cause slide layout inheritance that overrides custom positions
def z1(left, right):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="10" name="z1L"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="264100"/><a:ext cx="5100900" cy="220800"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchorCtr="0" anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/><a:lstStyle/>
        <a:p><a:pPr algn="l"><a:buNone/></a:pPr>{rr(left,sz=1800,bold=True,color='1A3A6B')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="z1R"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="4039250" y="264100"/><a:ext cx="4941900" cy="220800"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchorCtr="0" anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/><a:lstStyle/>
        <a:p><a:pPr algn="r"><a:buNone/></a:pPr>{rr(right,sz=1700,color='1A3A6B')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>'''

def z2(msg):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="z2"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162725" y="641800"/><a:ext cx="8818500" cy="669300"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchorCtr="0" anchor="t" bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        <a:p><a:pPr algn="l"><a:buNone/></a:pPr>{rr(msg,sz=1500)}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>'''

def z3(heading):
    # Zone 3: 소제목 — 중앙정렬 + 밑줄 (사용자 피드백 반영)
    # algn="ctr" 중앙배치, u='sng' 밑줄 명시 (rr() 기본값 u='none' 오버라이드)
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="13" name="z3"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="1455150"/><a:ext cx="8818500" cy="343500"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>{rr(heading,sz=1600,bold=True,color='1A3A6B',u='sng')}<a:endParaRPr u="none"/></a:p>
      </p:txBody></p:sp>'''

def z4(body_xml, top=1850000, height=2780000):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="14" name="z4"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="{top}"/><a:ext cx="8818500" cy="{height}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        {body_xml}
      </p:txBody></p:sp>'''

def z4_2col(left_xml, right_xml, top=1850000):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="14" name="z4L"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="{top}"/><a:ext cx="4300000" cy="2860000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        {left_xml}
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="15" name="z4R"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="4680000" y="{top}"/><a:ext cx="4300000" cy="2860000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        {right_xml}
      </p:txBody></p:sp>'''

def z5(src):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="99" name="z5"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="104375" y="4715475"/><a:ext cx="8938800" cy="130000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/><a:lstStyle/>
        <a:p><a:pPr><a:buNone/></a:pPr>{rr('※ Source : ' + src, sz=800, color='888888')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>'''

SRC = 'CAICT 具身智能发展报告（2025年）, 中国信息通信研究院·清华大学, Jan 2026'

def make_table(headers, rows, x, y, cx, cy, col_widths=None):
    n = len(headers)
    if col_widths is None:
        cw = cx // n
        col_widths = [cw] * (n - 1) + [cx - cw * (n - 1)]
    grid = ''.join(f'<a:gridCol w="{w}"/>' for w in col_widths)
    n_rows = len(rows)
    row_h = max(280000, (cy - 380000) // max(n_rows, 1))
    def cell(text, fill, tcol='333333', bold=False, sz=880):
        b = ' b="1"' if bold else ''
        return (f'<a:tc><a:txBody><a:bodyPr bIns="50000" lIns="91440" rIns="91440" tIns="50000"/><a:lstStyle/>'
                f'<a:p><a:pPr algn="l"><a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/></a:pPr>'
                f'<a:r><a:rPr lang="ko" sz="{sz}"{b} dirty="0"><a:solidFill><a:srgbClr val="{tcol}"/></a:solidFill></a:rPr>'
                f'<a:t>{esc(text)}</a:t></a:r></a:p></a:txBody>'
                f'<a:tcPr><a:lnL w="9525"><a:solidFill><a:srgbClr val="C8D0DC"/></a:solidFill></a:lnL>'
                f'<a:lnR w="9525"><a:solidFill><a:srgbClr val="C8D0DC"/></a:solidFill></a:lnR>'
                f'<a:lnT w="9525"><a:solidFill><a:srgbClr val="C8D0DC"/></a:solidFill></a:lnT>'
                f'<a:lnB w="9525"><a:solidFill><a:srgbClr val="C8D0DC"/></a:solidFill></a:lnB>'
                f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill></a:tcPr></a:tc>')
    hdr = '<a:tr h="380000">' + ''.join(cell(h,'1A3A6B','FFFFFF',True,950) for h in headers) + '</a:tr>'
    body = ''
    for i, row in enumerate(rows):
        f = 'F0F4FA' if i%2==0 else 'FFFFFF'
        body += f'<a:tr h="{row_h}">' + ''.join(cell(c, f) for c in row) + '</a:tr>'
    return (f'<p:graphicFrame><p:nvGraphicFramePr>'
            f'<p:cNvPr id="30" name="tbl"/>'
            f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/>'
            f'</p:nvGraphicFramePr>'
            f'<p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            f'<a:tbl><a:tblPr firstRow="1" bandRow="1"/><a:tblGrid>{grid}</a:tblGrid>'
            f'{hdr}{body}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')

def text_box(x, y, cx, cy, xml, id_=16, name='tb'):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="{id_}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        {xml}
      </p:txBody></p:sp>'''

def save(n, xml):
    with open(f'{SLIDES}/slide{n}.xml', 'w', encoding='utf-8') as f:
        f.write(xml)
    print(f'slide{n}.xml 저장 완료')

# ─── SLIDE 1: 표지 (CES/MWC 템플릿 좌표 기준) ──────────────────────
# Layout y positions from original template: title=888500 cy=599400, date=3899950
save(1, sld(f'''
    <p:sp><p:nvSpPr><p:cNvPr id="10" name="title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="888500"/><a:ext cx="9144000" cy="599400"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('Embodied AI', sz=4800, bold=True, color='1A3A6B')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="sub1"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="1600000"/><a:ext cx="9144000" cy="500000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('몸을 가진  AI 의 부상', sz=2800, bold=True, color='1A5276')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="sub2"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="2250000"/><a:ext cx="9144000" cy="400000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('구현 AI 기술·제품·생태계 종합 분석', sz=1800, color='444444')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="13" name="meta"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="3899950"/><a:ext cx="9144000" cy="381900"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('신동형  |  2026.04.08', sz=1600, color='555555')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
'''))

# ─── SLIDE 2: INDEX ──────────────────────────────────────────────
# ─── SLIDE 2: INDEX — CES 스타일 목차 ───────────────────────────
# 레이아웃: 빨간 세로 악센트 바 | "목차" 제목 | 테두리 박스 + 로마숫자 목록
def idx_row(num, text, row_id):
    """목차 테이블 한 행: 번호(우정렬) + 내용(좌정렬)"""
    def cell(content, algn='l', bold=False, col_w=None):
        b = ' b="1"' if bold else ''
        return (f'<a:tc><a:txBody>'
                f'<a:bodyPr bIns="76200" lIns="152400" rIns="152400" tIns="76200"/>'
                f'<a:lstStyle/>'
                f'<a:p><a:pPr algn="{algn}"><a:buNone/></a:pPr>'
                f'<a:r><a:rPr lang="ko" sz="1700"{b} u="none" dirty="0">'
                f'<a:solidFill><a:srgbClr val="1A3A6B"/></a:solidFill></a:rPr>'
                f'<a:t>{esc(content)}</a:t></a:r><a:endParaRPr/></a:p>'
                f'</a:txBody>'
                f'<a:tcPr><a:lnL w="0"><a:noFill/></a:lnL>'
                f'<a:lnR w="0"><a:noFill/></a:lnR>'
                f'<a:lnT w="0"><a:noFill/></a:lnT>'
                f'<a:lnB w="0"><a:noFill/></a:lnB>'
                f'<a:noFill/></a:tcPr></a:tc>')
    return f'<a:tr h="590000">{cell(num, algn="r", bold=True)}{cell(text)}</a:tr>'

toc_items = [
    ('I.',    '전체 현황 — 개념·특징·글로벌 현황 및 시장 규모'),
    ('II.',   '기술 동향 — 알고리즘 4경로·데이터 전략·VLA 진화 상세'),
    ('III.',  '제품 및 응용 — 인형·산업용 로봇 제품 현황'),
    ('IV.',   '스마트 운반 & 신형 제품 — 이동장비·신체·협동팔'),
    ('V.',    '산업 생태계 — 352개 기업·공급망·표준화 전략'),
    ('VI.',   '미래 전망 — 시장 $3,398억·기술 로드맵·시사점'),
    ("VII.",  "Devil's Advocate — 비판적 관점 5가지"),
]
toc_rows = ''.join(idx_row(n, t, i) for i,(n,t) in enumerate(toc_items))

save(2, sld(f'''
    <!-- ① 목차 제목: slideLayout4 빨간 선(x≈402375)보다 오른쪽에 배치 -->
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="idx_title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="550000" y="264100"/><a:ext cx="8430000" cy="450000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="l"><a:buNone/></a:pPr>
          {rr('목차', sz=2800, bold=True, color='1A3A6B')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <!-- ③ 테두리 박스 (outline only) -->
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="idx_border"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="800000"/><a:ext cx="8818500" cy="4100000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/>
        <a:ln w="12700"><a:solidFill><a:srgbClr val="AAAAAA"/></a:solidFill></a:ln></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p></p:txBody></p:sp>
    <!-- ④ 로마숫자 목록 (테두리 박스 내 테이블, 셀 경계 없음) -->
    <p:graphicFrame>
      <p:nvGraphicFramePr>
        <p:cNvPr id="13" name="toc_tbl"/>
        <p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
        <p:nvPr/>
      </p:nvGraphicFramePr>
      <p:xfrm><a:off x="200000" y="840000"/><a:ext cx="8740000" cy="4130000"/></p:xfrm>
      <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">
        <a:tbl>
          <a:tblPr firstRow="0" bandRow="0"/>
          <a:tblGrid>
            <a:gridCol w="700000"/>
            <a:gridCol w="8040000"/>
          </a:tblGrid>
          {toc_rows}
        </a:tbl>
      </a:graphicData></a:graphic>
    </p:graphicFrame>
'''))

# ─── SLIDE 3: I-① 개념 및 특징 ───────────────────────────────────
save(3, sld(
    z1('I. 전체 현황', '① 개념과 특징') +
    z2('구현 AI는 "AI+로봇"의 단순 결합을 넘어 물리 본체-지능-환경 상호작용의 완전 폐루프를 구현하는 새로운 기술 패러다임임.') +
    z3('1. 구현 AI의 개념과 내涵') +
    z4(
        pp(rr('■ ITU-T F.748.66 정의', sz=1300, bold=True, color='1A3A6B')) +
        pp(rr('"물리 실체와 융합해 자율적으로 물리 세계와 상호작용하고 환경에 적응하는 AI"', sz=1100, color='0055B3')) +
        pp_e() +
        pp(rr('■ 핵심 3요소', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('구현 본체: 인형로봇·4족로봇·협동팔·자율주행차·드론 등', sz=1100)) +
        pp_b(rr('지능 내핵: LLM → VLM → VLA → 세계모델(World Model) 진화', sz=1100)) +
        pp_b(rr('환경 상호작용: "제1인칭 시각"으로 현실 물리 세계와 동적 교감', sz=1100)) +
        pp_e() +
        pp(rr('■ 3대 역량 목표', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('인지 능력: "보고" → "이해". 시각·언어·동작 멀티모달 연합 훈련', sz=1100)) +
        pp_b(rr('협력 능력: "단독 실행" → "협동 작업". 단말-엣지-클라우드 협동', sz=1100)) +
        pp_b(rr('학습 능력: "사전 학습" → "현장 학습". 실환경 적응 자율 진화', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 4: I-② 글로벌 현황 ───────────────────────────────────
save(4, sld(
    z1('I. 전체 현황', '② 글로벌 동향 & 단계') +
    z2('구현 AI는 2030년 누계 시장 3,398억 달러 규모로 성장이 예측되나, 데이터-모델-본체-장면 난제 사이클이 미해결 상태로 산업화는 초기 단계임.') +
    z3('2. 글로벌 주목도 & 산업 현황') +
    z4_2col(
        pp(rr('글로벌 시장 전망 (2030)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('인형로봇: 40.4 억 달러', sz=1100)) +
        pp_b(rr('자율주행(L1-L3): 1,722 억 달러', sz=1100)) +
        pp_b(rr('드론: 1,636 억 달러', sz=1100)) +
        pp_b(rr('누계 합계: 3,398 억 달러', sz=1100, color='B71C1C')) +
        pp_e() +
        pp(rr('주요 투자 사례 (2025)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Figure AI: 10 억$ 융자, 기업가치 390 억$', sz=1100)) +
        pp_b(rr('Apptronik: 3.5 억$ A라운드', sz=1100)) +
        pp_b(rr('中 전체: 744 건, 735 억 위안', sz=1100)),
        pp(rr('산업 현황 & 3대 논쟁', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('경로 선택: 감지→인지→결정→실행 구현, 데이터 vs 모델 비중?', sz=1050)) +
        pp_b(rr('본체 구조: 전용 형태 vs 범용 형태?', sz=1050)) +
        pp_b(rr('데이터 방안: 실기체 vs 仿真 합성 어떻게 조합?', sz=1050)) +
        pp_e() +
        pp(rr('현 VLA 한계', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('泛化性 부족: 훈련 분포 밖 장면 성능 급락', sz=1050)) +
        pp_b(rr('장기 태스크 성공률: 20~40% 수준', sz=1050)) +
        pp_b(rr('SW-HW 협동 미완성: 시간 스케일 불일치', sz=1050))
    ) +
    z5(SRC)
))

# ─── SLIDE 6: II-① 알고리즘 4대경로 ─────────────────────────────
save(6, sld(
    z1('II. 기술 혁신', '① 알고리즘 4대 경로') +
    z2('LLM→VLM→VLA→세계모델로의 기술 진화가 구현 AI의 인지·결정 능력을 급격히 향상시키며, 2025년 VLA 논문 수 1년 만에 4배 급증(1,700편+)이 이를 입증함.') +
    z3('1. 알고리즘 기술 — 미수렴, 다경로 탐색') +
    make_table(
        ['경로', '대표 모델', '핵심 특성', '적용 사례'],
        [
            ['경로 1\n모듈화 분층', 'MPC / WBC', '심층학습(인지)+기계학습(운동)+인공프로그래밍', 'AMR 창고 운반·운동회 댄스'],
            ['경로 2\n분층 대모델', 'LLM/VLM\n플래너', '대모델이 태스크 추론·계획, API로 동작 호출', 'Google Gemini Robotics-ER 1.5'],
            ['경로 3\nE2E VLA', 'Helix / π0.5\nRoboBrain 2.0', '시각·언어·동작 단일 프레임 통일\n7~9Hz인지+200Hz운동 협동', 'Figure AI / PI / 智源'],
            ['경로 4\n세계모델', 'DreamVLA\nCtrl-World', '동역학 모델링으로 행동 예연·동작 예측\nVLA 동작 정책 학습 지도', '칭화대+스탠포드'],
        ],
        x=162800, y=1790000, cx=8818500, cy=2860000,
        col_widths=[1500000, 2000000, 3000000, 2318500]
    ) +
    z5(SRC)
))

# ─── SLIDE 7: II-② 데이터 + 본체 ────────────────────────────────
save(7, sld(
    z1('II. 기술 혁신', '② 데이터 & 본체') +
    z2('구현 AI 학습에는 수만~수백만 시간의 데이터가 필요하며, 仿真합성과 실기체채집의 이중전략이 업계 표준으로 자리잡고 있음. 본체는 SW-HW 일체형 부품 혁신이 핵심임.') +
    z3('2. 데이터 핵심 수요 & 본체 다원화') +
    z4_2col(
        pp(rr('■ 데이터 전략 (이중)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('仿真합성: 물체 자산 합성·물리환경 생성·궤적·동작 비디오', sz=1050)) +
        pp_b(rr('실기체 채집: 원격조작(VR장갑)·개방환경·동작캡처(광학/관성)', sz=1050)) +
        pp_b(rr('핵심 과제: Sim-to-Real Gap 극복 (仿真→현실 성능 급락 방지)', sz=1050, color='B71C1C')) +
        pp_e() +
        pp(rr('■ 클라우드-엣지-단말 협동', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('클라우드: 데이터 서비스·仿真 플랫폼·모델 서비스', sz=1050)) +
        pp_b(rr('엣지: 데이터 처리·기술 편성·개발 툴', sz=1050)) +
        pp_b(rr('단말: 추론 칩(엣지 AI), 데이터 업로드·모델 배포', sz=1050)),
        pp(rr('■ 본체 다원화 혁신', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('인형로봇 (핵심 포커스)', sz=1050, color='0055B3')) +
        pp_b(rr('  Figure AI Helix: E2E, 7~9Hz인지+200Hz운동', sz=1000)) +
        pp_b(rr('  宇树 R1: 3.99만 위안, 가격 경쟁력', sz=1000)) +
        pp_b(rr('  Apptronik Apollo + Google DeepMind', sz=1000)) +
        pp_e() +
        pp_b(rr('4족·협동팔·복합형 (산업 현장)', sz=1050, color='1A4D1A')) +
        pp_b(rr('  Agility Digit: Amazon 물류 협업', sz=1000)) +
        pp_e() +
        pp_b(rr('본체 4대 시스템: 감지·동력·에너지·실행', sz=1050))
    ) +
    z5(SRC)
))

# ─── SLIDE 8: II-③ VLA 진화 상세 ────────────────────────────────
save(8, sld(
    z1('II. 기술 혁신', '③ VLA 진화 상세') +
    z2('엔드투엔드 VLA는 "대통일 단일 시스템"과 "분층 협력 이중 시스템" 두 가지 설계 아키텍처로 발전 중이며, 멀티모달 융합·강화학습이 핵심 개선 방향임.') +
    z3('3. VLA 기술 진화 심층 분석') +
    z4_2col(
        pp(rr('① 대통일 단일 시스템 VLA', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('UniAct (칭화대): 이기종 데이터로 범용 동작 공간 학습, 100개 시연만으로 4종 제어 인터페이스', sz=1050)) +
        pp_b(rr('MLA (北京大): 이미지+점군+촉각+언어 완전 멀티센서 멀티모달', sz=1050)) +
        pp_b(rr('GEN-0 (Generalist AI): 비동기 시간 처리, 100억 파라미터 확장 시 빠른 적응', sz=1050)) +
        pp_e() +
        pp(rr('② 분층 협력 이중 시스템', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Figure Helix: 7~9Hz 추론+200Hz 운동 제어 협동', sz=1050)) +
        pp_b(rr('FiS (北京大·港大·智方): 빠른 실행 시스템을 느린 추론 시스템에 내재화, 117.7Hz 동작 생성', sz=1050)),
        pp(rr('③ 멀티모달 확장', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('ForceVLA (복단대): 힘 감지 혼합 전문가 융합 모듈 FVLMoE', sz=1050)) +
        pp_b(rr('TLA (삼성 중국): 촉각 토큰화 후 LLM에 투입, 촉각·시각·언어 통합', sz=1050)) +
        pp_e() +
        pp(rr('④ 세계모델 융합', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('DreamVLA (상하이교통대): 세계 지식으로 환경 미래 상태 예측, 동작 탐색 보조', sz=1050)) +
        pp_b(rr('Ctrl-World (칭화대+스탠포드): 태스크 예연·가상 전략 채점으로 낯선 태스크 성공률 향상', sz=1050)) +
        pp_e() +
        pp(rr('⑤ 강화학습 융합', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('PI π*0.6: 전문가 교정 지도로 오류 수정, 성공률 지속 향상', sz=1050)) +
        pp_b(rr('RLinf (칭화대): 대규모 강화학습 프레임워크, 구현 AI 특화', sz=1050))
    ) +
    z5(SRC)
))

# ─── SLIDE 9: III-① 로봇 제품 ───────────────────────────────────
save(9, sld(
    z1('III. 제품 생태계', '① 로봇 제품') +
    z2('인형로봇이 구현 AI 분야의 핵심 캐리어로 부상하며, 중미 양국이 전 스택·중하드웨어·重소프트 大脑 3대 노선으로 경쟁 중임. 宇树 R1은 3.99만 위안으로 가격 장벽을 낮췄음.') +
    z3('1. 로봇 — 가장 "핫한" 구현 AI 캐리어') +
    make_table(
        ['분류', '대표 기업/제품', '핵심 특징'],
        [
            ['전 스택파\n(SW+HW 자체개발)', 'Figure AI (Helix)\n智元 (Go-1, 灵犀)', 'E2E 모델로 SW-HW 협동 능력 극대화\n기술 폐루프로 자체 진화'],
            ['중하드웨어파\n(동체 설계 최적화)', '宇树 R1 (3.99만위안)\nAgility Digit+Amazon\nApptronik Apollo+Google', '비용 경쟁력 + 운동 제어 알고리즘 강점\n물류·제조 현장 조기 상용화'],
            ['重소프트 大脑파\n(범용 기반 모델)', 'Physical Intelligence π0.5\nField AI (FFMs)\n銀河通用', '표준화 인터페이스로 이기종 로봇 적응\n낮은 개발 문턱, 오픈소스 전략'],
        ],
        x=162800, y=1790000, cx=8818500, cy=2860000,
        col_widths=[2200000, 3200000, 3418500]
    ) +
    z5(SRC)
))

# ─── SLIDE 10: III-② 스마트 운반 & 신형 제품 ────────────────────
save(10, sld(
    z1('IV. 스마트 운반 & 신형 제품', '이동장비 · 신체 · 협동팔') +
    z2('자율주행차·드론은 구현 AI의 가장 빠른 상용화 캐리어로, 2030년 합계 3,358억 달러 시장을 형성할 전망임. 신형 제품은 "육해공 일체화"로 비구조화 환경 침투 중임.') +
    z3('2. 스마트 운반 장비 & 신형 제품') +
    z4_2col(
        pp(rr('■ 자율주행차 (L1-L3)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('2030년 시장 1,722 억 달러 (Grand View Research)', sz=1100)) +
        pp_b(rr('구조화 환경(도심) → 야외 비구조화 환경 확장', sz=1100)) +
        pp_b(rr('Tesla: 인형로봇 Optimus와 자율주행 기술 공유', sz=1100)) +
        pp_e() +
        pp(rr('■ 드론·무인기', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('2030년 시장 1,636 억 달러', sz=1100)) +
        pp_b(rr('항공·수중·극한 환경으로 확장', sz=1100)) +
        pp_b(rr('군집 무인기: 복잡 환경 멀티 에이전트 협동', sz=1100)),
        pp(rr('■ 신형 스마트 제품', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('자변형 이동 장치: 구조·운동 모드 동적 재구성', sz=1100)) +
        pp_b(rr('군집 마이크로 장치: 확장·재조합 가능 스마트 군체', sz=1100)) +
        pp_b(rr('"육해공 일체화": 단기능 → 다공간·다주체 협동', sz=1100)) +
        pp_e() +
        pp(rr('■ 미래 생활 "스마트 3대장"', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('인형로봇 (가정·산업·의료 서비스)', sz=1100)) +
        pp_b(rr('자율주행차 (스마트 이동)', sz=1100)) +
        pp_b(rr('드론 (물류·탐사·극한 환경)', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 11: IV 산업 생태계 ────────────────────────────────────
save(11, sld(
    z1('V. 산업 생태계', '352개 기업 · 공급망 · 표준화 전략') +
    z2('구현 AI 산업 체인이 行業응용·제품서비스·기술서비스·인프라 4대 블록으로 성장하며, 중국은 352개 기업 이상이 735억 위안 규모의 생태계를 형성 중임.') +
    z3('1. 생태계 현황 & 과제') +
    z4_2col(
        pp(rr('■ 생태계 규모 (중국)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('투자: 2025.12 기준 744건, 총 735.43 억 위안', sz=1100)) +
        pp_b(rr('기업 수: 352개 이상 (베이징·상하이·선전·항저우 집중)', sz=1100)) +
        pp_b(rr('4대 블록: 행업 응용·제품 서비스·기술 서비스·인프라', sz=1100)) +
        pp_e() +
        pp(rr('■ 훈련장 건설 붐', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('현황: 마라톤·格鬪赛·运动会 행사 사회 고관심', sz=1100)) +
        pp_b(rr('실제 효용: 복잡 환경 적응 능력 불충분, 추가 검증 필요', sz=1100)) +
        pp_b(rr('과제: 정형화→비정형화 환경 전환 능력 제한', sz=1100)),
        pp(rr('■ 표준 체계 구축', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('국제: ITU-T F.748.66 구현 AI 시스템 표준 제정', sz=1100)) +
        pp_b(rr('국내: 산업 표준화 단계적 추진 중', sz=1100)) +
        pp_b(rr('목표: 기술 호환성·공급망 효율화 확보', sz=1100)) +
        pp_e() +
        pp(rr('■ 안전 문제 (규모화 제한 요소)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('물리적 위험: 고속 운동 본체의 안전 사고 리스크', sz=1100)) +
        pp_b(rr('데이터 보안: 센서 수집 개인정보 처리', sz=1100)) +
        pp_b(rr('책임 귀속: AI 오판 시 법적 책임 불명확', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 12: V 전망 ─────────────────────────────────────────────
save(12, sld(
    z1('VI. 미래 전망', '시장 $3,398억 · 기술 로드맵 · 시사점') +
    z2('구현 AI는 기술 아키텍처 재편·응용 장면 심화·안전 윤리 구축 3대 방향으로 발전하며, 2030년 3,398억 달러 시장을 형성할 전망임.') +
    z3('3대 발전 방향') +
    z4(
        pp(rr('① 기술 아키텍처 재편: "기능 모듈 적층" → "다모달 인지 융합"', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('세계모델이 大脑에서 물리 시뮬레이션 구현 → 행동 예연·동작 예측 최적화', sz=1100)) +
        pp_b(rr('LLM→VLM→VLA 진화의 다음 단계: 세계모델 기반 자율 성장 AI', sz=1100)) +
        pp_b(rr('멀티모달 인지 능력: 시각+언어+촉각+힘 감지+점군 통합 융합', sz=1100)) +
        pp_e() +
        pp(rr('② 응용 장면 심화: "시연" → "실용"', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('공장·창고 → 가정·의료·교육 → 특수·극한 환경으로 확장', sz=1100)) +
        pp_b(rr('"맞춤 개발" → "표준화 납품" → "2차 개발 운영 유지" 폐루프 완성', sz=1100)) +
        pp_b(rr('인형로봇 ChatGPT 모멘트: 통용 인형로봇 대중화 변곡점 임박', sz=1100)) +
        pp_e() +
        pp(rr('③ 안전 윤리 구축: "규정 준수" → "윤리 협동 프레임워크" 전방위 배치', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('기능 안전·사이버 보안·책임 귀속·프라이버시 보호 4대 이슈', sz=1100)) +
        pp_b(rr('국제 표준 선점: ITU·ISO 등 국제기구 내 기술 주도권 경쟁 가속', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 13: Devil's Advocate ──────────────────────────────────
# ※ z1 좌측 라벨은 반드시 INDEX(slide2) 의 7번째 챕터(VII.) 와 일치해야 한다.
#    verify_toc.py 가 이를 검사하므로 챕터 라벨을 임의로 바꾸지 말 것.
save(13, sld(
    z1("VII. Devil's Advocate", '비판적 관점 5가지') +
    z2("구현 AI는 기술 열기와 달리 VLA 泛化性 한계·장기 태스크 성공률 20~40%·SW-HW 협동 미완성·데이터 부족·고비용 등 5대 구조적 난제가 미해결 상태임.") +
    z3("비판적 관점 5가지") +
    z4(
        pp_b(rr('① VLA 泛化性 한계: 훈련 데이터 분포 밖 장면 성능 급락. 1X World Model·PI π0.5 낯선 상황 성공률 대폭 하락. 현실 복잡성 완전 커버 어려운 구조적 한계.', sz=1100)) +
        pp_e() +
        pp_b(rr('② 장기 태스크 수행 20~40%: Google Gemini Robotics-ER 1.5 + Gemini Robotics VLA의 "쓰레기 정리"·"물품 교환" 장기 태스크 성공률. 고수준 계획(1~10Hz) vs 저수준 제어(100Hz+) 시간 스케일 불일치.', sz=1100)) +
        pp_e() +
        pp_b(rr('③ SW-HW 협동 미완성: 복수 시간 스케일 협동 제어 필요. 어느 링크에서든 신호 불안정 시 태스크 실패. 跨본체 이전 시 성능 재현 불가.', sz=1100)) +
        pp_e() +
        pp_b(rr('④ 데이터 부족 & Sim-to-Real Gap: 실기체 데이터는 훈련장 의존. 仿真합성은 가상-현실 격차 미해소. 채집-활용 전략 미확정.', sz=1100)) +
        pp_e() +
        pp_b(rr('⑤ 고비용 & 표준화 부재: 시스템 가격 고가 유지. 맞춤 개발 구조가 대규모 양산 제약. 호환성 부재로 공급망 효율화 지연.', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 5: 맺음말 (sldIdLst에서 마지막으로 이동되어 최종 페이지가 됨) ─────
# build_pptx.sh 가 sldIdLst에서 rId10(slide5)을 마지막으로 이동시킨다.
# 이 슬라이드는 placeholder를 사용하지 않고 자체 textBox로 구성된다.
closing_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<p:sld {NS}>
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    <p:sp><p:nvSpPr><p:cNvPr id="10" name="closing_title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="500000"/><a:ext cx="9144000" cy="800000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr("감사합니다.", sz=4000, bold=True, color='1A3A6B')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="closing_bullets"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="1200000" y="1500000"/><a:ext cx="6744000" cy="1500000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="t" bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr>
        <a:lstStyle/>
        <a:p><a:pPr algn="l" marL="300000" indent="-300000"><a:buChar char="●"/></a:pPr>
          {rr('이 자료는 지속적으로 업데이트되어 공개될 예정입니다.', sz=1500)}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="l" marL="300000" indent="-300000"><a:buChar char="●"/></a:pPr>
          {rr('사례 연구나 협업에 관심 있는 기업 및 기관의 연락을 환영합니다.', sz=1500)}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="l" marL="300000" indent="-300000"><a:buChar char="●"/></a:pPr>
          {rr('보고서, 출판, 강연 문의는 편하게 연락 주세요.', sz=1500)}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="closing_contact"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="3200000"/><a:ext cx="9144000" cy="1200000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>{rr('신동형', sz=2000, bold=True, color='1A3A6B')}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>{rr('010-2202-8761', sz=1800, color='555555')}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>{rr('donghyung.shin@gmail.com', sz=1800, color='555555')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''

with open(f'{SLIDES}/slide5.xml', 'w', encoding='utf-8') as f:
    f.write(closing_xml)
print('  slide5.xml (맺음말) saved')

print("\n모든 슬라이드 XML 저장 완료!")
print("슬라이드 매핑 (sldIdLst 기준 최종 표시 순서):")
print("  1=표지, 2=INDEX, 3=I-①개념, 4=I-②현황")
print("  5=II-①알고리즘, 6=II-②데이터/본체, 7=II-③VLA")
print("  8=III-①로봇, 9=IV.스마트운반&신형")
print("  10=V.산업생태계, 11=VI.미래전망, 12=VII.Devil's Advocate")
print("  13=감사합니다 (sldIdLst 마지막)")
