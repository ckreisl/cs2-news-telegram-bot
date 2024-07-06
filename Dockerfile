FROM python:3.11-slim

RUN apt-get update && apt-get install -y sqlite3

RUN groupadd -g 1000 dev && \
    useradd -u 1000 -g dev -m dev

USER dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY cs2posts/ cs2posts/
COPY main.py .

CMD [ "python", "main.py" ]
