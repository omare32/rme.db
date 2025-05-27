Set-ExecutionPolicy Bypass -Scope Process -Force
.\find_and_copy_missing.ps1# Source directories to copy from
$sourceDirs = @(
    "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.backup",
    "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.original"
)

# Destination directory
$destDir = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db"

# Batch size for review
$batchSize = 100

# Log file
$logFile = Join-Path $destDir "copy_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Function to get all files from source directories
get_all_files() {
    param (
        [string]$sourceDir
    )
    
    # Get all files, excluding .git directories
    $allFiles = Get-ChildItem -Path $sourceDir -Recurse -File | 
                Where-Object { $_.FullName -notmatch '\\.git\\' }
    
    return $allFiles
}

# Function to copy a batch of files
copy_batch() {
    param (
        [array]$files,
        [string]$sourceBase,
        [string]$destBase,
        [ref]$copiedCount,
        [ref]$skippedCount
    )
    
    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($sourceBase.Length + 1)
        $destPath = Join-Path $destBase $relativePath
        $destDir = [System.IO.Path]::GetDirectoryName($destPath)
        
        # Create destination directory if it doesn't exist
        if (-not (Test-Path -Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        # Skip if file already exists and is the same
        if (Test-Path -Path $destPath) {
            $existingFile = Get-Item -Path $destPath -ErrorAction SilentlyContinue
            if ($existingFile -and ($file.Length -eq $existingFile.Length) -and 
                ($file.LastWriteTime -le $existingFile.LastWriteTime)) {
                $skippedCount.Value++
                continue
            }
        }
        
        # Copy the file
        try {
            Copy-Item -Path $file.FullName -Destination $destPath -Force
            $copiedCount.Value++
            "Copied: $relativePath" | Out-File -FilePath $logFile -Append
        } catch {
            "Error copying $($file.FullName): $_" | Out-File -FilePath $logFile -Append
        }
    }
}

# Main script
Write-Host "Starting file copy process..."
Write-Host "Log file: $logFile"

$totalFiles = 0
$allFiles = @()

# Get all files from source directories
foreach ($sourceDir in $sourceDirs) {
    if (Test-Path -Path $sourceDir) {
        Write-Host "Scanning $sourceDir..."
        $files = get_all_files -sourceDir $sourceDir
        $allFiles += $files
        Write-Host "Found $($files.Count) files in $sourceDir"
    } else {
        Write-Host "Warning: Source directory not found: $sourceDir" | Out-File -FilePath $logFile -Append
    }
}

$totalFiles = $allFiles.Count
Write-Host "Total files to process: $totalFiles"

if ($totalFiles -eq 0) {
    Write-Host "No files found to copy."
    exit
}

# Process files in batches
$batchNumber = 1
$copiedCount = 0
$skippedCount = 0

for ($i = 0; $i -lt $totalFiles; $i += $batchSize) {
    $batch = $allFiles[$i..[Math]::Min(($i + $batchSize - 1), ($totalFiles - 1))]
    
    Write-Host "`n=== Batch $batchNumber ==="
    Write-Host "Files in this batch: $($batch.Count)"
    
    # Show first 5 files in the batch
    Write-Host "`nSample files in this batch:"
    $batch | Select-Object -First 5 | ForEach-Object { 
        $relPath = $_.FullName.Substring($_.Directory.Parent.FullName.Length + 1)
        Write-Host "  - $relPath" 
    }
    
    if ($batch.Count -gt 5) {
        Write-Host "  ... and $($batch.Count - 5) more files"
    }
    
    $confirm = Read-Host "`nDo you want to copy this batch? (y/n, default: y)"
    
    if ($confirm -ne 'n') {
        foreach ($sourceDir in $sourceDirs) {
            $batchFromSource = $batch | Where-Object { $_.FullName.StartsWith($sourceDir) }
            if ($batchFromSource) {
                copy_batch -files $batchFromSource -sourceBase $sourceDir -destBase $destDir -copiedCount ([ref]$copiedCount) -skippedCount ([ref]$skippedCount)
            }
        }
        Write-Host "Copied batch $batchNumber. Total copied: $copiedCount, Skipped: $skippedCount"
    } else {
        Write-Host "Skipped batch $batchNumber"
    }
    
    $batchNumber++
    
    # Ask if user wants to continue
    if ($i + $batchSize -lt $totalFiles) {
        $continue = Read-Host "`nContinue with next batch? (y/n, default: y)"
        if ($continue -eq 'n') {
            Write-Host "Stopped by user after $batchNumber batches."
            break
        }
    }
}

Write-Host "`nCopy process completed."
Write-Host "Total files processed: $totalFiles"
Write-Host "Files copied: $copiedCount"
Write-Host "Files skipped (already exist): $skippedCount"
Write-Host "Log file: $logFile"
