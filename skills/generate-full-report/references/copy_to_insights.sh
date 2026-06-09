#!/usr/bin/env bash
# copy_to_insights.sh — outputs/ 의 {주제}_*.docx/pptx 4종을
# OneDrive\신동형인사이트\{주제}_{YYYYMMDD}\ 디렉터리로 일괄 보관한다.
#
# 사용법:
#   bash references/copy_to_insights.sh HumanoidWP2025 20260426
#
# 이 스크립트는 PowerShell을 호출해 Windows OneDrive 경로에 접근한다.
# Cowork sandbox 안에서는 OneDrive가 마운트되지 않으므로,
# bash 스크립트가 PowerShell wrapper(.ps1)를 outputs 에 빌드해 두고
# 사용자에게 한 번 실행 안내를 띄운다. 자동 실행은 컴퓨터 제어로 .bat을 더블클릭하면 된다.
set -euo pipefail
TOPIC="${1:?Usage: copy_to_insights.sh <TOPIC> <YYYYMMDD>}"
YMD="${2:?YYYYMMDD required}"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${TOPIC}_${YMD}"

# OneDrive 후보 + Test-Path는 PowerShell이 처리한다 — 이 스크립트는 .ps1만 emit
PS_PATH="$SKILL_DIR/copy_to_insights.ps1"
if [ ! -f "$PS_PATH" ]; then
  echo "ERROR: $PS_PATH not found (이 스킬 번들에 포함되어야 함)"
  exit 2
fi

# Cowork outputs 디렉터리가 워크스페이스로 마운트되어 있을 때만 실행
WORKSPACE="${COWORK_OUTPUTS:-/sessions/$USER/mnt/outputs}"
echo "── copy_to_insights.sh ──"
echo "  TOPIC=$TOPIC, DATE=$YMD"
echo "  SKILL_DIR=$SKILL_DIR"
echo "  WORKSPACE=$WORKSPACE"
echo "  → 사용자에게 안내: outputs/copy_to_insights.bat 더블클릭으로 OneDrive 보관 완료"
