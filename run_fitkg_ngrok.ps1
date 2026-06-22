# FitKG demo via ngrok — graph UI + RAG chat + KIMORE + LLM (single public URL)
# Usage:
#   1. Copy .env.example → .env and set NVIDIA_API_KEY (or OPENAI_API_KEY)
#   2. ngrok config add-authtoken YOUR_TOKEN   (once — https://dashboard.ngrok.com/get-started/your-authtoken)
#   3. .\run_fitkg_ngrok.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Refresh PATH so winget-installed ngrok is found in this session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

function Test-NgrokAuth {
    $cfg = Join-Path $env:LOCALAPPDATA "ngrok\ngrok.yml"
    if (-not (Test-Path $cfg)) { return $false }
    $text = Get-Content $cfg -Raw -ErrorAction SilentlyContinue
    return ($text -match "authtoken:\s*\S+")
}

function Stop-FitkgPorts {
    $ports = 8765, 8766, 8767, 8768, 8770, 4040
    foreach ($port in $ports) {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
    Start-Sleep -Milliseconds 600
}

function Wait-Health([int]$Port, [int]$Seconds = 45) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 3
            if ($r.server -eq "fitkg-serve" -and $r.ok) { return $r }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    throw "FitKG server did not become healthy on port $Port within ${Seconds}s"
}

function Get-NgrokPublicUrl {
    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline) {
        try {
            $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2
            $https = $tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
            if ($https.public_url) { return $https.public_url }
        } catch { }
        Start-Sleep -Milliseconds 400
    }
    return $null
}

# --- prerequisites ---
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "ngrok not found. Install: winget install Ngrok.Ngrok" -ForegroundColor Red
    exit 1
}
if (-not (Test-NgrokAuth)) {
    Write-Host ""
    Write-Host "ngrok needs a free authtoken (one-time setup):" -ForegroundColor Yellow
    Write-Host "  1. Sign in at https://dashboard.ngrok.com/get-started/your-authtoken"
    Write-Host "  2. Run:  ngrok config add-authtoken YOUR_TOKEN"
    Write-Host "  3. Re-run: .\run_fitkg_ngrok.ps1"
    Write-Host ""
    exit 1
}

$ragIndex = Join-Path $PSScriptRoot "outputs\fitkg_kg\rag_index.json"
if (-not (Test-Path $ragIndex)) {
    Write-Host "Building RAG index (first time)..." -ForegroundColor Cyan
    python fitkg_build_rag_index.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# --- start FitKG API + static UI ---
Write-Host "Stopping old servers on 8765–8770 / ngrok 4040..." -ForegroundColor DarkGray
Stop-FitkgPorts

$env:FITKG_PORT = "8766"
Write-Host "Starting FitKG (graph + RAG + LLM API) on port 8766..." -ForegroundColor Cyan
$fitkgJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    $env:FITKG_PORT = "8766"
    python fitkg_serve.py 2>&1
}

try {
    $health = Wait-Health -Port 8766
    Write-Host "FitKG ready — RAG index: $($health.rag_index), LLM: $($health.llm) ($($health.llm_provider))" -ForegroundColor Green

    Write-Host "Starting ngrok tunnel..." -ForegroundColor Cyan
    $ngrokJob = Start-Job -ScriptBlock {
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path", "User")
        & ngrok http 8766 --log=stdout 2>&1
    }

    $public = Get-NgrokPublicUrl
    if (-not $public) {
        throw "ngrok started but no public URL on :4040 — check ngrok job output"
    }

    $demoUrl = "$public/fitkg_graph_ui/index.html"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  PUBLIC DEMO URL (share this):" -ForegroundColor Green
    Write-Host "  $demoUrl" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Local:     http://127.0.0.1:8766/fitkg_graph_ui/index.html"
    Write-Host "ngrok UI:  http://127.0.0.1:4040  (request inspector)"
    Write-Host ""
    Write-Host "Demo features on this URL:"
    Write-Host "  • Knowledge graph search + 2-hop explorer"
    Write-Host "  • RAG chat (blue button, bottom-right) — enable LLM checkbox"
    Write-Host "  • Body map + muscle highlighting from chat"
    Write-Host "  • KIMORE rehab pose demo + live feedback"
    Write-Host ""
    Write-Host "Press Ctrl+C to stop ngrok and FitKG." -ForegroundColor DarkGray

    # Keep script alive; stream FitKG logs on Ctrl+C path
    while ($true) {
        Receive-Job $fitkgJob -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
        if ($fitkgJob.State -eq "Failed" -or $fitkgJob.State -eq "Completed") {
            Write-Host "FitKG server stopped unexpectedly." -ForegroundColor Red
            Receive-Job $fitkgJob
            break
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Write-Host "`nShutting down..." -ForegroundColor DarkGray
    Stop-Job $fitkgJob, $ngrokJob -ErrorAction SilentlyContinue
    Remove-Job $fitkgJob, $ngrokJob -Force -ErrorAction SilentlyContinue
    Stop-FitkgPorts
}
