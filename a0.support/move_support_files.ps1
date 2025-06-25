# Source and destination base directories
$sourceBase = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\a0.support"
$destBase = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.data\a0.support"

# File extensions to move (common large files in support directories)
$extensions = @(
    # Archives and packages
    "*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.jar",
    # Media files
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff", "*.webp", "*.svg",
    # Documents
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.xlsb", "*.ppt", "*.pptx",
    # Data files
    "*.csv", "*.json", "*.xml", "*.db", "*.sqlite", "*.sqlite3",
    # Logs and dumps
    "*.log", "*.dump", "*.bak",
    # Virtual environments and caches
    "venv*", "env*", ".venv*", "__pycache__", ".pytest_cache", ".mypy_cache",
    # Node.js related
    "node_modules", "dist", "build", ".next", ".nuxt",
    # Python related
    "*.pyc", "*.pyo", "*.pyd", "*.egg", "*.whl",
    # System files
    "*.dll", "*.exe", "*.so", "*.dylib"
)

# Get all files matching the extensions recursively, excluding .git directories
$filesToMove = Get-ChildItem -Path $sourceBase -Recurse -Include $extensions -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.Extension -ne '.ipynb' -and 
        $_.FullName -notmatch '\\.git\\' -and
        $_.FullName -notmatch 'node_modules\\.bin'  # Don't move .bin files in node_modules
    }

# Add large text files (>1MB) to the files to move
$largeTextFiles = Get-ChildItem -Path $sourceBase -Recurse -Include @("*.txt", "*.log") -ErrorAction SilentlyContinue | 
    Where-Object { $_.Length -gt 1MB }
$filesToMove = @($filesToMove) + @($largeTextFiles)

# Remove any duplicate files that might be included in both lists
$filesToMove = $filesToMove | Sort-Object FullName -Unique

# Find directories to remove after moving their contents
$dirsToRemove = @("node_modules", "dist", "build", ".next", ".nuxt", "venv*", "env*", 
                 ".venv*", "__pycache__", ".pytest_cache", ".mypy_cache", ".gradle", ".m2")

# Get all directories that match our patterns
$directoriesToProcess = $dirsToRemove | ForEach-Object {
    Get-ChildItem -Path $sourceBase -Directory -Recurse -Filter $_ -ErrorAction SilentlyContinue
} | Sort-Object FullName -Unique

# Add specific files we want to move (like large files we know about)
$specificFiles = @(
    "01.frontend.rar",
    "Market-Research-main.zip",
    "bfg.jar"
) | ForEach-Object {
    Get-Item -Path (Join-Path $sourceBase $_) -ErrorAction SilentlyContinue
} | Where-Object { $_ -ne $null }

$filesToMove = @($filesToMove) + @($specificFiles) | Sort-Object FullName -Unique

if ($filesToMove.Count -eq 0 -and $directoriesToProcess.Count -eq 0) {
    Write-Host "No files or directories to process in $sourceBase."
    exit
}

Write-Host "Found $($filesToMove.Count) files to move from $sourceBase to $destBase"

# Move files
foreach ($file in $filesToMove) {
    try {
        # Skip directories (handled separately)
        if ($file.PSIsContainer) {
            continue
        }
        
        # Skip if file doesn't exist (might have been moved already)
        if (-not (Test-Path $file.FullName)) {
            continue
        }
        
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
        Move-Item -Path $file.FullName -Destination $destPath -Force -ErrorAction Stop
    }
    catch {
        Write-Host "Error moving $($file.FullName): $_" -ForegroundColor Red
    }
}

# Process directories (move their contents and then remove the directories)
foreach ($dir in $directoriesToProcess) {
    try {
        # Skip if directory doesn't exist or is empty
        if (-not (Test-Path $dir.FullName) -or (Get-ChildItem -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
            continue
        }
        
        # Get the relative path from the source base
        $relativePath = $dir.FullName.Substring($sourceBase.Length + 1)
        
        # Create the destination directory
        $destDir = Join-Path $destBase $relativePath
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        # Move all items from the source directory to the destination
        Write-Host "Moving contents of $($dir.FullName) to $destDir"
        Get-ChildItem -Path $dir.FullName -Force | Move-Item -Destination $destDir -Force -ErrorAction Stop
        
        # Remove the now-empty directory
        Write-Host "Removing empty directory: $($dir.FullName)"
        Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction Stop
    }
    catch {
        Write-Host "Error processing directory $($dir.FullName): $_" -ForegroundColor Red
    }
}

# Clean up empty directories
Get-ChildItem -Path $sourceBase -Recurse -Directory | 
    Where-Object { (Get-ChildItem -Path $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue).Count -eq 0 } | 
    Sort-Object -Property FullName -Descending | 
    ForEach-Object {
        try {
            Remove-Item -Path $_.FullName -Force -ErrorAction Stop
            Write-Host "Removed empty directory: $($_.FullName)"
        }
        catch {
            Write-Host "Error removing empty directory $($_.FullName): $_" -ForegroundColor Red
        }
    }

Write-Host "All support files and directories have been moved/cleaned up successfully!"
Write-Host "Moved $($filesToMove.Count) files in total"
Write-Host "Source: $sourceBase"
Write-Host "Destination: $destBase"
