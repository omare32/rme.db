# Source and destination directories
$sourceDir = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.original"
$destDir = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db"

# File patterns to copy (database and Excel files)
$filePatterns = @("*.db", "*.sqlite", "*.sqlite3", "*.xlsx", "*.xls", "*.xlsm", "*.xlsb", "*.csv")

# Exclude patterns (from .gitignore)
$excludePatterns = @(
    "*\__pycache__\*",
    "*\.git\*",
    "*\node_modules\*",
    "*\venv\*",
    "*\.venv\*",
    # Changed pattern
    "*\a0.support\.gradio\*"
)

# Function to check if a file should be excluded
function Should-ExcludeFile {
    param (
        [string]$filePath
    )
    
    foreach ($pattern in $excludePatterns) {
        if ($filePath -like $pattern) {
            return $true
        }
    }
    return $false
}

# Create a log file
$logFile = Join-Path $destDir "copy_files_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$logContent = @()

# Get all matching files
$filesToCopy = Get-ChildItem -Path $sourceDir -Include $filePatterns -Recurse -File | 
    Where-Object { -not (Should-ExcludeFile $_.FullName) }

foreach ($file in $filesToCopy) {
    $relativePath = $file.FullName.Substring($sourceDir.Length).TrimStart('\')
    $destinationPath = Join-Path $destDir $relativePath
    $destinationDir = [System.IO.Path]::GetDirectoryName($destinationPath)
    
    # Create destination directory if it doesn't exist
    if (-not (Test-Path -Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        $logContent += "Created directory: $destinationDir"
    }
    
    # Copy the file if it doesn't exist or is different
    if (-not (Test-Path -Path $destinationPath) -or 
        ((Get-FileHash $file.FullName).Hash -ne (Get-FileHash $destinationPath).Hash)) {
        Copy-Item -Path $file.FullName -Destination $destinationPath -Force
        $logContent += "Copied: $relativePath"
    }
    else {
        $logContent += "Skipped (already exists): $relativePath"
    }
}

# Write to log file
$logContent | Out-File -FilePath $logFile -Encoding UTF8

Write-Host "File copy operation completed. Check the log file: $logFile"
