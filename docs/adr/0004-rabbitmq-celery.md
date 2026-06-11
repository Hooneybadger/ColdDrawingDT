# ADR 0004 - RabbitMQ and Celery for FEA work

## Context

FEA is long-running. It must not hold an HTTP request open. It must survive worker restarts.

## Decision

Use RabbitMQ as the durable work broker and Celery workers for FEA jobs, with late acknowledgement, low prefetch, and idempotent job rows.

## Rejected

Kafka is not selected. The need is durable work distribution, not high-volume replay for many independent consumers.
