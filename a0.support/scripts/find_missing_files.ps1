# Source directories to check for new/missing files
$sourceDirs = @(
    "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.backup",
    "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.original"
)

# Destination directory
$destDir = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db"

# Log file
$logFile = Join-Path $destDir "missing_files_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Function to get all files that need to be copied
function Get-FilesToCopy {
    param (
        [string]$sourceDir,
        [string]$destDir
    )
    
    $filesToCopy = @()
    
    # Get all files in source directory that match our pattern (01. to a0.)
    $allFiles = Get-ChildItem -Path $sourceDir -Recurse -File | 
                Where-Object { 
                    $_.FullName -notmatch '\\\.git\\' -and  # Exclude .git directories
                    $_.DirectoryName -match '\\\d{2}\..*|\\a0\..*'  # Only include 01. to a0. folders
                }
    
    foreach ($file in $allFiles) {
        $relativePath = $file.FullName.Substring($sourceDir.Length).TrimStart('\')
        $destPath = Join-Path $destDir $relativePath
        
        # Check if file doesn't exist in destination or is different
        if (-not (Test-Path $destPath)) {
            $filesToCopy += $file
            "MISSING: $relativePath" | Out-File -FilePath $logFile -Append
        }
        else {
            $destFile = Get-Item $destPath -ErrorAction SilentlyContinue
            if ($destFile -eq $null -or 
                $file.Length -ne $destFile.Length -or 
                $file.LastWriteTime -gt $destFile.LastWriteTime) {
                $filesToCopy += $file
                "UPDATED: $relativePath" | Out-File -FilePath $logFile -Append
            }
        }
    }
    
    return $filesToCopy
}

# Main script
Write-Host "Scanning for missing or updated files..."
$allFilesToCopy = @()

foreach ($sourceDir in $sourceDirs) {
    if (Test-Path -Path $sourceDir) {
        Write-Host "Scanning $sourceDir..."
        $files = Get-FilesToCopy -sourceDir $sourceDir -destDir $destDir
        $allFilesToCopy += $files
        Write-Host "Found $($files.Count) files to copy from $([System.IO.Path]::GetFileName($sourceDir))"
    }
    else {
        Write-Host "Warning: Source directory not found: $sourceDir"
    }
}

$totalFiles = $allFilesToCopy.Count
Write-Host "`nTotal files to copy: $totalFiles"
Write-Host "Log file: $logFile"

if ($totalFiles -eq 0) {
    Write-Host "No files need to be copied."
    exit
}

# Show a preview of the files
Write-Host "`nPreview of files to be copied:"
$allFilesToCopy | Select-Object -First 20 | ForEach-Object { 
    $relPath = $_.FullName.Substring($_.Directory.Parent.FullName.Length + 1)
    Write-Host "  - $relPath" 
}

if ($totalFiles -gt 20) {
    Write-Host "  ... and $($totalFiles - 20) more files"
}

Write-Host "`nReview the log file for complete list: $logFile"
Write-Host "After reviewing, you can run the copy operation with the copy_files.ps1 script."
