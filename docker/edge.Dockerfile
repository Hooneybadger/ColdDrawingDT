FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
COPY workers /app/workers
COPY config /app/config
COPY schemas /app/schemas

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src:/app
CMD ["python", "-m", "cold_drawing_twin.edge.opcua.adapter"]
