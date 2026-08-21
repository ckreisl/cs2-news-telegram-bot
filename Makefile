UV ?= uv
DOCKER_IMAGE ?= cs2-news-bot

.DEFAULT_GOAL := help

.PHONY: help install install-dev sync lock upgrade test test-cov lint format typecheck check pre-commit run docker-build docker-run clean

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nAvailable targets:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Sync .venv with runtime dependencies only
	$(UV) sync --no-dev

install-dev: sync ## Sync .venv with runtime and development dependencies

sync: ## Sync .venv with uv.lock (runtime + dev)
	$(UV) sync

lock: ## Refresh uv.lock from pyproject.toml
	$(UV) lock

upgrade: ## Upgrade locked dependencies to their latest allowed versions
	$(UV) lock --upgrade

lint: ## Run ruff lint checks and verify formatting
	$(UV) run ruff check cs2posts tests
	$(UV) run ruff format --check cs2posts tests

format: ## Apply ruff fixes and formatting
	$(UV) run ruff check --fix cs2posts tests
	$(UV) run ruff format cs2posts tests

typecheck: ## Run mypy type checks
	$(UV) run mypy cs2posts

test: ## Run test suite
	$(UV) run pytest -v tests/

test-cov: ## Run tests with coverage for cs2posts
	$(UV) run pytest -v --cov-report=term-missing --cov=cs2posts tests/

check: lint test ## Run lint and tests

pre-commit: ## Run pre-commit hooks on all files
	$(UV) run pre-commit run --all-files

run: ## Run the Telegram bot locally
	$(UV) run python main.py

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
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name ".coverage" \) -delete
