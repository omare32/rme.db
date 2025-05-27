# Source and destination directories
$sourceDir = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.original"
$destDir = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db"

# Create a log file
$logFile = Join-Path $destDir "sync_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$logContent = @()

# Function to check if a file should be excluded based on .gitignore
function Test-IgnoredFile {
    param (
        [string]$filePath
    )
    
    # Convert to relative path for git check-ignore
    $relativePath = $filePath.Replace("$destDir\", "")
    
    # Check if the file is ignored by git
    $ignored = git -C $destDir check-ignore -q $relativePath 2>$null
    
    return $ignored -eq $null ? $false : $true
}

# Get all files from source directory
$allFiles = Get-ChildItem -Path $sourceDir -Recurse -File -Force

foreach ($file in $allFiles) {
    $relativePath = $file.FullName.Substring($sourceDir.Length).TrimStart('\\')
    $destinationPath = Join-Path $destDir $relativePath
    $destinationDir = [System.IO.Path]::GetDirectoryName($destinationPath)
    
    # Skip if the file is in the .git directory
    if ($file.FullName -like '*\.git\*') {
        continue
    }
    
    # Create destination directory if it doesn't exist
    if (-not (Test-Path -Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        $logContent += "Created directory: $destinationDir"
    }
    
    # Check if the file would be ignored by git
    $isIgnored = Test-IgnoredFile -filePath $destinationPath
    
    # Copy the file if it doesn't exist or is different
    if (-not (Test-Path -Path $destinationPath) -or 
        ((Get-FileHash $file.FullName).Hash -ne (Get-FileHash $destinationPath).Hash)) {
        
        # If the file is not ignored, make a backup before overwriting
        if ((Test-Path -Path $destinationPath) -and (-not $isIgnored)) {
            $backupPath = "$destinationPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            Copy-Item -Path $destinationPath -Destination $backupPath -Force
            $logContent += "Backed up: $relativePath to $backupPath"
        }
        
        # Copy the file
        Copy-Item -Path $file.FullName -Destination $destinationPath -Force
        
        if ($isIgnored) {
            $logContent += "Copied (ignored): $relativePath"
        } else {
            $logContent += "Copied: $relativePath"
        }
    }
    else {
        if ($isIgnored) {
            $logContent += "Skipped (ignored, already exists): $relativePath"
        } else {
            $logContent += "Skipped (already exists): $relativePath"
        }
    }
}

# Write to log file
$logContent | Out-File -FilePath $logFile -Encoding UTF8

Write-Host "Sync operation completed. Check the log file: $logFile"
