# Stop conflicting Python web servers on 8765/8766, then start FitKG (graph + RAG chat).
$ErrorActionPreference = "SilentlyContinue"
$ports = 8765, 8766, 8767, 8768
foreach ($port in $ports) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Milliseconds 800
Set-Location $PSScriptRoot
Write-Host "Starting FitKG on port 8766 (graph + chat API)..." -ForegroundColor Cyan
python fitkg_serve.py
