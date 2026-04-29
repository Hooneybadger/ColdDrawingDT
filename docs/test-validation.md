# Test and validation

Terms: [glossary](glossary.md).

This version runs one check: `scripts/validate_contracts.py`. The lists below are the tests later phases must add.

## Current check

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_contracts.py
```

It parses YAML, checks Asset IDs, and validates Snapshot and Decision examples.

## Unit tests later

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

