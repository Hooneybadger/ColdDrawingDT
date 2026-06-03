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
COPY scripts /app/scripts

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src:/app
EXPOSE 8000
CMD ["uvicorn", "--factory", "cold_drawing_twin.api.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
