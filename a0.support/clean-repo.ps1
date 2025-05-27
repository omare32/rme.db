# Clean Repository Script
# This script will remove sensitive files from your Git history

# Configuration
$repoUrl = "https://github.com/omare32/rme.db.git"
$tempDir = "$env:TEMP\rme-clean-$(Get-Date -Format 'yyyyMMddHHmmss')"
$cleanBranch = "cleaned-history"

# Files to remove (add more as needed)
$filesToRemove = @(
    "17.email/01.summarize/02.rev.01ig/client.7z",
    "17.email/01.summarize/02.rev.01ig/client.txt",
    "17.email/03.reem/01.old.nada.new.api/01_fetch_emails.py",
    "17.email/03.reem/01.old.nada.new.api/04_create_drafts.py",
    "17.email/01.summarize/02.rev.01ig/01.extract.and.summarize.ipynb",
    "17.email/01.summarize/02.rev.01ig/01.extract.and.summarize.rev.03.ipynb",
    "17.email/02.sum.and.reply/01.5.cells.complete.yasser-omar.ipynb",
    "17.email/02.sum.and.reply/01.5.cells.complete.new.api.ipynb",
    "17.email/02.sum.and.reply/02.5.cells.complete.new.rme.api.ipynb",
    "17.email/02.sum.and.reply/Email-Auto-Responce-V1(Final).rme.api.ipynb",
    "17.email/03.reem/01.old.nada.new.api/original.rme.api.ipynb"
)

# Create temporary directory
Write-Host "Creating temporary directory: $tempDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Clone the repository
Write-Host "Cloning repository..." -ForegroundColor Cyan
Set-Location $tempDir
git clone --mirror $repoUrl repo.git
Set-Location repo.git

# Create and checkout a new branch
Write-Host "Creating clean branch..." -ForegroundColor Cyan
git checkout --orphan $cleanBranch

# Remove sensitive files
foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Write-Host "Removing $file..." -ForegroundColor Yellow
        git filter-branch --force --index-filter \
            "git rm --cached --ignore-unmatch '$file'" \
            --prune-empty --tag-name-filter cat -- --all
    } else {
        Write-Host "File not found: $file" -ForegroundColor Red
    }
}

# Clean up and optimize the repository
Write-Host "Cleaning up..." -ForegroundColor Cyan
git for-each-ref --format="delete %(refname)" refs/original/ | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now

# Push the cleaned repository
Write-Host "Pushing cleaned repository to branch: $cleanBranch" -ForegroundColor Cyan
git push origin $cleanBranch

Write-Host "`nCleanup complete! The cleaned repository has been pushed to the '$cleanBranch' branch." -ForegroundColor Green
Write-Host "You can now review the changes and force push to main if everything looks good." -ForegroundColor Green
