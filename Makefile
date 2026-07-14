# ============================================================
# Prabhu AI Studio — Developer Makefile
#
# WHY a Makefile?
#   Provides short, memorable commands for common dev tasks.
#   Every developer runs the same commands regardless of their
#   shell or OS (make is available on Linux, macOS, WSL).
#
# Usage: make <target>
#   make up          — start all Docker services
#   make down        — stop all Docker services
#   make migrate     — run database migrations
#   make test        — run backend test suite
#   make lint        — lint and type-check backend
#   make seed        — seed the database with sample data
#   make logs        — follow all container logs
# ============================================================

.PHONY: help up down restart build migrate rollback test lint format \
        seed logs shell-backend shell-db clean reset

# Default target: show help
help:
	@echo ""
	@echo "  Prabhu AI Studio — Developer Commands"
	@echo "  ======================================"
	@echo ""
	@echo "  Infrastructure:"
	@echo "    make up          Start all services (detached)"
	@echo "    make down        Stop all services"
	@echo "    make restart     Restart all services"
	@echo "    make build       Rebuild Docker images"
	@echo "    make logs        Follow container logs"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate     Apply all pending migrations"
	@echo "    make rollback    Rollback the last migration"
	@echo "    make seed        Seed database with sample data"
	@echo ""
	@echo "  Development:"
	@echo "    make test        Run backend test suite with coverage"
	@echo "    make lint        Run ruff + mypy"
	@echo "    make format      Auto-format code with ruff"
	@echo "    make shell-backend  Open shell in backend container"
	@echo "    make shell-db       Open psql in postgres container"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean       Remove __pycache__ and .pyc files"
	@echo "    make reset       Stop, remove volumes, and restart fresh"
	@echo ""

# ----------------------------
# Infrastructure
# ----------------------------

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

# ----------------------------
# Database
# ----------------------------

migrate:
	docker compose exec backend alembic upgrade head

rollback:
	docker compose exec backend alembic downgrade -1

seed:
	docker compose exec backend python scripts/seed.py

# ----------------------------
# Testing & Quality
# ----------------------------

test:
	docker compose exec backend pytest

test-unit:
	docker compose exec backend pytest tests/unit/ -v

test-api:
	docker compose exec backend pytest tests/api/ -v

test-integration:
	docker compose exec backend pytest tests/integration/ -v

lint:
	docker compose exec backend ruff check app/
	docker compose exec backend mypy app/

format:
	docker compose exec backend ruff format app/

# ----------------------------
# Shells
# ----------------------------

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U prabhu -d prabhu_ai_studio

# ----------------------------
# Cleanup
# ----------------------------

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	find . -name ".coverage" -delete 2>/dev/null; true

reset:
	docker compose down -v
	docker compose up -d
	sleep 5
	docker compose exec backend alembic upgrade head
