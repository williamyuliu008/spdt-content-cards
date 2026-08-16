# rujing push (v2, SPDT-Content-Cards)
param([string]$CardJson)

$hdcCandidates = @(
    "C:\Users\willi\AppData\Local\OpenHarmony\Sdk\26.0.0\toolchains\hdc.exe",
    "D:\9_infra\DevEco\sdk\default\openharmony\toolchains\hdc.exe",
    "$env:LOCALAPPDATA\Huawei\DevEcoStudio\sdk\default\openharmony\toolchains\hdc.exe"
)
$hdc = $null
foreach ($c in $hdcCandidates) {
    if (Test-Path $c) { $hdc = $c; break }
}
if (-not $hdc) {
    Write-Host "[FAIL] hdc.exe not found in: $($hdcCandidates -join '; ')" -ForegroundColor Red
    exit 1
}

Write-Host "[STEP 1] List devices..." -ForegroundColor Cyan
$targets = & $hdc list targets 2>&1
$targetsText = ($targets | Out-String).Trim()
Write-Host "  devices: $targetsText" -ForegroundColor Gray
if ([string]::IsNullOrWhiteSpace($targetsText) -or $targetsText -eq "[Empty]") {
    Write-Host "[FAIL] No device connected" -ForegroundColor Red
    exit 1
}
# accept if any line is non-empty device serial
$hasDevice = $false
foreach ($line in ($targetsText -split "`n")) {
    $t = $line.Trim()
    if ($t -and $t -ne "[Empty]" -and $t -notmatch "^\s*$") { $hasDevice = $true; break }
}
if (-not $hasDevice) {
    Write-Host "[FAIL] No valid device target" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Device connected" -ForegroundColor Green

if (-not (Test-Path $CardJson)) {
    Write-Host "[FAIL] Card file not found: $CardJson" -ForegroundColor Red
    exit 1
}

$size = [math]::Round((Get-Item $CardJson).Length/1024, 1)
Write-Host "[STEP 2] Push card package ($size KB)..." -ForegroundColor Cyan

& $hdc file send $CardJson /data/local/tmp/rujing_cards.json
Write-Host "  -> pushed to /data/local/tmp/" -ForegroundColor Green

& $hdc shell "mkdir -p /data/storage/el2/base/files/"
& $hdc shell "cp /data/local/tmp/rujing_cards.json /data/storage/el2/base/files/rujing_cards.json"

$verify = & $hdc shell "ls -la /data/storage/el2/base/files/rujing_cards.json" 2>&1
if ($LASTEXITCODE -eq 0 -and $verify) {
    Write-Host "  -> copied to sandbox: $verify" -ForegroundColor Green
} else {
    Write-Host "  [WARN] sandbox copy may have failed, try backup path..." -ForegroundColor Yellow
    & $hdc shell "mkdir -p /data/app/el2/100/base/com.harmonystudio.rujing/files/"
    & $hdc shell "cp /data/local/tmp/rujing_cards.json /data/app/el2/100/base/com.harmonystudio.rujing/files/rujing_cards.json"
    Write-Host "  -> backup path attempted" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[DONE] In rujing APP: Settings -> Import -> One-click Import" -ForegroundColor Yellow
