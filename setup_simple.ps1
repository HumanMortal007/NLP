# Simple Setup Script for YouTube Comment Analyzer

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "YouTube Comment Analyzer - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Yellow
Write-Host ""

# Activate venv if exists
if (Test-Path "venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
}

# Install packages
Write-Host "`nInstalling packages (this may take a few minutes)..." -ForegroundColor Cyan

$packages = @(
    "google-api-python-client",
    "google-generativeai", 
    "transformers",
    "torch",
    "pandas",
    "matplotlib",
    "seaborn"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    pip install $package --quiet
}

Write-Host "`n✓ All packages installed!" -ForegroundColor Green

# Create directories
Write-Host "`nCreating output directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "nlp\analysis_results" | Out-Null
New-Item -ItemType Directory -Force -Path "nlp\visualizations" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the analyzer:" -ForegroundColor Yellow
Write-Host "  python nlpv_id.py" -ForegroundColor White
Write-Host ""
Write-Host "Your API keys are already configured in the file." -ForegroundColor Cyan
Write-Host "Results will be saved in:" -ForegroundColor Cyan
Write-Host "  - nlp/analysis_results/" -ForegroundColor White
Write-Host "  - nlp/visualizations/" -ForegroundColor White
Write-Host ""
