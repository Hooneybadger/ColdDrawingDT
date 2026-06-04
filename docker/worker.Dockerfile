FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends gmsh && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
COPY workers /app/workers
COPY config /app/config
COPY schemas /app/schemas
COPY omniverse /app/omniverse
COPY usd /app/usd

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src:/app
CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=INFO", "-Q", "fea.default,fea.priority", "--prefetch-multiplier=1"]
