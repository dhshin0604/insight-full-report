#!/usr/bin/env bash
# build_pptx_checked.sh — build_pptx.sh + 통합 게이트(1회 실행)
#
# 기존 오케스트레이터(build_pptx.sh)는 verify_toc 만 내장한다. 이 래퍼는 그 위에
# 내용 품질 게이트(verify_content)와 (옵션)LLM-judge 를 더해, 한 번의 빌드 결과를
# gate_report.py 로 합산 채점한다. 재시도 루프(Phase 6.5)가 매 시도마다 호출한다.
#
# 사용:
#   bash build_pptx_checked.sh kr build_pptx_kr.py 주제_KR_Presentation_YYYYMMDD.pptx
# 옵션 환경변수:
#   JUDGE_VERDICT=judge_verdict_kr.json   # LLM-judge 결과가 있으면 함께 합산
#
# 종료코드: 모든 게이트 통과 0, 하나라도 실패 1 (gate_${lang}.json 에 fixes[] 산출)
set -uo pipefail   # ※ set -e 는 일부러 제외: 게이트 실패를 직접 처리해야 함

LANG_CODE="${1:?Usage: build_pptx_checked.sh <kr|en> <build.py> <out.pptx>}"
BUILD_PY="${2:?build script required}"
OUTPUT="${3:?output filename required}"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
UNPACKED="unpacked_${LANG_CODE}"
JUDGE="${JUDGE_VERDICT:-}"

echo "─── [1/2] 빌드: build_pptx.sh $LANG_CODE ───"
bash "$SKILL_DIR/build_pptx.sh" "$LANG_CODE" "$BUILD_PY" "$OUTPUT"
BUILD_RC=$?
echo "build_pptx.sh exit = $BUILD_RC"

echo "─── [2/2] 통합 게이트: gate_report.py ───"
if [ -d "$UNPACKED" ]; then
  python3 "$SKILL_DIR/gate_report.py" --unpacked "$UNPACKED" --lang "$LANG_CODE" \
      --skill-dir "$SKILL_DIR" ${JUDGE:+--judge "$JUDGE"} --out "gate_${LANG_CODE}.json"
  GATE_RC=$?
else
  echo "❌ $UNPACKED 없음 — 빌드가 너무 일찍 실패"; GATE_RC=1
fi

if [ "$BUILD_RC" -ne 0 ] || [ "$GATE_RC" -ne 0 ]; then
  echo "↻ 게이트 미통과 — gate_${LANG_CODE}.json 의 fixes[] 를 적용 후 재호출"
  exit 1
fi
echo "✅ build + gate 통과: $OUTPUT"
exit 0
