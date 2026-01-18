# Cleanup script to remove outdated documentation files

$rootDir = 'c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel'

Write-Host "Starting cleanup of root directory..."

# Get all markdown files from root
$mdFiles = Get-ChildItem -Path $rootDir -Filter '*.md' -File | Where-Object { 
    $_.Name -notlike 'README*.md'
}

Write-Host "Found $($mdFiles.Count) markdown files to delete"

# Delete each file
$deleted = 0
$mdFiles | ForEach-Object {
    try {
        Remove-Item -Path $_.FullName -Force -ErrorAction Stop
        Write-Host "Deleted: $($_.Name)"
        $deleted++
    }
    catch {
        Write-Host "Failed to delete $($_.Name): $_"
    }
}

Write-Host "Deleted $deleted markdown files"

# Clean up Python test files from root
$pyFiles = Get-ChildItem -Path $rootDir -Filter '*.py' -File | Where-Object {
    $_.Name -like 'test_*.py' -or 
    $_.Name -like 'validate_*.py' -or 
    $_.Name -like 'STEP*.py' -or 
    $_.Name -like 'SESSION*.py' -or
    $_.Name -eq 'run_tests.py'
}

Write-Host "Found $($pyFiles.Count) Python test files to delete"

$deleted = 0
$pyFiles | ForEach-Object {
    try {
        Remove-Item -Path $_.FullName -Force -ErrorAction Stop
        Write-Host "Deleted: $($_.Name)"
        $deleted++
    }
    catch {
        Write-Host "Failed to delete $($_.Name): $_"
    }
}

Write-Host "Deleted $deleted Python test files"

Write-Host "`nCleanup complete!"
Write-Host "Remaining root markdown files:"
Get-ChildItem -Path $rootDir -Filter '*.md' -File
