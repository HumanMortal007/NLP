# CreatorGPT Quick Start Script
# This script helps you get started quickly

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CreatorGPT Setup & Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "1. Initial Setup (Install dependencies)" -ForegroundColor White
Write-Host "2. Run Complete Analysis Pipeline" -ForegroundColor White
Write-Host "3. Start API Server Only" -ForegroundColor White
Write-Host "4. Start Frontend Only" -ForegroundColor White
Write-Host "5. Start API Server + Frontend" -ForegroundColor White
Write-Host "6. View Results" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
        
        # Check if venv exists
        if (-Not (Test-Path "venv")) {
            Write-Host "Creating virtual environment..." -ForegroundColor Yellow
            python -m venv venv
        }
        
        # Activate venv
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & ".\venv\Scripts\Activate.ps1"
        
        # Install Python packages
        Write-Host "Installing Python packages..." -ForegroundColor Yellow
        pip install -r requirements.txt
        
        # Check Node.js
        Write-Host "`nChecking Node.js installation..." -ForegroundColor Yellow
        try {
            $nodeVersion = node --version
            Write-Host "✓ Node.js $nodeVersion found" -ForegroundColor Green
            
            # Install frontend dependencies
            if (Test-Path "frontend/package.json") {
                Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
                Set-Location frontend
                npm install
                Set-Location ..
                Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
            }
        } catch {
            Write-Host "⚠ Node.js not found. Skipping frontend setup." -ForegroundColor Yellow
        }
        
        # Create .env from example
        if (-Not (Test-Path ".env")) {
            Write-Host "`nCreating .env file from template..." -ForegroundColor Yellow
            Copy-Item ".env.example" ".env"
            Write-Host "✓ .env file created" -ForegroundColor Green
            Write-Host "⚠ Please edit .env and add your API keys!" -ForegroundColor Yellow
        }
        
        Write-Host "`n✓ Setup complete!" -ForegroundColor Green
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Edit .env file with your API keys" -ForegroundColor White
        Write-Host "2. Run this script again and choose option 2" -ForegroundColor White
    }
    
    "2" {
        Write-Host "`nRunning complete analysis pipeline..." -ForegroundColor Yellow
        
        # Activate venv
        & ".\venv\Scripts\Activate.ps1"
        
        # Run pipeline
        python main_pipeline.py
        
        Write-Host "`n✓ Analysis complete!" -ForegroundColor Green
        Write-Host "Results are in:" -ForegroundColor Cyan
        Write-Host "  - data/outputs/ (CSV and reports)" -ForegroundColor White
        Write-Host "  - data/visualizations/ (charts)" -ForegroundColor White
    }
    
    "3" {
        Write-Host "`nStarting API server..." -ForegroundColor Yellow
        
        # Activate venv
        & ".\venv\Scripts\Activate.ps1"
        
        # Start API
        Set-Location backend
        Write-Host "API server starting at http://localhost:8000" -ForegroundColor Green
        Write-Host "API docs available at http://localhost:8000/docs" -ForegroundColor Cyan
        uvicorn api:app --reload --host 0.0.0.0 --port 8000
    }
    
    "4" {
        Write-Host "`nStarting frontend..." -ForegroundColor Yellow
        
        Set-Location frontend
        Write-Host "Frontend starting..." -ForegroundColor Green
        npm run dev
    }
    
    "5" {
        Write-Host "`nStarting API server and frontend..." -ForegroundColor Yellow
        Write-Host "⚠ This will open two terminal windows" -ForegroundColor Yellow
        
        # Start API in new window
        Start-Process pwsh -ArgumentList "-NoExit", "-Command", "& '.\venv\Scripts\Activate.ps1'; cd backend; uvicorn api:app --reload --host 0.0.0.0 --port 8000"
        
        # Wait a bit for API to start
        Start-Sleep -Seconds 3
        
        # Start frontend in new window
        Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
        
        Write-Host "`n✓ Services started!" -ForegroundColor Green
        Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
    }
    
    "6" {
        Write-Host "`nOpening results folders..." -ForegroundColor Yellow
        
        if (Test-Path "data/outputs") {
            explorer "data/outputs"
        }
        
        if (Test-Path "data/visualizations") {
            explorer "data/visualizations"
        }
        
        Write-Host "✓ Results folders opened" -ForegroundColor Green
    }
    
    default {
        Write-Host "Invalid choice. Please run the script again." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Thank you for using CreatorGPT!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
