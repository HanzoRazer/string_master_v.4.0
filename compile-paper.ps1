# Zone-Tritone Canon Paper Compilation Script
# Compiles the academic LaTeX paper to PDF

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Zone-Tritone System - Academic Paper Builder   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if pdflatex is available
$pdflatex = Get-Command pdflatex -ErrorAction SilentlyContinue

if (-not $pdflatex) {
    Write-Host "ERROR: pdflatex not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install a LaTeX distribution:" -ForegroundColor Yellow
    Write-Host "  - Windows: MiKTeX from https://miktex.org/" -ForegroundColor Yellow
    Write-Host "  - macOS:   brew install --cask mactex" -ForegroundColor Yellow
    Write-Host "  - Linux:   sudo apt install texlive-full" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Navigate to papers directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$papersPath = Join-Path $scriptPath "papers"

if (-not (Test-Path $papersPath)) {
    Write-Host "ERROR: papers/ directory not found!" -ForegroundColor Red
    exit 1
}

Set-Location $papersPath
Write-Host "Working directory: $papersPath" -ForegroundColor Gray
Write-Host ""

# Compile the paper (run twice for cross-references)
Write-Host "Compiling zone_tritone_canon.tex..." -ForegroundColor Green
Write-Host ""

Write-Host "[Pass 1/2] First compilation..." -ForegroundColor Yellow
& pdflatex -interaction=nonstopmode zone_tritone_canon.tex | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: First compilation failed!" -ForegroundColor Red
    Write-Host "Check zone_tritone_canon.log for details" -ForegroundColor Yellow
    exit 1
}

Write-Host "[Pass 2/2] Second compilation (for cross-references)..." -ForegroundColor Yellow
& pdflatex -interaction=nonstopmode zone_tritone_canon.tex | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Second compilation failed!" -ForegroundColor Red
    Write-Host "Check zone_tritone_canon.log for details" -ForegroundColor Yellow
    exit 1
}

# Check if PDF was generated
if (Test-Path "zone_tritone_canon.pdf") {
    Write-Host ""
    Write-Host "SUCCESS! Paper compiled successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "Generated file:" -ForegroundColor Cyan
    Write-Host "  papers/zone_tritone_canon.pdf" -ForegroundColor White
    Write-Host ""
    
    # Get file size
    $pdfFile = Get-Item "zone_tritone_canon.pdf"
    $fileSize = "{0:N2} KB" -f ($pdfFile.Length / 1KB)
    Write-Host "File size: $fileSize" -ForegroundColor Gray
    Write-Host "Last modified: $($pdfFile.LastWriteTime)" -ForegroundColor Gray
    Write-Host ""
    
    # Clean up auxiliary files (optional)
    Write-Host "Cleaning up auxiliary files..." -ForegroundColor Yellow
    Remove-Item -Path "*.aux", "*.log", "*.out" -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "To view the PDF, run:" -ForegroundColor Cyan
    Write-Host "  Start-Process papers\zone_tritone_canon.pdf" -ForegroundColor White
    Write-Host ""
    
} else {
    Write-Host "ERROR: PDF was not generated!" -ForegroundColor Red
    Write-Host "Check zone_tritone_canon.log for compilation errors" -ForegroundColor Yellow
    exit 1
}

Write-Host "==================================================" -ForegroundColor Cyan
