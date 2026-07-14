# ============================================================
# Prabhu AI Studio — Windows Setup Script (PowerShell)
# Run: .\scripts\setup.ps1
# ============================================================

param(
    [switch]$SkipDocker,
    [switch]$DevMode
)

$ErrorActionPreference = "Stop"

Write-Host "🎬 Prabhu AI Studio — Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Check prerequisites
Write-Host "`n[1/5] Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed. Please install Docker Desktop first."
    exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed. Please install Python 3.12+."
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed. Please install Node.js 20+."
    exit 1
}

Write-Host "✓ Docker, Python, and Node.js found." -ForegroundColor Green

# Set up .env
Write-Host "`n[2/5] Setting up environment file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env created from .env.example" -ForegroundColor Green
    Write-Host "  ⚠ IMPORTANT: Edit .env and change APP_SECRET_KEY and JWT_SECRET_KEY!" -ForegroundColor Red
} else {
    Write-Host "✓ .env already exists, skipping." -ForegroundColor Green
}

# Create media directories
Write-Host "`n[3/5] Creating media directories..." -ForegroundColor Yellow
$mediaDirs = @("backend\media\images", "backend\media\audio", "backend\media\videos", "backend\media\transcripts", "models\llm", "models\sd", "models\tts")
foreach ($dir in $mediaDirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
Write-Host "✓ Media and model directories created." -ForegroundColor Green

# Start Docker services
if (-not $SkipDocker) {
    Write-Host "`n[4/5] Starting Docker services..." -ForegroundColor Yellow
    docker compose up -d postgres redis
    Write-Host "  Waiting for PostgreSQL to be ready..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
    Write-Host "✓ Docker services started." -ForegroundColor Green
}

# Backend setup
Write-Host "`n[5/5] Setting up Python backend..." -ForegroundColor Yellow
Push-Location backend
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .venv\Scripts\pip install -r requirements.txt -q
& .venv\Scripts\pip install -r requirements-dev.txt -q
Write-Host "✓ Python dependencies installed." -ForegroundColor Green
Pop-Location

# Frontend setup
Write-Host "`n[6/6] Setting up Node.js frontend..." -ForegroundColor Yellow
Push-Location frontend
npm install --silent
Write-Host "✓ Node.js dependencies installed." -ForegroundColor Green
Pop-Location

Write-Host "`n=============================" -ForegroundColor Cyan
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Edit .env with your secret keys" -ForegroundColor White
Write-Host "  2. Run: docker compose exec backend alembic upgrade head" -ForegroundColor White
Write-Host "  3. Run: docker compose up" -ForegroundColor White
Write-Host "  4. Open: http://localhost:3000" -ForegroundColor White
