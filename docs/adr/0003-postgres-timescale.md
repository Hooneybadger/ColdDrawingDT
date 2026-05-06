# ADR 0003 - PostgreSQL with TimescaleDB

## Context

The system needs relational Decision Lineage and time-indexed process history.

## Decision

Use PostgreSQL with the TimescaleDB extension so both models stay in one database system. History uses hypertables.
