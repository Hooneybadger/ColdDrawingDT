# ADR 0008 - Docker Compose first

## Context

The first target is one on-site factory.

## Decision

Use Docker Compose for service deploy and NVIDIA Container Toolkit for GPU containers. Revisit Kubernetes only when high availability, multi-node scheduling, or session and worker scale is a concrete need.
