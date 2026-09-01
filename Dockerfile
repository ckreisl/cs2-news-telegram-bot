FROM ghcr.io/astral-sh/uv:0.11.6 AS uv

FROM python:3.14-slim AS builder

COPY --from=uv /uv /usr/local/bin/uv

# UV_PYTHON_DOWNLOADS=never pins the venv to the base image's interpreter, so it
# stays valid when copied into the runtime stage.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Only the lockfile is needed to build /app/.venv; keeping the source out of
# this layer means dependencies are re-installed only when uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project


FROM python:3.14-slim

LABEL version="1.0" description="CS2 News Telegram Bot"

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 dev && \
    useradd -u 1000 -g dev -m dev

WORKDIR /app
RUN chown dev:dev /app

USER dev

# uv is a build-time tool only; the runtime image just runs the prebuilt venv.
COPY --from=builder --chown=dev:dev /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

COPY --chown=dev:dev cs2posts/ cs2posts/
COPY --chown=dev:dev main.py .

HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD python -m cs2posts.healthcheck

CMD ["python", "main.py"]
