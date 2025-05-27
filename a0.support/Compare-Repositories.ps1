# Define the directories
$originalRepo = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db.original"
$newRepo = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db"

# Get all files from both directories, excluding .git directory
$originalFiles = Get-ChildItem -Path $originalRepo -Recurse -File | 
                Where-Object { $_.FullName -notlike '*\.git\*' } |
                ForEach-Object { $_.FullName.Substring($originalRepo.Length + 1) }

$newFiles = Get-ChildItem -Path $newRepo -Recurse -File | 
           Where-Object { $_.FullName -notlike '*\.git\*' } |
           ForEach-Object { $_.FullName.Substring($newRepo.Length + 1) }

# Find files in original but not in new
$missingFiles = Compare-Object -ReferenceObject $originalFiles -DifferenceObject $newFiles -PassThru | 
               Where-Object { $_.SideIndicator -eq '<=' } |
               Sort-Object

# Display results
if ($missingFiles) {
    Write-Host "Files in original but not in new repository:" -ForegroundColor Yellow
    $missingFiles | ForEach-Object {
        $filePath = $_
        $fullPath = Join-Path $originalRepo $filePath
        $size = (Get-Item $fullPath).Length / 1KB
        $extension = [System.IO.Path]::GetExtension($filePath)
        
        [PSCustomObject]@{
            'File' = $filePath
            'Size (KB)' = [math]::Round($size, 2)
            'Extension' = $extension
        }
    } | Format-Table -AutoSize
} else {
    Write-Host "No files found in original that are missing from the new repository." -ForegroundColor Green
}

# Also check for files that might contain sensitive information
Write-Host "`nChecking for potentially sensitive files in the original repository:" -ForegroundColor Yellow
$sensitivePatterns = @(
    '*.key', '*.pem', '*.p12', '*.pfx', '*.crt', '*.cer', 
    '*.p7b', '*.p7c', '*.p7s', '*.p8', '*.p10', '*.p12', 
    '*.jks', '*.keystore', '*.truststore', '*.jceks',
    '*secret*', '*password*', '*credential*', '*token*',
    '*.json', '*.config', '*.conf', '*.cfg', '*.env', '*.ini'
)

$sensitiveFiles = Get-ChildItem -Path $originalRepo -Include $sensitivePatterns -Recurse -File -ErrorAction SilentlyContinue |
                 Where-Object { $_.FullName -notlike '*\.git\*' } |
                 Select-Object @{Name="RelativePath";Expression={$_.FullName.Substring($originalRepo.Length + 1)}}, 
                              @{Name="Size (KB)";Expression={[math]::Round(($_.Length / 1KB), 2)}},
                              Extension

if ($sensitiveFiles) {
    Write-Host "Potentially sensitive files found in original repository:" -ForegroundColor Red
    $sensitiveFiles | Format-Table -AutoSize
} else {
    Write-Host "No potentially sensitive files found using common patterns." -ForegroundColor Green
}

# Save results to a file
$outputFile = "C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\file_comparison_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$results = @"

=== Files in original but not in new repository ===
$($missingFiles -join "`n")

=== Potentially sensitive files in original repository ===
$($sensitiveFiles | Format-Table -AutoSize | Out-String)

=== Analysis completed at $(Get-Date) ===
"@

$results | Out-File -FilePath $outputFile -Encoding utf8
Write-Host "`nResults saved to: $outputFile" -ForegroundColor Cyan
