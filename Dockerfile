FROM python:3.12-slim

LABEL version="1.0" description="CS2 News Telegram Bot"

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 dev && \
    useradd -u 1000 -g dev -m dev

WORKDIR /app
RUN chown dev:dev /app

USER dev

COPY --chown=dev:dev requirements.txt .

ENV PATH="/home/dev/.local/bin:${PATH}"
RUN pip install --upgrade pip \
    && pip install --user --no-cache-dir -r requirements.txt

COPY --chown=dev:dev cs2posts/ cs2posts/
COPY --chown=dev:dev main.py .

HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD python -m cs2posts.healthcheck

CMD ["python", "main.py"]
