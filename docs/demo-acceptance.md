# Demo and acceptance

Terms: [glossary](glossary.md).

The commands in this file are **acceptance targets**. They are not implemented in this version except the contract check.

## What you can run now

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_contracts.py
python scripts/render_factory_layout.py
```

You can also open the worked JSON under [examples/](examples/) and the factory picture [images/factory-layout.svg](images/factory-layout.svg).

## Later executable checks

### A. Model

```bash
make model-verify
```

Must run the released PINN locally with the glossary feature order and print verdict, indicators, and model version.

### B. FEA

```bash
make fea-smoke
```

Must run Gmsh and OpenRadioss, parse quality and physics output, and apply the configured criterion. This cannot pass while `required_thresholds` is empty.

### C. Fast Decision

```bash
make demo-fast
```

Fresh Digital Twin -> Snapshot -> PINN SAFE or UNSAFE -> finalized Decision without FEA.

### D. FEA Decision

```bash
make demo-fea
```

Fresh Digital Twin -> PINN NEED_FEA -> queue -> real OpenRadioss -> postprocess -> Decision or Manual review.

### E. 3D

```bash
make factory-stage
make demo-stream
```

Generate the factory stage and use the operator Kit app through WebRTC.

## Golden demo script

Use Drawing 4 and the demo Snapshot numbers `0.3, 0.2, 0.08, 0.7`.

1. Senior app opens the 96 x 41.13 m factory.
2. Select `BG.MIEUM.DRW.04` and show live Digital Twin state.
3. Run a fast-path Evaluation and show Snapshot, model, and policy Lineage.
4. Apply a condition where PINN returns `NEED_FEA`.
5. Show job states `QUEUED -> RUNNING -> POSTPROCESSING -> FINALIZED`.
6. Show FEA deformation and critical region linked to that job and Snapshot.
7. Open Decision Lineage and versions.
8. Move to a historical timeline without changing live state.
9. Open operator view in Chromium over WebRTC.
10. Show FEA failure or timeout -> `MANUAL_REVIEW`.

Until those apps exist, walk the same story with the JSON examples.

## Architecture gates

- No database access from Omniverse clients
- No synchronous FEA inside an HTTP request
- No Scenario overwrite of live state
- No SAFE fallback from failed or inconclusive required FEA
- No raw hardening scalar treated as a physical unit
- No unversioned safety threshold

## Portfolio capture later

Only after end-to-end acceptance:

1. Full factory senior view
2. Drawing 4 detail
3. System architecture
4. Digital Twin / PINN / FEA Decision flow
5. Real OpenRadioss overlay
6. Decision Lineage
7. Operator WebRTC view
8. Grafana reliability dashboard
