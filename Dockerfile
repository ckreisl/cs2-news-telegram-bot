FROM python:3.12-slim

RUN apt-get update && apt-get install -y sqlite3

RUN groupadd -g 1000 dev && \
    useradd -u 1000 -g dev -m dev

WORKDIR /app
RUN chown dev:dev /app

USER dev

COPY --chown=dev:dev requirements.txt .

ENV PATH="/home/dev/.local/bin:${PATH}"
RUN pip install --user --no-cache-dir -r requirements.txt

COPY --chown=dev:dev cs2posts/ cs2posts/
COPY --chown=dev:dev main.py .

CMD [ "python", "main.py" ]
