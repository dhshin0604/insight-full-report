#!/usr/bin/env bash
# build_pptx.sh — 정본 PPTX 빌드 오케스트레이터 (v0.9.3)
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
#   PPTX_SKILL    — pptx 스킬 디렉터리 (자동탐색 가능, 아래 "pptx 스킬 호환" 참조)
#   TEMPLATE      — TEMPLATE.pptx 경로 (자동탐색 가능, 본 스킬의 references/TEMPLATE.pptx 우선)
#   N_CONTENT     — 본문 슬라이드 수 (기본 8 → 총 13장)
#   PROFILE       — profile.json 경로 (미지정 시 자동 선택: ./profile.json > references/profile.json)
#   LOGO          — 표지 로고 PNG 경로 (미지정 시 references/logo.png, 없으면 템플릿 기본 이미지)
#   SKIP_VALIDATE — 1 이면 pack 뒤 validate.py 검증을 건너뜀 (기본: 검증하고 실패 시 중단)
#
# 프로필 자동 적용: 슬라이드 작성 직후 references/apply_profile.py 가 unpacked/ppt 전체
# (슬라이드 + 레이아웃 하단 크레딧)의 {AUTHOR_KR} {AUTHOR_EN} {PHONE_KR} {PHONE_EN} {EMAIL}
# 를 profile.json 값으로 치환한다. 값이 비어 플레이스홀더가 남으면 빌드를 중단한다.
#
# pptx 스킬 호환 (v0.9.3):
#   Anthropic pptx 스킬 2026-10 판은 scripts/office/unpack.py · pack.py 를 더 제공하지 않고,
#   add_slide.py 가 <p:sldIdLst> 등록까지 직접 수행한다. 이 스크립트는 두 세대를 모두 지원한다.
#   - unpack/pack : 스킬에 unpack.py·pack.py 가 둘 다 있으면 그것을 쓰고(legacy), 없으면 내장
#                   zipfile 구현을 쓴다(builtin). 내장 pack 은 [Content_Types].xml 을 첫 항목으로 쓴다.
#   - sldIdLst    : "이미 등록된 슬라이드는 그대로, 빠진 슬라이드만 추가, 중복·고아는 제거" 방식이라
#                   add_slide.py 가 등록을 하든 안 하든 결과가 같다.
#   - PPTX_SKILL  : 환경변수 > /mnt/skills/public/pptx > ~/.claude/skills/synced/*/pptx
#                   > /mnt/skills/*/pptx > /sessions/*/.../skills/pptx 순으로 탐색한다.
#   - validate    : 스킬에 scripts/office/validate.py 가 있으면 pack 뒤 `--original TEMPLATE` 로
#                   스키마·관계·콘텐츠타입을 검증한다 (실패 시 중단, SKIP_VALIDATE=1 로 해제).
#
set -euo pipefail

LANG_CODE="${1:?Usage: build_pptx.sh <kr|en> <build_script.py> <output.pptx>}"
BUILD_PY="${2:?build script path required}"
OUTPUT="${3:?output filename required}"
N_CONTENT="${N_CONTENT:-8}"

# ── 0. 경로 자동 탐색 ──────────────────────────────────────────────
find_pptx_skill() {
  local c
  for c in "${PPTX_SKILL:-}" /mnt/skills/public/pptx "$HOME"/.claude/skills/synced/*/pptx /mnt/skills/*/pptx; do
    if [ -n "$c" ] && [ -f "$c/scripts/add_slide.py" ]; then echo "$c"; return 0; fi
  done
  # 구형 Cowork 세션 레이아웃 (/sessions/<id>/mnt/.../skills/pptx)
  c=$(find /sessions -maxdepth 7 -name "add_slide.py" -path "*/pptx/scripts/*" 2>/dev/null | head -1 || true)
  if [ -n "$c" ]; then dirname "$(dirname "$c")"; return 0; fi
  return 1
}
PPTX_SKILL="$(find_pptx_skill || true)"
[ -n "$PPTX_SKILL" ] && [ -f "$PPTX_SKILL/scripts/add_slide.py" ] && [ -f "$PPTX_SKILL/scripts/clean.py" ] \
  || { echo "ERROR: pptx skill not found (scripts/add_slide.py, scripts/clean.py 필요). Set PPTX_SKILL env var."; exit 2; }

# unpack/pack 모드: 스킬 구판(unpack.py·pack.py 보유) 이면 legacy, 아니면 내장 zipfile 구현
UNPACK_PY="$PPTX_SKILL/scripts/office/unpack.py"
PACK_PY="$PPTX_SKILL/scripts/office/pack.py"
VALIDATE_PY="$PPTX_SKILL/scripts/office/validate.py"
if [ -f "$UNPACK_PY" ] && [ -f "$PACK_PY" ]; then OOXML_MODE="legacy (skill unpack.py/pack.py)"; else OOXML_MODE="builtin (zipfile)"; fi

# TEMPLATE 우선순위: 환경변수 > 본 스킬의 references/TEMPLATE.pptx > 사용자 업로드
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${TEMPLATE:-}" ]; then
  if [ -f "$SKILL_DIR/TEMPLATE.pptx" ]; then
    TEMPLATE="$SKILL_DIR/TEMPLATE.pptx"
  else
    TEMPLATE=$(find /sessions /mnt/user-data . -maxdepth 6 -name "TEMPLATE*.pptx" 2>/dev/null | head -1 || true)
  fi
fi
[ -f "$TEMPLATE" ] || { echo "ERROR: TEMPLATE.pptx not found. Set TEMPLATE env var."; exit 2; }

STRIP="$SKILL_DIR/strip_google_extensions.py"
VERIFY="$SKILL_DIR/verify_toc.py"
APPLY_PROFILE="$SKILL_DIR/apply_profile.py"
LOGO="${LOGO:-$SKILL_DIR/logo.png}"
[ -f "$STRIP" ]  || { echo "ERROR: $STRIP not found"; exit 2; }
[ -f "$VERIFY" ] || { echo "ERROR: $VERIFY not found"; exit 2; }
[ -f "$APPLY_PROFILE" ] || { echo "ERROR: $APPLY_PROFILE not found"; exit 2; }
# 프로필 파일 자동 선택: PROFILE 환경변수 > ./profile.json(작업 폴더) > references/profile.json
PROFILE="$(python3 "$APPLY_PROFILE" --which)"

UNPACKED="unpacked_${LANG_CODE}"

echo "═══════════════════════════════════════════════════════════════"
echo "  build_pptx.sh v0.9.3 — $LANG_CODE → $OUTPUT"
echo "  PPTX_SKILL = $PPTX_SKILL"
echo "  OOXML      = $OOXML_MODE"
echo "  TEMPLATE   = $TEMPLATE"
echo "  PROFILE    = $PROFILE"
echo "  LOGO       = $([ -f "$LOGO" ] && echo "$LOGO" || echo "(none — 템플릿 기본 이미지 유지)")"
echo "  BUILD_PY   = $BUILD_PY"
echo "  UNPACKED   = $UNPACKED"
echo "═══════════════════════════════════════════════════════════════"

# ── 1. 클린 unpack ────────────────────────────────────────────────
rm -rf "$UNPACKED"
if [ -f "$UNPACK_PY" ] && [ -f "$PACK_PY" ]; then
  python3 "$UNPACK_PY" "$TEMPLATE" "$UNPACKED/" | tail -1
else
  python3 - "$TEMPLATE" "$UNPACKED" << 'PY'
import os, sys, zipfile
src, dst = sys.argv[1], sys.argv[2]
root = os.path.realpath(dst)
with zipfile.ZipFile(src) as z:
    for info in z.infolist():
        target = os.path.realpath(os.path.join(dst, info.filename))
        if target != root and not target.startswith(root + os.sep):
            sys.exit(f'ERROR: unsafe path in template zip: {info.filename}')
    z.extractall(dst)
n = sum(len(fs) for _, _, fs in os.walk(dst))
print(f'  unpack: {n} parts → {dst}/')
PY
fi

# ── 1b. 로고 훅: references/logo.png (또는 LOGO=경로) 가 있으면 표지 레이아웃 이미지 교체 ──
if [ -f "$LOGO" ] && [ -f "$UNPACKED/ppt/media/image1.png" ]; then
  cp "$LOGO" "$UNPACKED/ppt/media/image1.png"
  echo "  logo: ppt/media/image1.png ← $LOGO"
fi

# ── 2. N_CONTENT개 슬라이드 추가 (slideLayout5 = contents) ────────
# 신판 add_slide.py 는 content type·rels·sldIdLst 를 모두 등록하고, 구판은 sldIdLst 를 등록하지 않는다.
# 어느 쪽이든 3단계가 sldIdLst 를 정합시키므로 여기서는 생성만 한다.
for i in $(seq 1 "$N_CONTENT"); do
  python3 "$PPTX_SKILL/scripts/add_slide.py" "$UNPACKED/" slideLayout5.xml >/dev/null 2>&1 || true
done

# ── 3. presentation.xml 보정: sldIdLst 정합 + 맺음말(템플릿 slide5 = rId10) 마지막으로 이동 ──
# presentation.xml.rels 의 slide 관계를 기준으로 (a) 중복·고아 sldId 제거 (b) 빠진 슬라이드 추가
# (c) 맺음말을 마지막으로 보낸다. 몇 번을 실행해도 결과가 같다(idempotent).
python3 - "$UNPACKED" "$N_CONTENT" << 'PY'
import re, sys
unpacked, n_content = sys.argv[1], int(sys.argv[2])
pres = f'{unpacked}/ppt/presentation.xml'
rels = f'{unpacked}/ppt/_rels/presentation.xml.rels'
with open(pres, encoding='utf-8') as f: x = f.read()
with open(rels, encoding='utf-8') as f: r = f.read()

# slide 관계: rId → target (slides/slideN.xml)
slide_rels = {}
for m in re.finditer(r'<Relationship\b[^>]*/>', r):
    tag = m.group(0)
    if re.search(r'Type="[^"]*/relationships/slide"', tag):
        rid = re.search(r'(?<![:\w])Id="([^"]+)"', tag).group(1)
        tgt = re.search(r'\bTarget="([^"]+)"', tag).group(1)
        slide_rels[rid] = tgt

m = re.search(r'<p:sldIdLst>(.*?)</p:sldIdLst>', x, re.DOTALL)
if not m:
    sys.exit('ERROR: presentation.xml 에 <p:sldIdLst> 가 없음')
entries = re.findall(r'<p:sldId\b[^>]*/>', m.group(1))

def rid_of(e): return re.search(r'r:id="([^"]+)"', e).group(1)
def slide_no(t):
    mm = re.search(r'slide(\d+)\.xml', t); return int(mm.group(1)) if mm else 0

seen, kept = set(), []
for e in entries:                      # (a) 중복·고아 제거, 기존 순서 유지
    rid = rid_of(e)
    if rid in seen or rid not in slide_rels: continue
    seen.add(rid); kept.append(e)
removed = len(entries) - len(kept)

max_id = max([int(i) for i in re.findall(r'(?<![:\w])id="(\d+)"', m.group(1))] + [255])
added = 0
for rid, tgt in sorted(slide_rels.items(), key=lambda kv: slide_no(kv[1])):   # (b) 빠진 슬라이드 추가
    if rid not in seen:
        max_id += 1; seen.add(rid); added += 1
        kept.append(f'<p:sldId id="{max_id}" r:id="{rid}"/>')

closing_rids = {rid for rid, t in slide_rels.items() if t.endswith('slides/slide5.xml')} or {'rId10'}
closing = [e for e in kept if rid_of(e) in closing_rids]                      # (c) 맺음말 마지막으로
others  = [e for e in kept if rid_of(e) not in closing_rids]
x = x[:m.start()] + '<p:sldIdLst>' + ''.join(others + closing) + '</p:sldIdLst>' + x[m.end():]
with open(pres, 'w', encoding='utf-8') as f: f.write(x)

total = len(kept)
print(f'  presentation.xml: sldIdLst {total} slides (+{added} added, -{removed} dup/orphan), closing slide moved to last')
if total - 5 != n_content:
    print(f'  ⚠️ 본문 슬라이드 {total - 5}장 ≠ N_CONTENT {n_content} — 템플릿 기본 5장 + N_CONTENT 구성이 맞는지 확인')
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

# ── 5b. 프로필 적용 (슬라이드 + 레이아웃 하단 크레딧) + 잔존 검사 ──
echo "─── apply_profile.py ($PROFILE) ───"
python3 "$APPLY_PROFILE" --profile "$PROFILE" "$UNPACKED/ppt"
# 값이 비어 플레이스홀더가 남으면 apply_profile.py 가 exit 2 → set -e 가 빌드를 중단시킴

# ── 6. TOC ↔ 본문 검증 ───────────────────────────────────────────
echo "─── verify_toc.py ───"
python3 "$VERIFY" "$UNPACKED"
# verify_toc.py가 실패하면 set -e가 빌드를 중단시킴

# ── 7. clean.py (참조되지 않는 파일 제거) ─────────────────────────
python3 "$PPTX_SKILL/scripts/clean.py" "$UNPACKED/" >/dev/null 2>&1 || true

# ── 8. ★ Google Slides 잔존물 제거 (pack 직전 필수) ──────────────
python3 "$STRIP" --unpacked "$UNPACKED/" 2>&1 | tail -5

# ── 9. pack ───────────────────────────────────────────────────────
if [ -f "$UNPACK_PY" ] && [ -f "$PACK_PY" ]; then
  python3 "$PACK_PY" "$UNPACKED/" "$OUTPUT" --original "$TEMPLATE" 2>&1 | tail -3
else
  python3 - "$UNPACKED" "$OUTPUT" << 'PY'
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
JUNK = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
parts = []
for root, _, fs in os.walk(src):
    for f in fs:
        if f in JUNK: continue
        parts.append(os.path.relpath(os.path.join(root, f), src).replace(os.sep, '/'))
parts.sort()
first = '[Content_Types].xml'
if first not in parts:
    sys.exit(f'ERROR: {src}/[Content_Types].xml 없음 — unpack 결과가 OOXML 패키지가 아님')
order = [first] + [p for p in parts if p != first]      # OPC: content types 를 첫 항목으로
if os.path.exists(out): os.remove(out)                  # 재패킹 시 삭제된 파트가 남지 않도록
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in order:
        z.write(os.path.join(src, p), p)
print(f'  pack: {len(order)} parts → {out} ({os.path.getsize(out)} bytes)')
PY
fi

# ── 9b. OOXML 검증 (pptx 스킬 validate.py, --original 로 템플릿 고유 오류는 제외) ──
if [ -f "$VALIDATE_PY" ] && [ "${SKIP_VALIDATE:-0}" != "1" ]; then
  echo "─── validate.py --original ───"
  if VOUT=$(python3 "$VALIDATE_PY" "$OUTPUT" --original "$TEMPLATE" 2>&1); then
    echo "$VOUT" | tail -3
  else
    echo "$VOUT" | tail -40
    echo "❌ FAIL: validate.py 가 OOXML 오류를 보고함 — 위 메시지의 fix 를 build 소스에 적용 후 재빌드 (우회: SKIP_VALIDATE=1)"
    exit 1
  fi
fi

# ── 10. 최종 검증 ─────────────────────────────────────────────────
GOOGLE_LEFT=$(unzip -p "$OUTPUT" ppt/presentation.xml 2>/dev/null | grep -c 'customschemas\.google\|customooxmlschemas\.google' || true)
META_LEFT=$(unzip -l "$OUTPUT" 2>/dev/null | grep -c 'ppt/metadata' || true)
SIZE=$(stat -c%s "$OUTPUT")

if [ "$GOOGLE_LEFT" -ne 0 ] || [ "$META_LEFT" -ne 0 ]; then
  echo "❌ FAIL: Google leftovers ($GOOGLE_LEFT) or metadata ($META_LEFT) still present"
  exit 1
fi

unzip -t "$OUTPUT" >/dev/null 2>&1 && echo "✅ $OUTPUT  ($SIZE bytes)  Google clean, zip OK"
