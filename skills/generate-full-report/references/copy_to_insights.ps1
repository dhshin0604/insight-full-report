$ErrorActionPreference = 'Stop'
$THIS = Split-Path -Parent $MyInvocation.MyCommand.Definition
Start-Transcript -Path (Join-Path $THIS 'copy_to_insights.log') -Force | Out-Null

# 신동형인사이트 폴더 위치 (OneDrive 동기화 경로 자동 탐색)
$candidates = @(
    "$env:USERPROFILE\OneDrive\Dong Hyung - 개인\신동형인사이트",
    "$env:USERPROFILE\OneDrive - Personal\신동형인사이트",
    "$env:OneDrive\신동형인사이트",
    "$env:OneDriveConsumer\신동형인사이트",
    "$env:USERPROFILE\OneDrive\신동형인사이트"
)
$INSIGHTS = $null
foreach ($c in $candidates) {
    if (Test-Path $c) { $INSIGHTS = $c; break }
}
if (-Not $INSIGHTS) {
    Write-Host "❌ 신동형인사이트 폴더를 찾지 못했습니다. 후보:" -ForegroundColor Red
    $candidates | ForEach-Object { Write-Host "   $_" }
    Stop-Transcript | Out-Null
    Start-Sleep -Seconds 6
    exit 1
}

Write-Host "신동형인사이트 위치: $INSIGHTS"
$TOPIC_DIR = Join-Path $INSIGHTS "HumanoidWP2025_20260426"
if (-Not (Test-Path $TOPIC_DIR)) {
    New-Item -ItemType Directory -Force -Path $TOPIC_DIR | Out-Null
    Write-Host "  → 신규 디렉터리 생성: $TOPIC_DIR"
} else {
    Write-Host "  → 기존 디렉터리 사용: $TOPIC_DIR"
}

$files = Get-ChildItem -Path $THIS -File | Where-Object { $_.Name -like 'HumanoidWP2025_*.docx' -or $_.Name -like 'HumanoidWP2025_*.pptx' }
Write-Host ""
Write-Host "복사할 파일 ($($files.Count)개):"
foreach ($f in $files) {
    $dst = Join-Path $TOPIC_DIR $f.Name
    Copy-Item -Path $f.FullName -Destination $dst -Force
    $sha = (Get-FileHash $dst -Algorithm SHA256).Hash.Substring(0,12)
    Write-Host ("  ✓ {0,-60} ({1:N1} KB, sha={2})" -f $f.Name, ($f.Length/1KB), $sha)
}

# 결과 검증
Write-Host ""
Write-Host "── 적용 후 디렉터리 내용 ──"
Get-ChildItem -Path $TOPIC_DIR | Format-Table Name, Length, LastWriteTime -AutoSize | Out-String | Write-Host
Write-Host "✅ 신동형인사이트\HumanoidWP2025_20260426 보관 완료." -ForegroundColor Green

Stop-Transcript | Out-Null
Start-Sleep -Seconds 4
