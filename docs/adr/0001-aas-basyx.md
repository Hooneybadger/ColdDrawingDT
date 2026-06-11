# ADR 0001 - AAS 3.x and Eclipse BaSyx

## Context

Several services need one shared meaning for each Asset and its live state.

## Options

- Custom JSON APIs only
- A generic Digital Twin framework
- AAS with BaSyx

## Decision

Use AAS 3.x with Eclipse BaSyx for the Digital Twin meaning layer.

## Trade-off

We operate an extra industrial runtime. We do not invent our own asset API.
