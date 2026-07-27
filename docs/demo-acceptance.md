# Demo and acceptance

Terms: [glossary](glossary.md).

## What you can run now

```bash
python -m pip install -e ".[dev]"
python scripts/validate_contracts.py
python scripts/render_factory_layout.py
make test
make factory-stage
```

PINN files (not in git):

```bash
make fetch-pinn
make model-verify
make demo-fast
```

FEA mesh and decks (OpenRadioss solve needs site binaries and a calibrated hardening map):

```bash
make fea-smoke
make demo-fea
```

## Executable checks

### A. Model

```bash
make model-verify
```

Runs the released PINN locally with the glossary feature order and prints verdict, indicators, and model version.

### B. FEA

```bash
make fea-smoke
```

Runs Gmsh and writes OpenRadioss decks. A full Engine run needs binaries. Automatic SAFE/UNSAFE cannot pass while `required_thresholds` is empty.

### C. Fast Decision

```bash
make demo-fast
```

Fresh Digital Twin -> Snapshot -> PINN SAFE or UNSAFE -> finalized Decision without FEA, or NEED_FEA -> FEA job.

### D. FEA Decision

```bash
make demo-fea
```

Forces the NEED_FEA path, queues a job, runs the pipeline, and stores Manual review while thresholds and the hardening curve are empty.

### E. 3D

```bash
make factory-stage
make demo-stream
```

`factory-stage` writes the OpenUSD factory. `demo-stream` reminds you to launch the operator Kit app on the RTX host. Streaming failure must not change a stored Decision.

## Golden demo script

Use Drawing 4 and the demo Snapshot numbers `0.3, 0.2, 0.08, 0.7`.

1. Senior app opens the 96 x 41.13 m factory.
2. Select `BG.MIEUM.DRW.04` and show live Digital Twin state.
3. Run a fast-path Evaluation and show Snapshot, model, and policy Lineage.
4. Apply a condition where PINN returns `NEED_FEA`.
5. Show job states `QUEUED -> RUNNING -> POSTPROCESSING -> FINALIZED` or Manual review.
6. Show FEA deformation and critical region when solver output exists.
7. Open Decision Lineage and versions.
8. Move to a historical timeline without changing live state.
9. Open operator view in Chromium over WebRTC on the RTX host.
10. Show FEA failure or timeout -> `MANUAL_REVIEW`.

## Architecture gates

- No database access from Omniverse clients
- No synchronous FEA inside an HTTP request when `FEA_EXECUTION=celery`
- No Scenario overwrite of live state
- No SAFE fallback from failed or inconclusive required FEA
- No raw hardening scalar treated as a physical unit
- No unversioned safety threshold
