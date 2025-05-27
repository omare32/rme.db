# Source directories to check for new/missing files
$sourceDirs = @(
    "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.backup",
    "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.original"
)

# Destination directory
$destDir = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db"

# Output file for the list of missing files
$outputFile = Join-Path $destDir "missing_files_list_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Function to check if a path is in our target folders (01. to a0.support)
function Is-InTargetFolder {
    param ([string]$path)
    
    # Extract the first folder name after the source directory
    $relativePath = $path -replace [regex]::Escape($sourceDir), ''
    $firstFolder = ($relativePath -split '[\\/]' | Where-Object { $_ -ne '' } | Select-Object -First 1)
    
    # Check if it matches our pattern (starts with 01. through a0.)
    return ($firstFolder -match '^\d{2}\..*|^a0\..*')
}

# Main script
Write-Host "Looking for files in source directories that don't exist in the destination..."

$missingFiles = @()

foreach ($sourceDir in $sourceDirs) {
    if (Test-Path -Path $sourceDir) {
        Write-Host "Scanning $sourceDir..."
        
        # Get all files in the source directory
        $allFiles = Get-ChildItem -Path $sourceDir -Recurse -File | 
                    Where-Object { $_.FullName -notmatch '\\.git\\' }
        
        foreach ($file in $allFiles) {
            $relativePath = $file.FullName.Substring($sourceDir.Length).TrimStart('\')
            
            # Skip if not in our target folders
            if (-not (Is-InTargetFolder -path $file.FullName)) {
                continue
            }
            
            $destPath = Join-Path $destDir $relativePath
            
            # Check if file doesn't exist in destination
            if (-not (Test-Path $destPath)) {
                $missingFiles += $file.FullName
                Write-Host "Missing: $relativePath"
            }
        }
    }
    else {
        Write-Host "Warning: Source directory not found: $sourceDir"
    }
}

# Save the list to a file
if ($missingFiles.Count -gt 0) {
    $missingFiles | Out-File -FilePath $outputFile -Encoding UTF8
    Write-Host "`nFound $($missingFiles.Count) missing files. List saved to: $outputFile"
    
    # Show a preview
    Write-Host "`nPreview of missing files:"
    $missingFiles | Select-Object -First 10 | ForEach-Object { 
        $relPath = $_.Substring($_.LastIndexOf('rme.db') + 7)
        Write-Host "  - $relPath" 
    }
    
    if ($missingFiles.Count -gt 10) {
        Write-Host "  ... and $($missingFiles.Count - 10) more files"
    }
    
    Write-Host "`nReview the complete list in: $outputFile"
}
else {
    Write-Host "No missing files found in the target folders (01. to a0.)."
}
