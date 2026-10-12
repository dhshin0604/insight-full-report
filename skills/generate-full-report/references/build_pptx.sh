#!/usr/bin/env bash
# build_pptx.sh : 정본 PPTX 빌드 오케스트레이터 (v1.0)
#
# KR 또는 EN PPTX 한 개를 처음부터 끝까지 같은 순서로 빌드함. 모델이 unpack, 슬라이드 추가,
# 순서 조정, 정리, pack 단계를 직접 짜다가 어긋나는 일을 막으려고 모든 OOXML 조작을 이 스크립트가 맡음.
# v1.0 부터 외부 pptx 스킬 스크립트에 기대지 않고 같은 폴더의 ooxml_tools.py(표준 라이브러리만)를 씀.
#
# 사용법:
#   bash references/build_pptx.sh kr build_pptx_kr.py 주제_KR_Presentation_YYYYMMDD.pptx
#   bash references/build_pptx.sh en build_pptx_en.py 주제_EN_Presentation_YYYYMMDD.pptx
#
# 인자:
#   $1 = 언어 (kr | en) : unpacked_kr/ 또는 unpacked_en/ 폴더 이름에 씀
#   $2 = 빌드 스크립트 : Zone helper 로 slide{N}.xml 을 쓰는 파이썬 스크립트
#   $3 = 출력 .pptx 파일 이름
#
# 환경 변수 (선택):
#   TEMPLATE   : TEMPLATE.pptx 경로 (기본 : 이 스크립트 옆 TEMPLATE.pptx)
#   N_CONTENT  : 더할 본문 슬라이드 수 (기본 8 → 총 13장. 전체 장 수 - 5)
#   PROFILE    : profile.json 경로 (기본 자동 선택 : ./profile.json > references/profile.json)
#   LOGO       : 표지 로고 PNG (기본 references/logo.png, 없으면 템플릿의 빈 이미지 유지)
#   PYTHON     : 파이썬 실행 파일 (기본 python3)
set -euo pipefail
# Windows(Git Bash) 의 cp949 파이프에서도 파이썬 출력이 멈추지 않게 UTF-8 로 고정
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

LANG_CODE="${1:?Usage: build_pptx.sh <kr|en> <build_script.py> <output.pptx>}"
BUILD_PY="${2:?build script path required}"
OUTPUT="${3:?output filename required}"
N_CONTENT="${N_CONTENT:-8}"
PY="${PYTHON:-python3}"

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="${TEMPLATE:-$SKILL_DIR/TEMPLATE.pptx}"
OOXML="$SKILL_DIR/ooxml_tools.py"
STRIP="$SKILL_DIR/strip_google_extensions.py"
VERIFY="$SKILL_DIR/verify_toc.py"
APPLY_PROFILE="$SKILL_DIR/apply_profile.py"
LOGO="${LOGO:-$SKILL_DIR/logo.png}"

command -v "$PY" >/dev/null 2>&1 || { echo "ERROR: $PY 없음. Python 3.9 이상을 설치하거나 PYTHON 환경변수로 지정"; exit 2; }
for f in "$TEMPLATE" "$OOXML" "$STRIP" "$VERIFY" "$APPLY_PROFILE"; do
  [ -f "$f" ] || { echo "ERROR: $f 없음"; exit 2; }
done
[ -f "$BUILD_PY" ] || { echo "ERROR: 빌드 스크립트 없음 : $BUILD_PY"; exit 2; }

# 프로필 자동 선택 : PROFILE 환경변수 > ./profile.json(작업 폴더) > references/profile.json
PROFILE="$("$PY" "$APPLY_PROFILE" --which | tr -d '\r')"   # Windows 파이썬의 CRLF 줄끝 제거
UNPACKED="unpacked_${LANG_CODE}"

echo "==============================================================="
echo "  build_pptx.sh : $LANG_CODE -> $OUTPUT"
echo "  TEMPLATE   = $TEMPLATE"
echo "  PROFILE    = $PROFILE"
echo "  LOGO       = $([ -f "$LOGO" ] && echo "$LOGO" || echo "(없음 : 템플릿 기본 이미지 유지)")"
echo "  BUILD_PY   = $BUILD_PY"
echo "  UNPACKED   = $UNPACKED  (본문 추가 $N_CONTENT 장)"
echo "==============================================================="

# 1. 깨끗하게 풀기
rm -rf "$UNPACKED"
"$PY" "$OOXML" unpack "$TEMPLATE" "$UNPACKED"

# 1b. 로고 : references/logo.png (또는 LOGO=경로) 가 있으면 표지 레이아웃 이미지 교체
if [ -f "$LOGO" ] && [ -f "$UNPACKED/ppt/media/image1.png" ]; then
  cp "$LOGO" "$UNPACKED/ppt/media/image1.png"
  echo "  logo: ppt/media/image1.png <- $LOGO"
fi

# 2. 본문 슬라이드 추가 (slideLayout5 = contents) : 관계 ID 와 슬라이드 ID 는 자동으로 다음 번호를 씀
"$PY" "$OOXML" add-slides "$UNPACKED" slideLayout5.xml "$N_CONTENT"

# 3. 맺음말 슬라이드(slide5.xml)를 sldIdLst 맨 끝으로
"$PY" "$OOXML" move-last "$UNPACKED" slide5.xml

# 4. slide3 레이아웃 보정 : 간지(layout3) -> 본문(layout5)
"$PY" "$OOXML" set-layout "$UNPACKED" slide3.xml slideLayout5.xml

# 5. 빌드 스크립트 실행 (콘텐츠 -> slide{N}.xml)
echo "--- $BUILD_PY ---"
TARGET_UNPACKED="$UNPACKED" "$PY" "$BUILD_PY"

# 5b. 프로필 적용 (슬라이드 + 레이아웃 하단 크레딧) + 잔존 검사 : 값이 비면 exit 2 로 중단
echo "--- apply_profile.py ($PROFILE) ---"
"$PY" "$APPLY_PROFILE" --profile "$PROFILE" "$UNPACKED/ppt"

# 6. TOC <-> 본문 챕터 정합 검사 : 실패하면 set -e 가 빌드를 멈춤
echo "--- verify_toc.py ---"
"$PY" "$VERIFY" "$UNPACKED"

# 7. sldIdLst 에 없는 슬라이드 파트 정리
"$PY" "$OOXML" clean "$UNPACKED"

# 8. Google Slides 잔존물 제거 (pack 직전 필수)
"$PY" "$STRIP" --unpacked "$UNPACKED/" 2>&1 | tail -5

# 9. 묶기
"$PY" "$OOXML" pack "$UNPACKED" "$OUTPUT"

# 10. 최종 검증 : 구조, Google 잔존물, metadata
"$PY" "$OOXML" check "$OUTPUT"
"$PY" - "$OUTPUT" <<'PY'
import sys, zipfile
out = sys.argv[1]
with zipfile.ZipFile(out) as z:
    pres = z.read('ppt/presentation.xml').decode('utf-8')
    google = pres.count('customschemas.google') + pres.count('customooxmlschemas.google')
    meta = sum(1 for n in z.namelist() if n.startswith('ppt/metadata'))
    size = sum(i.file_size for i in z.infolist())
if google or meta:
    print('FAIL: Google 잔존물 %d, metadata %d' % (google, meta)); sys.exit(1)
import os
print('OK %s (%d bytes) : Google 잔존물 0, metadata 0, zip OK' % (out, os.path.getsize(out)))
PY
