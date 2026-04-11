PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
DOCKER_IMAGE ?= cs2-news-bot

.DEFAULT_GOAL := help

.PHONY: help venv install install-dev test test-cov lint typecheck check pre-commit run docker-build docker-run clean

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nAvailable targets:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: ## Create a local virtual environment in .venv
	$(PYTHON) -m venv .venv

install: ## Install runtime dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

lint: ## Run flake8 lint checks
	$(PYTHON) -m flake8 cs2posts tests

typecheck: ## Run mypy type checks
	$(PYTHON) -m mypy cs2posts

test: ## Run test suite
	$(PYTHON) -m pytest -v tests/

test-cov: ## Run tests with coverage for cs2posts
	$(PYTHON) -m pytest -v --cov-report=term-missing --cov=cs2posts tests/

check: lint test ## Run lint and tests

pre-commit: ## Run pre-commit hooks on all files
	$(PYTHON) -m pre_commit run --all-files

run: ## Run the Telegram bot locally
	$(PYTHON) main.py

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run Docker container with .env and named volumes
	docker run -d \
		-v backups:/app/backups/ \
		-v database:/app/database \
		--env-file .env \
		--name $(DOCKER_IMAGE) \
		$(DOCKER_IMAGE)

clean: ## Remove common local cache artifacts
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name ".coverage" \) -delete
