#!/usr/bin/env bash
# build_pptx.sh — 정본 PPTX 빌드 오케스트레이터
#
# 이 스크립트는 KR 또는 EN PPTX 한 개를 처음부터 끝까지 결정론적으로 빌드한다.
# 모델(Opus/Sonnet)이 unpack/add_slide/sldIdLst/strip/pack 단계를 잘못 짜는 일을
# 막기 위해, 모든 OOXML 조작을 이 스크립트가 수행한다.
#
# 사용법:
#   bash references/build_pptx.sh kr build_pptx_kr.py EmbodiedAI_KR_Presentation_20260408.pptx
#   bash references/build_pptx.sh en build_pptx_en.py EmbodiedAI_EN_Presentation_20260408.pptx
#
# 인자:
#   $1 = 언어 (kr | en) — unpacked_kr/ 또는 unpacked_en/ 디렉터리명에 사용
#   $2 = 빌드 스크립트 경로 — Zone helper로 슬라이드 XML을 작성하는 파이썬 스크립트
#   $3 = 출력 .pptx 파일명
#
# 환경 변수 (옵션):
#   PPTX_SKILL — pptx 스킬 디렉터리 (자동탐색 가능)
#   TEMPLATE   — TEMPLATE.pptx 경로 (자동탐색 가능, 본 스킬의 references/TEMPLATE.pptx 우선)
#   N_CONTENT  — 본문 슬라이드 수 (기본 8 → 총 13장)
#
set -euo pipefail

LANG_CODE="${1:?Usage: build_pptx.sh <kr|en> <build_script.py> <output.pptx>}"
BUILD_PY="${2:?build script path required}"
OUTPUT="${3:?output filename required}"
N_CONTENT="${N_CONTENT:-8}"

# ── 0. 경로 자동 탐색 ──────────────────────────────────────────────
if [ -z "${PPTX_SKILL:-}" ]; then
  PPTX_SKILL=$(find /sessions -maxdepth 6 -name "pptx" -type d -path "*/skills/*" 2>/dev/null | head -1 || true)
fi
[ -d "$PPTX_SKILL" ] || { echo "ERROR: pptx skill not found. Set PPTX_SKILL env var."; exit 2; }

# TEMPLATE 우선순위: 환경변수 > 본 스킬의 references/TEMPLATE.pptx > 사용자 업로드
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${TEMPLATE:-}" ]; then
  if [ -f "$SKILL_DIR/TEMPLATE.pptx" ]; then
    TEMPLATE="$SKILL_DIR/TEMPLATE.pptx"
  else
    TEMPLATE=$(find /sessions -maxdepth 6 -name "TEMPLATE*.pptx" 2>/dev/null | head -1 || true)
  fi
fi
[ -f "$TEMPLATE" ] || { echo "ERROR: TEMPLATE.pptx not found. Set TEMPLATE env var."; exit 2; }

STRIP="$SKILL_DIR/strip_google_extensions.py"
VERIFY="$SKILL_DIR/verify_toc.py"
[ -f "$STRIP" ]  || { echo "ERROR: $STRIP not found"; exit 2; }
[ -f "$VERIFY" ] || { echo "ERROR: $VERIFY not found"; exit 2; }

UNPACKED="unpacked_${LANG_CODE}"

echo "═══════════════════════════════════════════════════════════════"
echo "  build_pptx.sh — $LANG_CODE → $OUTPUT"
echo "  PPTX_SKILL = $PPTX_SKILL"
echo "  TEMPLATE   = $TEMPLATE"
echo "  BUILD_PY   = $BUILD_PY"
echo "  UNPACKED   = $UNPACKED"
echo "═══════════════════════════════════════════════════════════════"

# ── 1. 클린 unpack ────────────────────────────────────────────────
rm -rf "$UNPACKED"
python3 "$PPTX_SKILL/scripts/office/unpack.py" "$TEMPLATE" "$UNPACKED/" | tail -1

# ── 2. N_CONTENT개 슬라이드 추가 (slideLayout5 = contents) ────────
for i in $(seq 1 "$N_CONTENT"); do
  python3 "$PPTX_SKILL/scripts/add_slide.py" "$UNPACKED/" slideLayout5.xml >/dev/null 2>&1 || true
done

# ── 3. presentation.xml 보정: sldIdLst에 새 sldId 추가 + 맺음말(rId10) 마지막으로 이동 ──
python3 - "$UNPACKED" "$N_CONTENT" << 'PY'
import re, sys
unpacked, n_content = sys.argv[1], int(sys.argv[2])
p = f'{unpacked}/ppt/presentation.xml'
with open(p) as f: x = f.read()

# 새 sldId 엔트리 추가 (id 261-26{N+0}, rId 12-1{N+1})
new_ids = ''.join(f'<p:sldId id="{261+i}" r:id="rId{12+i}"/>' for i in range(n_content))
if new_ids not in x:
    x = x.replace('</p:sldIdLst>', new_ids + '</p:sldIdLst>')

# 맺음말(rId10) 슬라이드를 sldIdLst의 마지막으로 이동
m = re.search(r'<p:sldIdLst>(.*?)</p:sldIdLst>', x, re.DOTALL)
if m:
    ids = re.findall(r'<p:sldId [^/]*/>', m.group(1))
    closing = [s for s in ids if 'rId10' in s]
    if closing:
        others = [s for s in ids if 'rId10' not in s]
        new_inner = ''.join(others) + closing[0]
        x = x.replace(m.group(0), f'<p:sldIdLst>{new_inner}</p:sldIdLst>')

with open(p, 'w') as f: f.write(x)
print(f'  presentation.xml: +{n_content} sldIds, closing slide moved to last')
PY

# ── 4. slide3.xml.rels 레이아웃 보정: layout3(divider) → layout5(contents) ──
SLIDE3_RELS="$UNPACKED/ppt/slides/_rels/slide3.xml.rels"
if [ -f "$SLIDE3_RELS" ] && grep -q 'slideLayout3.xml' "$SLIDE3_RELS"; then
  sed -i 's|slideLayouts/slideLayout3.xml|slideLayouts/slideLayout5.xml|' "$SLIDE3_RELS"
  echo "  slide3.xml.rels: layout3 → layout5"
fi

# ── 5. 빌드 스크립트 실행 (사용자 작성 콘텐츠 → slide{N}.xml) ──
echo "─── Running $BUILD_PY ───"
TARGET_UNPACKED="$UNPACKED" python3 "$BUILD_PY"

# ── 6. TOC ↔ 본문 검증 ───────────────────────────────────────────
echo "─── verify_toc.py ───"
python3 "$VERIFY" "$UNPACKED"
# verify_toc.py가 실패하면 set -e가 빌드를 중단시킴

# ── 7. clean.py (참조되지 않는 파일 제거) ─────────────────────────
python3 "$PPTX_SKILL/scripts/clean.py" "$UNPACKED/" >/dev/null 2>&1 || true

# ── 8. ★ Google Slides 잔존물 제거 (pack 직전 필수) ──────────────
python3 "$STRIP" --unpacked "$UNPACKED/" 2>&1 | tail -5

# ── 9. pack ───────────────────────────────────────────────────────
python3 "$PPTX_SKILL/scripts/office/pack.py" "$UNPACKED/" "$OUTPUT" --original "$TEMPLATE" 2>&1 | tail -3

# ── 10. 최종 검증 ─────────────────────────────────────────────────
GOOGLE_LEFT=$(unzip -p "$OUTPUT" ppt/presentation.xml 2>/dev/null | grep -c 'customschemas\.google\|customooxmlschemas\.google' || true)
META_LEFT=$(unzip -l "$OUTPUT" 2>/dev/null | grep -c 'ppt/metadata' || true)
SIZE=$(stat -c%s "$OUTPUT")

if [ "$GOOGLE_LEFT" -ne 0 ] || [ "$META_LEFT" -ne 0 ]; then
  echo "❌ FAIL: Google leftovers ($GOOGLE_LEFT) or metadata ($META_LEFT) still present"
  exit 1
fi

unzip -t "$OUTPUT" >/dev/null 2>&1 && echo "✅ $OUTPUT  ($SIZE bytes)  Google clean, zip OK"
