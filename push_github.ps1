# Push to github.com/astral-fate/physio (run after: gh auth login)
$ErrorActionPreference = "Stop"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")
Set-Location $PSScriptRoot

$git = @("git", "-c", "safe.directory=D:/physui")
$repo = "astral-fate/physio"
$repoUrl = "https://github.com/$repo.git"

gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged into GitHub. Run:" -ForegroundColor Yellow
    Write-Host "  gh auth login --hostname github.com --git-protocol https --web"
    exit 1
}

$remotes = & @git remote 2>$null
if ($remotes -contains "origin") {
    & @git remote set-url origin $repoUrl
} else {
    & @git remote add origin $repoUrl
}

Write-Host "Remote: $repoUrl" -ForegroundColor Cyan
Write-Host "Pushing main..." -ForegroundColor Cyan
& @git push -u origin main
Write-Host ""
Write-Host "Done: https://github.com/$repo" -ForegroundColor Green
Write-Host "Next: https://vercel.com/new → Import $repo → add NVIDIA_API_KEY → Deploy"
