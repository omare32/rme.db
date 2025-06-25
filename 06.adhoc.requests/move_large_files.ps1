# Source and destination base directories
$sourceBase = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\06.adhoc.requests"
$destBase = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.data\06.adhoc.requests"

# File extensions to move (Excel, PDF, archive, and executable files)
$extensions = @("*.xlsx", "*.xls", "*.pdf", "*.7z", "*.zip", "*.rar", "*.exe")

# Get all files matching the extensions recursively
$filesToMove = Get-ChildItem -Path $sourceBase -Recurse -Include $extensions

if ($filesToMove.Count -eq 0) {
    Write-Host "No files to move in $sourceBase."
    exit
}

Write-Host "Found $($filesToMove.Count) files to move from $sourceBase to $destBase"

foreach ($file in $filesToMove) {
    # Get the relative path from the source base
    $relativePath = $file.FullName.Substring($sourceBase.Length + 1)
    
    # Create the destination directory if it doesn't exist
    $destDir = Join-Path $destBase (Split-Path $relativePath -Parent)
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    
    # Move the file
    $destPath = Join-Path $destBase $relativePath
    Write-Host "Moving $($file.FullName) to $destPath"
    Move-Item -Path $file.FullName -Destination $destPath -Force
}

Write-Host "All large files have been moved successfully!"
Write-Host "Source: $sourceBase"
Write-Host "Destination: $destBase"
