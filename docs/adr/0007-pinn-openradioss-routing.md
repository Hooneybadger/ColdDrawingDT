# ADR 0007 - PINN first, OpenRadioss on NEED_FEA

## Context

The deployed PINN already returns `SAFE`, `UNSAFE`, or `NEED_FEA` plus physics-related indicators.

## Decision

Treat PINN `NEED_FEA` as the main high-fidelity route, plus data-quality and site policy. `SAFE` and `UNSAFE` may finalize without FEA when policy allows.
