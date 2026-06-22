# Deploy FitKG to Vercel (graph UI + RAG + KIMORE + LLM)
# Prerequisites: npm i -g vercel   (or: winget install Vercel.Vercel)
#
# First deploy (links project + uploads outputs/fitkg_kg data):
#   cd D:\physui
#   vercel
#
# Production:
#   vercel --prod
#
# Set env vars in Vercel dashboard (Project → Settings → Environment Variables):
#   NVIDIA_API_KEY          (required for LLM chat)
#   FITKG_CHAT_MODEL        (optional, default qwen/qwen3-next-80b-a3b-instruct)
#   FITKG_LLM_MAX_TOKENS    (optional; use 512 on Hobby if LLM times out)
#
# Or via CLI:
#   vercel env add NVIDIA_API_KEY

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Host "Vercel CLI not found. Install: npm install -g vercel" -ForegroundColor Yellow
    Write-Host "Or deploy via https://vercel.com/new (import Git repo)" -ForegroundColor Yellow
    exit 1
}

$rag = Join-Path $PSScriptRoot "outputs\fitkg_kg\rag_index.json"
if (-not (Test-Path $rag)) {
    Write-Host "Building RAG index..." -ForegroundColor Cyan
    python fitkg_build_rag_index.py
}

$prod = $args -contains "--prod"
if ($prod) {
    Write-Host "Deploying to Vercel PRODUCTION..." -ForegroundColor Green
    vercel --prod
} else {
    Write-Host "Deploying preview to Vercel..." -ForegroundColor Cyan
    vercel
}
