#!/usr/bin/env python3
"""Build English PPTX slides — canonical 신동형 인사이트 정본 템플릿.

build_pptx.sh 오케스트레이터에서 호출된다. unpack/pack/strip 등은 오케스트레이터가
처리하므로, 이 스크립트는 슬라이드 XML 파일만 작성한다.

환경변수 TARGET_UNPACKED 가 unpack된 디렉터리(예: 'unpacked_en') 를 가리킨다.
"""
import os, re

TARGET = os.environ.get('TARGET_UNPACKED', 'unpacked_en')
SLIDES = f'{TARGET}/ppt/slides'

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')

LANG = 'en-US'

def esc(t): return str(t).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def rr(text, sz=None, bold=False, color=None, lang='en-US', u='none'):
    sz_a = f' sz="{sz}"' if sz else ''
    b_a  = ' b="1"' if bold else ''
    u_a  = f' u="{u}"' if u else ''
    col  = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if color else ''
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

def z1(left, right):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="10" name="z1L"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="264100"/><a:ext cx="5100900" cy="220800"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/><a:lstStyle/>
        <a:p><a:pPr algn="l"><a:buNone/></a:pPr>{rr(left,sz=1800,bold=True,color='1A3A6B')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="z1R"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="4039250" y="264100"/><a:ext cx="4941900" cy="220800"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/><a:lstStyle/>
        <a:p><a:pPr algn="r"><a:buNone/></a:pPr>{rr(right,sz=1700,color='1A3A6B')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>'''

def z2(msg):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="z2"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162725" y="641800"/><a:ext cx="8818500" cy="669300"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="t" bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        <a:p><a:pPr algn="l"><a:buNone/></a:pPr>{rr(msg,sz=1500)}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>'''

def z3(heading):
    # Center-aligned + underline (confirmed user style)
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
      <p:spPr><a:xfrm><a:off x="162800" y="{top}"/><a:ext cx="4300000" cy="2780000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        {left_xml}</p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="15" name="z4R"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="4680000" y="{top}"/><a:ext cx="4300000" cy="2780000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr><a:lstStyle/>
        {right_xml}</p:txBody></p:sp>'''

def z5(src):
    return f'''
    <p:sp><p:nvSpPr><p:cNvPr id="99" name="z5"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="104375" y="4715475"/><a:ext cx="8938800" cy="130000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/><a:lstStyle/>
        <a:p><a:pPr><a:buNone/></a:pPr>{rr('※ Source: ' + src, sz=800, color='888888')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>'''

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
                f'<a:r><a:rPr lang="en-US" sz="{sz}"{b} u="none" dirty="0"><a:solidFill><a:srgbClr val="{tcol}"/></a:solidFill></a:rPr>'
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
    print(f'  slide{n}.xml saved')

SRC = 'CAICT Embodied Intelligence Development Report (2025), CAICT & Tsinghua University, Jan 2026'

# ─── SLIDE 1: COVER ──────────────────────────────────────────────
save(1, sld(f'''
    <p:sp><p:nvSpPr><p:cNvPr id="10" name="title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="888500"/><a:ext cx="9144000" cy="599400"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('Embodied AI', sz=4800, bold=True, color='1A3A6B')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="sub1"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="1600000"/><a:ext cx="9144000" cy="500000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('The Rise of AI with a Body', sz=2800, bold=True, color='1A5276')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="sub2"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="2250000"/><a:ext cx="9144000" cy="400000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('Comprehensive Analysis: Technology · Products · Ecosystem', sz=1800, color='444444')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="13" name="meta"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="3899950"/><a:ext cx="9144000" cy="381900"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('Dong Hyung Shin  |  2026.04.08', sz=1600, color='555555')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
'''))

# ─── SLIDE 2: INDEX ──────────────────────────────────────────────
def idx_row_en(num, text, row_id):
    def cell(content, algn='l', bold=False):
        b = ' b="1"' if bold else ''
        return (f'<a:tc><a:txBody>'
                f'<a:bodyPr bIns="76200" lIns="152400" rIns="152400" tIns="76200"/>'
                f'<a:lstStyle/>'
                f'<a:p><a:pPr algn="{algn}"><a:buNone/></a:pPr>'
                f'<a:r><a:rPr lang="en-US" sz="1700"{b} u="none" dirty="0">'
                f'<a:solidFill><a:srgbClr val="1A3A6B"/></a:solidFill></a:rPr>'
                f'<a:t>{esc(content)}</a:t></a:r><a:endParaRPr/></a:p>'
                f'</a:txBody>'
                f'<a:tcPr><a:lnL w="0"><a:noFill/></a:lnL>'
                f'<a:lnR w="0"><a:noFill/></a:lnR>'
                f'<a:lnT w="0"><a:noFill/></a:lnT>'
                f'<a:lnB w="0"><a:noFill/></a:lnB>'
                f'<a:noFill/></a:tcPr></a:tc>')
    return f'<a:tr h="590000">{cell(num, algn="r", bold=True)}{cell(text)}</a:tr>'

toc_en = [
    ('I.',    'Overall Status — Concepts, Features, Global Status & Market Size'),
    ('II.',   'Technology Trends — Algorithm 4 Pathways, Data Strategy, VLA Evolution'),
    ('III.',  'Products & Applications — Humanoid & Industrial Robot Products'),
    ('IV.',   'Smart Transport & New Products — Vehicles, Drones & Novel Devices'),
    ('V.',    'Industry Ecosystem — 352+ Companies, Supply Chain & Standardization'),
    ('VI.',   'Future Outlook — $339.8B Market, Technology Roadmap & Implications'),
    ("VII.",  "Devil's Advocate — 5 Critical Structural Challenges"),
]
toc_rows_en = ''.join(idx_row_en(n, t, i) for i,(n,t) in enumerate(toc_en))

save(2, sld(f'''
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="idx_title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="550000" y="264100"/><a:ext cx="8430000" cy="450000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="l"><a:buNone/></a:pPr>
          {rr('Contents', sz=2800, bold=True, color='1A3A6B')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="idx_border"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="800000"/><a:ext cx="8818500" cy="4100000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/>
        <a:ln w="12700"><a:solidFill><a:srgbClr val="AAAAAA"/></a:solidFill></a:ln></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p></p:txBody></p:sp>
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
          <a:tblGrid><a:gridCol w="700000"/><a:gridCol w="8040000"/></a:tblGrid>
          {toc_rows_en}
        </a:tbl>
      </a:graphicData></a:graphic>
    </p:graphicFrame>
'''))

# ─── SLIDE 3: I-① Concepts & Characteristics ─────────────────────
save(3, sld(
    z1('I. Overall Status', '① Concepts & Characteristics') +
    z2('Embodied AI transcends the simple fusion of "AI+robotics" to realize a complete closed loop of physical body–intelligence–environment interaction, representing a new technological paradigm.') +
    z3('1. Embodied AI: Definition & Core Elements') +
    z4(
        pp(rr('■ ITU-T F.748.66 Definition', sz=1300, bold=True, color='1A3A6B')) +
        pp(rr('"AI that integrates with physical entities to autonomously interact with and adapt to the physical world"', sz=1100, color='0055B3')) +
        pp_e() +
        pp(rr('■ Three Core Components', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Physical Body: Humanoid robots, quadrupeds, collaborative arms, autonomous vehicles, drones', sz=1100)) +
        pp_b(rr('Intelligence Core: LLM → VLM → VLA → World Model evolutionary progression', sz=1100)) +
        pp_b(rr('Environment Interaction: First-person perception for dynamic engagement with the physical world', sz=1100)) +
        pp_e() +
        pp(rr('■ Three Capability Goals', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Perception: "See" → "Understand". Multi-modal joint training: vision, language, and motion', sz=1100)) +
        pp_b(rr('Collaboration: "Solo execution" → "Cooperative tasks". Terminal–edge–cloud coordination', sz=1100)) +
        pp_b(rr('Learning: "Pre-training" → "In-situ learning". Autonomous evolution through real-world adaptation', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 4: I-② Global Trends & Market ────────────────────────
save(4, sld(
    z1('I. Overall Status', '② Global Trends & Market Stage') +
    z2('Embodied AI is projected to reach a cumulative market of $339.8B by 2030, yet unresolved data–model–body–scenario challenge cycles keep the industry in its early commercialization phase.') +
    z3('2. Global Attention & Industry Status') +
    z4_2col(
        pp(rr('Global Market Outlook (2030)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Humanoid robots: $4.04B', sz=1100)) +
        pp_b(rr('Autonomous driving (L1–L3): $172.2B', sz=1100)) +
        pp_b(rr('Drones: $163.6B', sz=1100)) +
        pp_b(rr('Cumulative total: $339.8B', sz=1100, color='B71C1C')) +
        pp_e() +
        pp(rr('Key Investment Cases (2025)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Figure AI: $1B raised, valuation $39B', sz=1100)) +
        pp_b(rr('Apptronik: $350M Series A', sz=1100)) +
        pp_b(rr('China total: 744 deals, ¥73.5B', sz=1100)),
        pp(rr('Industry Status & 3 Key Debates', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Pathway: Sense→Perceive→Decide→Act — data vs. model weighting?', sz=1050)) +
        pp_b(rr('Body design: Specialized form vs. general-purpose form?', sz=1050)) +
        pp_b(rr('Data strategy: Real-world collection vs. simulation synthesis?', sz=1050)) +
        pp_e() +
        pp(rr('Current VLA Limitations', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Poor generalization: Performance drops sharply outside training distribution', sz=1050)) +
        pp_b(rr('Long-horizon task success rate: Only 20–40%', sz=1050)) +
        pp_b(rr('SW–HW coordination incomplete: Multi-timescale mismatch', sz=1050))
    ) +
    z5(SRC)
))

# ─── SLIDE 6: II-① Algorithm 4 Pathways ─────────────────────────
save(6, sld(
    z1('II. Technology Trends', '① Algorithm 4 Pathways') +
    z2('The LLM→VLM→VLA→World Model progression has rapidly enhanced cognition and decision-making in embodied AI; VLA papers quadrupled in one year to 1,700+ in 2025, confirming the surge.') +
    z3('1. Algorithm Technology — Unconverged, Multi-Pathway Exploration') +
    make_table(
        ['Pathway', 'Representative Models', 'Key Characteristics', 'Application Examples'],
        [
            ['Pathway 1\nModular-Layered', 'MPC / WBC', 'Deep learning (perception) + machine learning (motion) + programmed rules', 'AMR warehouse logistics, athletic performance'],
            ['Pathway 2\nLayered Large Model', 'LLM/VLM\nPlanner', 'Large model for task reasoning & planning; API calls for motion execution', 'Google Gemini Robotics-ER 1.5'],
            ['Pathway 3\nEnd-to-End VLA', 'Helix / π0.5\nRoboBrain 2.0', 'Unified vision–language–action in a single framework\n7–9 Hz cognition + 200 Hz motion coordination', 'Figure AI / PI / Zhiyuan'],
            ['Pathway 4\nWorld Model', 'DreamVLA\nCtrl-World', 'Dynamics modeling for action pre-play and motion prediction\nGuides VLA action-policy learning', 'Tsinghua + Stanford'],
        ],
        x=162800, y=1790000, cx=8818500, cy=2860000,
        col_widths=[1500000, 2000000, 3000000, 2318500]
    ) +
    z5(SRC)
))

# ─── SLIDE 7: II-② Data & Hardware ──────────────────────────────
save(7, sld(
    z1('II. Technology Trends', '② Data & Hardware') +
    z2('Embodied AI training demands tens of thousands to millions of hours of data. The dual strategy of simulation synthesis and real-world collection has become the industry standard, while hardware innovation focuses on integrated SW–HW component breakthroughs.') +
    z3('2. Core Data Requirements & Diversified Hardware') +
    z4_2col(
        pp(rr('■ Data Strategy (Dual Track)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Simulation synthesis: Object asset generation, physics env., trajectory & motion video', sz=1050)) +
        pp_b(rr('Real-world collection: Teleoperation (VR gloves), open environments, motion capture', sz=1050)) +
        pp_b(rr('Key challenge: Overcoming Sim-to-Real Gap (preventing performance drop)', sz=1050, color='B71C1C')) +
        pp_e() +
        pp(rr('■ Cloud–Edge–Terminal Coordination', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Cloud: Data services, simulation platforms, model services', sz=1050)) +
        pp_b(rr('Edge: Data processing, task orchestration, development tools', sz=1050)) +
        pp_b(rr('Terminal: Inference chip (edge AI), data upload & model deployment', sz=1050)),
        pp(rr('■ Diversified Hardware Innovation', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Humanoid Robots (Core Focus)', sz=1050, color='0055B3')) +
        pp_b(rr('  Figure AI Helix: E2E, 7–9 Hz cognition + 200 Hz motion', sz=1000)) +
        pp_b(rr('  Unitree R1: ¥39,900, price competitiveness', sz=1000)) +
        pp_b(rr('  Apptronik Apollo + Google DeepMind', sz=1000)) +
        pp_e() +
        pp_b(rr('Quadruped / Collaborative Arms / Hybrid (Industrial)', sz=1050, color='1A4D1A')) +
        pp_b(rr('  Agility Digit: Amazon logistics collaboration', sz=1000)) +
        pp_e() +
        pp_b(rr('4 Body Subsystems: Sensing, Actuation, Power, Execution', sz=1050))
    ) +
    z5(SRC)
))

# ─── SLIDE 8: II-③ VLA Evolution ────────────────────────────────
save(8, sld(
    z1('II. Technology Trends', '③ VLA Evolution in Depth') +
    z2('End-to-end VLA is evolving along two architectural tracks — "unified single-system" and "layered dual-system" — with multi-modal fusion and reinforcement learning as the core improvement directions.') +
    z3('3. VLA Technology Evolution: Deep Analysis') +
    z4_2col(
        pp(rr('① Unified Single-System VLA', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('UniAct (Tsinghua): Heterogeneous-data universal action space; 4 control interfaces from only 100 demos', sz=1050)) +
        pp_b(rr('MLA (Peking Univ.): Full multi-sensor fusion — image, point cloud, tactile, language', sz=1050)) +
        pp_b(rr('GEN-0 (Generalist AI): Async time-step processing; rapid adaptation at 10B parameters', sz=1050)) +
        pp_e() +
        pp(rr('② Layered Dual-System', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Figure Helix: 7–9 Hz reasoning + 200 Hz motor control coordination', sz=1050)) +
        pp_b(rr('FiS (PKU·HKU·Zhifang): Fast execution system embedded in slow reasoning system; 117.7 Hz motion generation', sz=1050)),
        pp(rr('③ Multi-Modal Extension', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('ForceVLA (Fudan): Force-sensing mixture-of-experts fusion module FVLMoE', sz=1050)) +
        pp_b(rr('TLA (Samsung China): Tactile tokenization fed into LLM; tactile–visual–language integration', sz=1050)) +
        pp_e() +
        pp(rr('④ World Model Fusion', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('DreamVLA (SJTU): Predicts future environment states via world knowledge to assist action exploration', sz=1050)) +
        pp_b(rr('Ctrl-World (Tsinghua+Stanford): Task pre-play & virtual strategy scoring improve novel-task success rate', sz=1050)) +
        pp_e() +
        pp(rr('⑤ Reinforcement Learning Fusion', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('PI π*0.6: Expert correction guidance for error recovery; continuous success-rate improvement', sz=1050)) +
        pp_b(rr('RLinf (Tsinghua): Large-scale RL framework specialized for embodied AI', sz=1050))
    ) +
    z5(SRC)
))

# ─── SLIDE 9: III-① Robot Products ──────────────────────────────
save(9, sld(
    z1('III. Products & Applications', '① Robot Products') +
    z2('Humanoid robots have emerged as the flagship carrier of embodied AI. China and the US compete across three strategic camps: full-stack, hardware-focused, and software-brain-first. Unitree R1 at ¥39,900 has lowered the price barrier significantly.') +
    z3('1. Robots — The "Hottest" Embodied AI Carrier') +
    make_table(
        ['Camp', 'Representative Companies / Products', 'Key Characteristics'],
        [
            ['Full-Stack\n(In-house SW+HW)', 'Figure AI (Helix)\nZhiyuan (Go-1, Lingxi)', 'E2E model maximizes SW–HW synergy\nClosed-loop self-evolution'],
            ['Hardware-First\n(Body Design)', 'Unitree R1 (¥39,900)\nAgility Digit + Amazon\nApptronik Apollo + Google', 'Cost competitiveness + motion control algorithms\nEarly commercialization in logistics & manufacturing'],
            ['Software-Brain-First\n(Foundation Model)', 'Physical Intelligence π0.5\nField AI (FFMs)\nGalaxy General', 'Standard interface for cross-platform robot adaptation\nLow dev barrier, open-source strategy'],
        ],
        x=162800, y=1790000, cx=8818500, cy=2860000,
        col_widths=[2200000, 3200000, 3418500]
    ) +
    z5(SRC)
))

# ─── SLIDE 10: III-② Smart Transport & New Products ──────────────
save(10, sld(
    z1('IV. Smart Transport & New Products', 'Vehicles · Drones · Novel Devices') +
    z2('Autonomous vehicles and drones are the fastest-commercializing carriers of embodied AI, projected to form a combined $335.8B market by 2030. Novel products are penetrating unstructured environments through air–land–sea integration.') +
    z3('2. Smart Transport Equipment & Novel Products') +
    z4_2col(
        pp(rr('■ Autonomous Vehicles (L1–L3)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('2030 market: $172.2B (Grand View Research)', sz=1100)) +
        pp_b(rr('Structured environments (urban) → unstructured outdoor expansion', sz=1100)) +
        pp_b(rr('Tesla: Shares autonomy tech with humanoid robot Optimus', sz=1100)) +
        pp_e() +
        pp(rr('■ Drones & UAVs', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('2030 market: $163.6B', sz=1100)) +
        pp_b(rr('Expanding to aerial, underwater, and extreme environments', sz=1100)) +
        pp_b(rr('Swarm UAVs: Multi-agent collaboration in complex environments', sz=1100)),
        pp(rr('■ Novel Smart Products', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Shape-shifting mobile devices: Dynamic reconfiguration of structure & motion modes', sz=1100)) +
        pp_b(rr('Swarm micro-devices: Scalable, recombinant intelligent collectives', sz=1100)) +
        pp_b(rr('"Air–Land–Sea integration": Single-function → multi-space, multi-agent cooperation', sz=1100)) +
        pp_e() +
        pp(rr('■ Future "Smart Living Trio"', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Humanoid robots (home, industrial & medical services)', sz=1100)) +
        pp_b(rr('Autonomous vehicles (smart mobility)', sz=1100)) +
        pp_b(rr('Drones (logistics, exploration & extreme environments)', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 11: IV Industry Ecosystem ────────────────────────────
save(11, sld(
    z1('V. Industry Ecosystem', '352+ Companies · Supply Chain · Standardization') +
    z2('The embodied AI industrial chain is growing across 4 blocks — industry applications, product services, technology services, and infrastructure. China alone has formed an ecosystem of 352+ companies worth ¥73.5B.') +
    z3('1. Ecosystem Status & Key Challenges') +
    z4_2col(
        pp(rr('■ Ecosystem Scale (China)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Investment: 744 deals through Dec 2025, total ¥73.543B', sz=1100)) +
        pp_b(rr('Companies: 352+ (concentrated in Beijing, Shanghai, Shenzhen, Hangzhou)', sz=1100)) +
        pp_b(rr('4 blocks: Industry apps · Product services · Tech services · Infrastructure', sz=1100)) +
        pp_e() +
        pp(rr('■ Robot Arena Construction Boom', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Status: Marathons, competitions & athletic events drawing high public attention', sz=1100)) +
        pp_b(rr('Reality: Insufficient adaptation to complex unstructured environments', sz=1100)) +
        pp_b(rr('Challenge: Limited transfer from structured → unstructured environments', sz=1100)),
        pp(rr('■ Standards Framework Development', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('International: ITU-T F.748.66 embodied AI system standard established', sz=1100)) +
        pp_b(rr('Domestic: Industry standardization being rolled out in phases', sz=1100)) +
        pp_b(rr('Goal: Ensure technical interoperability and supply chain efficiency', sz=1100)) +
        pp_e() +
        pp(rr('■ Safety Issues (Key Barriers to Scale-up)', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Physical risk: Safety accidents from high-speed moving bodies', sz=1100)) +
        pp_b(rr('Data security: Handling personal data collected by sensors', sz=1100)) +
        pp_b(rr('Liability attribution: Legal responsibility in AI misjudgment cases unclear', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 12: V Future Outlook ──────────────────────────────────
save(12, sld(
    z1('VI. Future Outlook', '$339.8B Market · Tech Roadmap · Implications') +
    z2('Embodied AI will advance along three directions: architectural reinvention, application deepening, and safety & ethics framework — forming a $339.8B market by 2030.') +
    z3('Three Development Directions') +
    z4(
        pp(rr('① Architectural Reinvention: "Stacked Function Modules" → "Multi-modal Cognitive Fusion"', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('World models simulate physics in the AI brain → optimizing action pre-play and motion prediction', sz=1100)) +
        pp_b(rr('Next step after LLM→VLM→VLA evolution: World model-based autonomous growth AI', sz=1100)) +
        pp_b(rr('Multi-modal perception: Unified fusion of vision + language + tactile + force + point cloud', sz=1100)) +
        pp_e() +
        pp(rr('② Application Deepening: "Demonstration" → "Practical Deployment"', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('Factory & warehouse → Home, medical & education → Special & extreme environments', sz=1100)) +
        pp_b(rr('"Custom development" → "Standardized delivery" → "Secondary development" closed loop completed', sz=1100)) +
        pp_b(rr('Humanoid robot ChatGPT moment: Mass-market inflection point for general humanoids imminent', sz=1100)) +
        pp_e() +
        pp(rr('③ Safety & Ethics: "Compliance" → "Ethical Cooperative Framework" Full Deployment', sz=1300, bold=True, color='1A3A6B')) +
        pp_b(rr('4 core issues: Functional safety · cybersecurity · liability attribution · privacy protection', sz=1100)) +
        pp_b(rr('Race for international standards leadership: Competition intensifying in ITU, ISO and beyond', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 13: Devil's Advocate ──────────────────────────────────
save(13, sld(
    z1("VII. Devil's Advocate", '5 Critical Perspectives') +
    z2("Despite the hype, Embodied AI faces 5 unresolved structural challenges: VLA generalization failures, long-horizon task success rates of only 20–40%, incomplete SW–HW coordination, data scarcity, and prohibitive costs.") +
    z3("5 Critical Structural Challenges") +
    z4(
        pp_b(rr('① VLA Generalization Failure: Performance drops sharply outside training distribution. 1X World Model & PI π0.5 show dramatically lower success in novel situations. Structural limitation in covering real-world complexity.', sz=1100)) +
        pp_e() +
        pp_b(rr('② Long-Horizon Tasks 20–40%: Success rate of Google Gemini Robotics-ER 1.5 + VLA on "garbage sorting" and "item exchange" long-horizon tasks. High-level planning (1–10 Hz) vs. low-level control (100 Hz+) timescale mismatch.', sz=1100)) +
        pp_e() +
        pp_b(rr('③ Incomplete SW–HW Coordination: Multi-timescale cooperative control required. Task failure if any link becomes unstable. Cross-body transfer fails to reproduce performance.', sz=1100)) +
        pp_e() +
        pp_b(rr('④ Data Scarcity & Sim-to-Real Gap: Real-body data depends on arenas. Simulation synthesis fails to resolve the virtual–real divide. Collection-to-use strategy still undefined.', sz=1100)) +
        pp_e() +
        pp_b(rr('⑤ High Cost & Lack of Standardization: System prices remain prohibitively high. Custom-build structure constrains mass production. Incompatibility delays supply chain optimization.', sz=1100))
    ) +
    z5(SRC)
))

# ─── SLIDE 5: CLOSING (sldIdLst가 마지막으로 이동시켜 최종 페이지가 됨) ──
# build_pptx.sh 가 sldIdLst에서 rId10(slide5)을 마지막으로 이동시킨다.
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
          {rr("Thank You.", sz=4000, bold=True, color='1A3A6B')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="11" name="closing_bullets"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="1200000" y="1500000"/><a:ext cx="6744000" cy="1500000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="t" bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"><a:noAutofit/></a:bodyPr>
        <a:lstStyle/>
        <a:p><a:pPr algn="l" marL="300000" indent="-300000"><a:buChar char="●"/></a:pPr>
          {rr('Feel free to share widely. Please credit the source when using.', sz=1500)}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="l" marL="300000" indent="-300000"><a:buChar char="●"/></a:pPr>
          {rr('This report is designed for learning and sharing insights on AI trends.', sz=1500)}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="l" marL="300000" indent="-300000"><a:buChar char="●"/></a:pPr>
          {rr('For inquiries or collaboration, please reach out anytime.', sz=1500)}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="12" name="closing_contact"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="0" y="3200000"/><a:ext cx="9144000" cy="1200000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>{rr('Dong Hyung Shin', sz=2000, bold=True, color='1A3A6B')}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>{rr('+82-10-2202-8761', sz=1800, color='555555')}<a:endParaRPr/></a:p>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>{rr('donghyung.shin@gmail.com', sz=1800, color='555555')}<a:endParaRPr/></a:p>
      </p:txBody></p:sp>
    <p:sp><p:nvSpPr><p:cNvPr id="13" name="closing_quote"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="162800" y="4480000"/><a:ext cx="8818500" cy="400000"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>
          {rr('"Use it freely, share widely. Just remember — always credit the source."', sz=1300, color='888888')}
        <a:endParaRPr/></a:p>
      </p:txBody></p:sp>
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''

with open(f'{SLIDES}/slide5.xml', 'w', encoding='utf-8') as f:
    f.write(closing_xml)
print('  slide5.xml (Thank You) saved')

print("\n✅ All English slides saved!")
print("Slide mapping (final order via sldIdLst):")
print("  1=Cover, 2=Contents, 3=I-①Concepts, 4=I-②Global")
print("  5=II-①Algorithms, 6=II-②Data/Hardware, 7=II-③VLA")
print("  8=III-①Robots, 9=IV.Smart Transport")
print("  10=V.Ecosystem, 11=VI.Outlook, 12=VII.Devil's Advocate")
print("  13=Thank You (sldIdLst last)")
