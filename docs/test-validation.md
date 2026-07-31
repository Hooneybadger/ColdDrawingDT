# Test and validation

Terms: [glossary](glossary.md).

This version runs contract checks and pytest.

## Current checks

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_contracts.py
python -m pip install -e ".[dev]"
make test
```

## Unit tests

Feature and model:

- Canonical feature order
- Range boundaries
- `confidence=null` meaning
- Model version parsing

Routing:

- SAFE path
- UNSAFE path
- NEED_FEA path
- Stale Digital Twin
- Missing required field
- Model unavailable

FEA mapping:

- Reduction ratio to final radius
- Die-angle geometry
- Friction mapping
- Hardening mapping version
- Idempotency key

Postprocess:

- Solver success but quality fail -> `INCONCLUSIVE`
- Safety criterion version applied

## Integration tests

- OPC UA source -> AAS update
- AAS update -> Timescale history
- Snapshot -> real PINN
- Queue -> worker lifecycle
- Gmsh -> OpenRadioss smoke case
- FEA result -> Decision store
- Decision -> Digital Twin result
- Event -> Omniverse state

## End-to-end cases

Use Drawing 4 and the demo Snapshot numbers unless a case says otherwise.

| ID | Story |
|---|---|
| E2E-1 | Fresh in-range input -> PINN SAFE -> Decision without FEA |
| E2E-2 | Fresh in-range input -> PINN UNSAFE -> Decision without extra FEA unless policy requires it |
| E2E-3 | PINN NEED_FEA -> OpenRadioss -> criterion -> Decision |
| E2E-4 | Out of PINN range -> FEA or Manual review per policy; no undefined PINN call |
| E2E-5 | FEA required and solver fails -> Manual review |
| E2E-6 | Stale required state -> no automatic final Decision |
| E2E-7 | Scenario override -> operational Digital Twin unchanged |

## Science checks later

FEA:

- Mesh convergence
- Quasi-static energy quality
- Simple reference problem when possible
- Sensitivity direction checks

System:

- Repeat the same Snapshot and config; compare checksums and metrics inside a stated tolerance

## Performance later

Track separately:

- PINN P50 and P95
- API overhead
- FEA queue wait
- FEA runtime
- WebRTC session start
- Concurrent operator stream GPU cost

Do not average PINN and FEA latency into one number.
