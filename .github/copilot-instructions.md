# Project Guidelines

## Overview

Telegram bot that delivers Counter-Strike 2 news, updates, and external announcements by crawling the Steam Web API. Built with `python-telegram-bot`, `aiosqlite`, `beautifulsoup4`, and `requests`.

## Code Style

- Python 3.12 (runtime & Docker), target 3.12+ syntax (`pyupgrade --py312-plus`)
- Always include `from __future__ import annotations` as the first import
- Import order enforced by `reorder-python-imports` (stdlib → third-party → local)
- Formatting via `autopep8`; line length is not enforced (`flake8 --ignore=E501`)
- Use type hints on all function signatures and return types
- Naming: `PascalCase` classes, `snake_case` functions/methods, `UPPER_SNAKE_CASE` constants/enum values
- Private attributes use name mangling (`__attribute`), expose via `@property`
- Use abstract base classes for extensible interfaces (e.g., `WebCrawler`, `Database`, `Parser`)

## Design Principles

- **SOLID**: Follow Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion principles
- **Layered architecture**: Separate data layer (`db/`, `dto/`), business logic (`cs2posts.py`, `crawler.py`, `parser/`), and presentation (`bot/`, `msg/`). Keep layers decoupled — business logic must not depend on bot framework specifics.
- **Readability over cleverness**: Prefer clear, well-named public methods over deeply nested private helpers. Minimize private functions — extract logic into dedicated classes or modules instead.
- **Testability**: Design classes and functions so they can be tested in isolation. Inject dependencies rather than hard-coding them. Every new feature or bug fix should include corresponding tests.
- **Security**: Validate and sanitize all external inputs (user commands, API responses). Never log or expose secrets. Follow OWASP best practices for input handling.

## Architecture

- **`cs2posts/bot/`** — Bot orchestration, command handlers, spam protection, settings (presentation layer)
- **`cs2posts/crawler.py`** — Async Steam API client (data access layer)
- **`cs2posts/cs2posts.py`** — Post filtering and categorization: NEWS, UPDATE, EXTERNAL (business logic layer)
- **`cs2posts/db/`** — ORM-less async SQLite via `aiosqlite` with direct SQL queries (data access layer)
- **`cs2posts/dto/`** — Data transfer objects (`Post`, `Chat`) with `from_dict()`/`to_dict()` (data layer)
- **`cs2posts/msg/`** — Telegram message construction using factory pattern, `TelegramMessageFactory` (presentation layer)
- **`cs2posts/parser/`** — BBCode/HTML to Telegram HTML conversion pipeline (business logic layer)
- **`cs2posts/content/`** — Rich content extraction: video, images, YouTube (business logic layer)

Key patterns:
- Factory pattern for message creation (`TelegramMessageFactory.create(post)`)
- Decorator-based middleware (`@spam_protected`, `@admin`) for command handlers
- All I/O operations are `async/await`; use `asyncio.to_thread()` for blocking calls
- Long messages (>4096 chars) are automatically split at newline boundaries

## Build and Test

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
python -m pytest -v --cov-report=term-missing --cov=cs2posts tests/

# Lint
flake8 cs2posts tests

# Pre-commit hooks (pyupgrade, reorder-python-imports, autopep8, flake8)
pre-commit run --all-files

# Run bot locally (requires .env with TELEGRAM_TOKEN)
python main.py
```

## Conventions

- Database layer uses raw SQL with `aiosqlite` — no ORM. DTOs handle serialization.
- Configuration loaded from environment variables via `python-dotenv` in `cs2posts/bot/settings.py`.
- Tests live in `tests/` using `pytest` + `pytest-asyncio`. Async tests use `@pytest.mark.asyncio`. Mock external dependencies with `unittest.mock.patch`.
- Use `@pytest.fixture` (and `@pytest_asyncio.fixture` for async) for reusable test data. Use `autouse=True` fixtures to reset shared state (e.g., LRU caches) between tests.
- CI runs on GitHub Actions (Python 3.12, Ubuntu) — see `.github/workflows/ci.yml`.
