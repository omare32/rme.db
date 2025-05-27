# Create a backup branch
git checkout -b backup-before-cleanup

# Create a new branch for the cleaned history
git checkout -b cleaned-history

# List of files to remove from history
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

# Remove each file from history
foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Write-Host "Removing $file from history..." -ForegroundColor Yellow
        git filter-branch --force --index-filter "git rm --cached --ignore-unmatch '$file'" --prune-empty --tag-name-filter cat -- --all
    }
}

# Clean up and optimize
git for-each-ref --format="delete %(refname)" refs/original/ | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now

Write-Host "`nCleanup complete! Here's what to do next:" -ForegroundColor Green
Write-Host "1. Review the changes: git log --stat"
Write-Host "2. Push the cleaned history: git push -u origin cleaned-history"
Write-Host "3. After verification, you can make this your new main branch"
