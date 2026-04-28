# Test and validation

Terms: [glossary](glossary.md).

This version runs one check: `scripts/validate_contracts.py`. The lists below are the tests later phases must add.

## Current check

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_contracts.py
```

It parses YAML, checks Asset IDs, and validates Snapshot and Decision examples.

