# PPTX 빌드 파이프라인 v0.4 (Build Pipeline)

## ★ CRITICAL BUG FIX — 반드시 준수

### ⓪ Google Slides 잔존물 제거 (v0.4 신규, PowerPoint "읽을 수 없습니다" 원인 #2)

일부 TEMPLATE.pptx는 과거 Google Slides에서 export된 이력이 있어 다음 요소가 숨어 있습니다:

- `ppt/presentation.xml` 끝 `<p:extLst>` 안 `<p:ext uri="GoogleSlidesCustomDataVersion2">`
- `ppt/_rels/presentation.xml.rels` 의 `Type="http://customschemas.google.com/relationships/presentationmetadata"`
- `[Content_Types].xml` 의 `Override PartName="/ppt/metadata"`
- `ppt/metadata` (Google ARC binary)

**증상**: LibreOffice / python-pptx / `unzip -t` 모두 통과하는데 Microsoft PowerPoint만 "읽을 수 없습니다" 에러.

**해결**: `pack.py` 호출 **직전**에 반드시:

```bash
python3 references/strip_google_extensions.py --unpacked unpacked_kr/
python3 references/strip_google_extensions.py --unpacked unpacked_en/
```

이 단계는 `clean.py` 다음, `pack.py` 이전이어야 합니다.

**검증**:
```bash
unzip -p final.pptx ppt/presentation.xml | grep -c 'customooxmlschemas.google\|customschemas.google'
# 반드시 0 이어야 함
```

---

### ① `<p:ph>` 절대 사용 금지 (PowerPoint "읽을 수 없습니다" 원인 #1)

Zone 헬퍼의 `<p:nvPr>` 안에 `<p:ph .../>` 를 넣으면, 한 슬라이드에 title 플레이스홀더가
여러 개 선언되어 PowerPoint가 OOXML 검증 실패로 파일 자체를 거부합니다.

```python
# ❌ 절대 금지 — 파일 손상 (PowerPoint 열기 오류)
<p:nvPr><p:ph type="title"/></p:nvPr>
<p:nvPr><p:ph idx="3" type="title"/></p:nvPr>

# ✅ 올바름 — 빈 nvPr 사용 (순수 텍스트 박스)
<p:nvPr/>
```

### ② `rr()` 함수에 `u='none'` 기본값 필수

slideLayout5의 `defRPr`에 `u="sng"`가 있어 모든 텍스트가 밑줄을 상속받습니다.
`u="none"`을 명시하지 않으면 Zone 3 소주제에 원하지 않는 밑줄이 생깁니다.

```python
# ✅ 올바른 rr() — u='none' 기본값
def rr(text, sz=None, bold=False, color=None, lang='ko', u='none'):
    sz_a = f' sz="{sz}"' if sz else ''
    b_a  = ' b="1"' if bold else ''
    u_a  = f' u="{u}"' if u else ''
    col  = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if color else ''
    return f'<a:r><a:rPr lang="{lang}"{sz_a}{b_a}{u_a} dirty="0">{col}</a:rPr><a:t>{esc(text)}</a:t></a:r>'
```

---

## 빌드 절차 개요

```bash
# STEP 0 — 경로 동적 탐색 (반드시 먼저 실행, 세션마다 경로 달라짐)
PPTX_SKILL=$(find /sessions -maxdepth 5 -name "pptx" -type d -path "*/skills/*" 2>/dev/null | head -1)
TEMPLATE=$(find /sessions -maxdepth 6 -name "TEMPLATE*.pptx" 2>/dev/null | head -1)
echo "PPTX_SKILL=$PPTX_SKILL  TEMPLATE=$TEMPLATE"

# 1. 템플릿 언팩
python3 "$PPTX_SKILL/scripts/office/unpack.py" "$TEMPLATE" unpacked_kr/

# 2. 슬라이드 추가 등록
python3 "$PPTX_SKILL/scripts/add_slide.py" unpacked_kr/ --count {N}

# 3. 레이아웃 rels 설정 (슬라이드 종류별)
#   slideLayout1 = cover
#   slideLayout2 = 맺음말(Closing)
#   slideLayout3 = 챕터 구분 슬라이드
#   slideLayout4 = INDEX
#   slideLayout5 = default_contents (★ 본문 슬라이드)

# 4. Python으로 슬라이드 XML 생성 및 저장
python3 build_slides.py

# 5. 클린업 및 패키징
python3 "$PPTX_SKILL/scripts/clean.py" unpacked_kr/
python3 "$PPTX_SKILL/scripts/office/pack.py" unpacked_kr/ Output_KR.pptx --original "$TEMPLATE"

# 6. 검증
unzip -t Output_KR.pptx | tail -3
```

---

## 기본 헬퍼 함수 (검증된 v0.2)

```python
def esc(t):
    return str(t).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def rr(text, sz=None, bold=False, color=None, lang='ko', u='none'):
    sz_a = f' sz="{sz}"' if sz else ''
    b_a  = ' b="1"' if bold else ''
    u_a  = f' u="{u}"' if u else ''
    col  = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if color else ''
    return f'<a:r><a:rPr lang="{lang}"{sz_a}{b_a}{u_a} dirty="0">{col}</a:rPr><a:t>{esc(text)}</a:t></a:r>'

def pp(*runs, algn='l', spc_bef=80, spc_aft=80):
    return (f'<a:p><a:pPr algn="{algn}"><a:spcBef><a:spcPts val="{spc_bef}"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="{spc_aft}"/></a:spcAft><a:buNone/></a:pPr>'
            f'{"".join(runs)}<a:endParaRPr/></a:p>')

def pp_bullet(*runs, spc=60):
    return (f'<a:p><a:pPr marL="228600" indent="-228600">'
            f'<a:spcBef><a:spcPts val="{spc}"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="{spc}"/></a:spcAft>'
            f'<a:buChar char="•"/></a:pPr>'
            f'{"".join(runs)}<a:endParaRPr/></a:p>')

def pp_empty():
    return '<a:p><a:pPr><a:spcBef><a:spcPts val="100"/></a:spcBef><a:spcAft><a:spcPts val="0"/></a:spcAft><a:buNone/></a:pPr><a:endParaRPr/></a:p>'

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
      'xmlns:mv="urn:schemas-microsoft-com:mac:vml" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
      'xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" '
      'xmlns:o="urn:schemas-microsoft-com:office:office" '
      'xmlns:v="urn:schemas-microsoft-com:vml" '
      'xmlns:pvml="urn:schemas-microsoft-com:office:powerpoint" '
      'xmlns:com="http://schemas.openxmlformats.org/drawingml/2006/compatibility" '
      'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" '
      'xmlns:p15="http://schemas.microsoft.com/office/powerpoint/2012/main" '
      'xmlns:ahyp="http://schemas.microsoft.com/office/drawing/2018/hyperlinkcolor"')

def sld_wrap(spTree):
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<p:sld {NS}>\n'
            f'  <p:cSld><p:spTree>\n'
            f'    <p:nvGrpSpPr><p:cNvPr id="1" name="Group 1"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>\n'
            f'    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            f'<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>\n'
            f'{spTree}\n'
            f'  </p:spTree></p:cSld>\n'
            f'  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>\n'
            f'</p:sld>')
```

---

## Zone 헬퍼 함수 (★ ph 완전 제거 v0.2)

```python
def zone_hdr(left_text, right_text, lang='ko'):
    """Zone 1 — 섹션 헤더. ⚠️ ph 없음, nvPr 빈 값"""
    return (
        f'    <p:sp><p:nvSpPr><p:cNvPr id="10" name="zone1L"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="162800" y="264100"/><a:ext cx="5100900" cy="220800"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr anchorCtr="0" anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>'
        f'<a:lstStyle/>'
        f'<a:p><a:pPr algn="l"><a:spcBef><a:spcPts val="0"/></a:spcBef>'
        f'<a:spcAft><a:spcPts val="0"/></a:spcAft><a:buNone/></a:pPr>'
        f'{rr(left_text, sz=1800, bold=True, color="1A3A6B", lang=lang)}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>\n'
        f'    <p:sp><p:nvSpPr><p:cNvPr id="11" name="zone1R"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="4039250" y="264100"/><a:ext cx="4941900" cy="220800"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr anchorCtr="0" anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square"/>'
        f'<a:lstStyle/>'
        f'<a:p><a:pPr algn="r"><a:spcBef><a:spcPts val="0"/></a:spcBef>'
        f'<a:spcAft><a:spcPts val="0"/></a:spcAft><a:buNone/></a:pPr>'
        f'{rr(right_text, sz=1700, color="1A3A6B", lang=lang)}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>'
    )

def zone_keymsg(msg, lang='ko'):
    """Zone 2 — KEY MESSAGE. ⚠️ ph 없음, nvPr 빈 값"""
    return (
        f'    <p:sp><p:nvSpPr><p:cNvPr id="12" name="zone2_keymsg"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="162725" y="641800"/><a:ext cx="8818500" cy="669300"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr anchorCtr="0" anchor="ctr" bIns="0" lIns="0" rIns="0" tIns="0" wrap="square">'
        f'<a:noAutofit/></a:bodyPr><a:lstStyle/>'
        f'<a:p><a:pPr algn="l"><a:spcBef><a:spcPts val="0"/></a:spcBef>'
        f'<a:spcAft><a:spcPts val="0"/></a:spcAft><a:buNone/></a:pPr>'
        f'{rr(msg, sz=1500, lang=lang)}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>'
    )

def zone_subhd(heading, lang='ko'):
    """Zone 3 — 소주제 제목. 중앙정렬, navy bold, 밑줄(u=sng), fill 없음.
    ⚠️ ph 없음, solidFill 배경 금지, 별도 밑줄 사각형 추가."""
    return (
        f'    <p:sp><p:nvSpPr><p:cNvPr id="13" name="zone3_subhd"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="162800" y="1455150"/><a:ext cx="8818500" cy="343500"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr anchor="ctr" bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square"/>'
        f'<a:lstStyle/>'
        f'<a:p><a:pPr algn="ctr"><a:spcBef><a:spcPts val="0"/></a:spcBef>'
        f'<a:spcAft><a:spcPts val="0"/></a:spcAft><a:buNone/></a:pPr>'
        f'{rr(heading, sz=1600, bold=True, color="1A3A6B", lang=lang, u="sng")}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>\n'
        f'    <p:sp><p:nvSpPr><p:cNvPr id="130" name="zone3_underline"/>'
        f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="162800" y="1773900"/><a:ext cx="8818500" cy="25400"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:solidFill><a:srgbClr val="1A3A6B"/></a:solidFill>'
        f'<a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/></p:txBody></p:sp>'
    )

def zone_body(paragraphs_xml, top=1850000, height=2780000, lang='ko'):
    """Zone 4 — 단일 본문. ⚠️ ph 없음"""
    return (
        f'    <p:sp><p:nvSpPr><p:cNvPr id="14" name="zone4_body"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="162800" y="{top}"/><a:ext cx="8818500" cy="{height}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square">'
        f'<a:noAutofit/></a:bodyPr><a:lstStyle/>'
        f'{paragraphs_xml}'
        f'</p:txBody></p:sp>'
    )

def zone_body2col(left_xml, right_xml, top=1850000, lang='ko'):
    """Zone 4 — 2단 분할. ⚠️ ph 없음"""
    return (
        f'    <p:sp><p:nvSpPr><p:cNvPr id="14" name="zone4_left"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="162800" y="{top}"/><a:ext cx="4300000" cy="2780000"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square">'
        f'<a:noAutofit/></a:bodyPr><a:lstStyle/>{left_xml}</p:txBody></p:sp>\n'
        f'    <p:sp><p:nvSpPr><p:cNvPr id="15" name="zone4_right"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="4680000" y="{top}"/><a:ext cx="4300000" cy="2780000"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square">'
        f'<a:noAutofit/></a:bodyPr><a:lstStyle/>{right_xml}</p:txBody></p:sp>'
    )

def zone_src(src, lang='ko'):
    """Zone 5 — Source 출처. ⚠️ ph 없음"""
    prefix = '※ Source : ' if lang == 'ko' else 'Source: '
    return (
        f'    <p:sp><p:nvSpPr><p:cNvPr id="99" name="zone5_src"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="104375" y="4715475"/><a:ext cx="8938800" cy="130000"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>'
        f'<a:lstStyle/>'
        f'<a:p><a:pPr><a:buNone/></a:pPr>'
        f'{rr(prefix + src, sz=800, color="888888", lang=lang)}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>'
    )

def text_col(x, y, cx, cy, content_xml, id_num=14, name='col'):
    """독립 텍스트 박스. ⚠️ ph 없음"""
    return (
        f'    <p:sp><p:nvSpPr><p:cNvPr id="{id_num}" name="{name}"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr bIns="45720" lIns="91440" rIns="91440" tIns="45720" wrap="square">'
        f'<a:noAutofit/></a:bodyPr><a:lstStyle/>'
        f'{content_xml}'
        f'</p:txBody></p:sp>'
    )
```

---

## 슬라이드 저장 패턴

```python
import os

SLIDES_DIR = 'unpacked_kr/ppt/slides'

def save_slide(n, xml):
    with open(os.path.join(SLIDES_DIR, f'slide{n}.xml'), 'w', encoding='utf-8') as f:
        f.write(xml)

# 예시: 본문 슬라이드
save_slide(3, sld_wrap(
    zone_hdr('Chapter I. 개요 및 배경', 'I-1', lang='ko') +
    zone_keymsg('구현 AI는 물리 세계 AI의 임계점에 도달하고 있음.', lang='ko') +
    zone_subhd('1.1 연구 배경', lang='ko') +
    zone_body(
        pp(rr('배경 텍스트', sz=1200, lang='ko')) +
        pp_bullet(rr('핵심 사실 1', sz=1100, lang='ko')),
        lang='ko'
    ) +
    zone_src('출처 기관, 발행일', lang='ko')
))
```

---

## 표지 슬라이드 XML 패턴

```python
def make_cover(title, subtitle, date, author, lang='ko'):
    font_lang = lang if lang == 'ko' else 'en-US'
    return sld_wrap(
        f'    <p:sp><p:nvSpPr><p:cNvPr id="10" name="title"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="457200" y="914400"/><a:ext cx="8229600" cy="1371600"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>'
        f'<a:lstStyle/>'
        f'<a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>'
        f'{rr(title, sz=3600, bold=True, lang=font_lang)}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>\n'
        f'    <p:sp><p:nvSpPr><p:cNvPr id="11" name="subtitle"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="457200" y="2286000"/><a:ext cx="8229600" cy="457200"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>'
        f'<a:lstStyle/>'
        f'<a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>'
        f'{rr(subtitle, sz=2000, lang=font_lang)}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>\n'
        f'    <p:sp><p:nvSpPr><p:cNvPr id="12" name="meta"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="457200" y="2857500"/><a:ext cx="8229600" cy="457200"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr anchor="ctr" bIns="0" lIns="91440" rIns="91440" tIns="0" wrap="square"/>'
        f'<a:lstStyle/>'
        f'<a:p><a:pPr algn="ctr"><a:buNone/></a:pPr>'
        f'{rr(date + "  |  " + author, sz=1600, color="555555", lang=font_lang)}<a:endParaRPr/></a:p>'
        f'</p:txBody></p:sp>'
    )
```

---

## 결과물 저장 경로

```bash
WORKSPACE=$(find /sessions -maxdepth 4 -type d -name "ClaudeCoworkFile" 2>/dev/null | head -1)
echo "WORKSPACE=$WORKSPACE"
cp {주제}_KR_Presentation_{날짜}.pptx "$WORKSPACE/"
cp {주제}_EN_Presentation_{날짜}.pptx "$WORKSPACE/"
```
