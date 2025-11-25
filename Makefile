.PHONY: help install install-dev init-db backfill-data run-api run-tests lint format docker-build docker-up docker-down clean

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose -f docker/docker-compose.yml

help:
	@echo "Vietnam Quant Platform - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo "  make run-api          Run FastAPI server locally"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Run linters (flake8, mypy, pylint)"
	@echo "  make run-tests        Run all tests with coverage"
	@echo ""
	@echo "Database:"
	@echo "  make init-db          Initialize database schema"
	@echo "  make backfill-data    Backfill historical data"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker images"
	@echo "  make docker-up        Start all Docker services"
	@echo "  make docker-down      Stop all Docker services"
	@echo "  make docker-logs      View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Clean temporary files and caches"

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt
	pre-commit install

init-db:
	$(PYTHON) scripts/init_db.py

backfill-data:
	$(PYTHON) scripts/backfill_data.py

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-tests:
	pytest src/tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ --max-line-length=100 --exclude=__pycache__,*.pyc
	mypy src/ --ignore-missing-imports
	pylint src/ --max-line-length=100 --disable=C0111,R0903

format:
	black src/ scripts/ --line-length=100
	isort src/ scripts/ --profile=black

docker-build:
	$(DOCKER_COMPOSE) build

docker-up:
	$(DOCKER_COMPOSE) up -d
	@echo "Services starting..."
	@echo "API will be available at http://localhost:8000"
	@echo "API docs at http://localhost:8000/docs"
	@echo "pgAdmin at http://localhost:5050 (if dev profile enabled)"

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

docker-restart:
	$(DOCKER_COMPOSE) restart

docker-ps:
	$(DOCKER_COMPOSE) ps

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/
	@echo "Cleaned temporary files and caches"

test-unit:
	pytest src/tests/unit/ -v

test-integration:
	pytest src/tests/integration/ -v

dev-setup: install-dev init-db
	@echo "Development environment setup complete!"
	@echo "Run 'make docker-up' to start services"
	@echo "Run 'make backfill-data' to load initial data"
