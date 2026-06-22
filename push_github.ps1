# Create github.com/astral-fate/physui and push (run after: gh auth login)
$ErrorActionPreference = "Stop"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")
Set-Location $PSScriptRoot

$git = @("git", "-c", "safe.directory=D:/physui")

gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged into GitHub. Run:" -ForegroundColor Yellow
    Write-Host "  gh auth login --hostname github.com --git-protocol https --web"
    exit 1
}

$repo = "astral-fate/physui"
$exists = gh repo view $repo 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating https://github.com/$repo ..." -ForegroundColor Cyan
    gh repo create physui --public --source=. --remote=origin --description "FitKG Explorer — graph UI, RAG chat, KIMORE demos (Vercel-ready)"
} else {
    Write-Host "Repo exists: https://github.com/$repo" -ForegroundColor Green
    $remotes = & @git remote 2>$null
    if ($remotes -notcontains "origin") {
        & @git remote add origin "https://github.com/$repo.git"
    }
}

Write-Host "Pushing main..." -ForegroundColor Cyan
& @git push -u origin main
Write-Host ""
Write-Host "Done: https://github.com/$repo" -ForegroundColor Green
Write-Host "Next: https://vercel.com/new → Import astral-fate/physui → add NVIDIA_API_KEY → Deploy"
