#!/usr/bin/env bash
# ============================================================
# Prabhu AI Studio — Linux/macOS Setup Script
# Run: bash scripts/setup.sh
# ============================================================

set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m"

log() { echo -e "${CYAN}[Prabhu Setup]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

log "Prabhu AI Studio — Setup"
echo "==============================="

# Prerequisites
log "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || error "Docker not found. Install Docker first."
command -v python3 >/dev/null 2>&1 || error "Python 3 not found. Install Python 3.12+."
command -v node >/dev/null 2>&1 || error "Node.js not found. Install Node.js 20+."
success "Docker, Python3, and Node.js found."

# .env
log "Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    success ".env created from .env.example"
    warn "IMPORTANT: Edit .env and change APP_SECRET_KEY and JWT_SECRET_KEY!"
else
    success ".env already exists, skipping."
fi

# Media directories
log "Creating media and model directories..."
mkdir -p backend/media/{images,audio,videos,transcripts}
mkdir -p models/{llm,sd,tts}
success "Directories created."

# Docker services
log "Starting Docker services (postgres + redis)..."
docker compose up -d postgres redis
echo "  Waiting for PostgreSQL..."
sleep 5
success "Docker services started."

# Backend
log "Setting up Python backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt
success "Python dependencies installed."
cd ..

# Frontend
log "Setting up Node.js frontend..."
cd frontend
npm install --silent
success "Node.js dependencies installed."
cd ..

echo ""
echo "==============================="
success "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your secret keys"
echo "  2. docker compose exec backend alembic upgrade head"
echo "  3. docker compose up"
echo "  4. Open http://localhost:3000"
