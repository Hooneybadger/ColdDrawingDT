# Test and validation

Terms: [glossary](glossary.md).

`make test-pinn` / `pinn-integration.yml` fetch the released bundle and call `predict.py`. Missing `predict.py` or `pinn.pt` fails the job. The workflow then prints `make model-verify` JSON from the same files.

`fea-integration.yml` runs on every push and pull request to `main` (and on `workflow_dispatch`). It installs OpenRadioss, runs `make fea-smoke` (Starter and Engine), then `scripts/summarize_fea_result.py`. That script fails if `result.json` is missing, `solver_status` is not `SUCCEEDED`, or termination is not `NORMAL_TERMINATION`. `criterion_verdict=INCONCLUSIVE` is expected and does not fail the job. `quality_pass` is printed from `result.json`; it is evidence, not a safety verdict.

## Current checks

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_contracts.py
python -m pip install -e ".[dev]"
make test
```

`make test` excludes `pinn_release`. That marker calls the released `predict.py` + `pinn.pt` bundle and **fails** if the files are missing (it does not skip as success). A valid in-domain verdict may be `SAFE`, `UNSAFE`, or `NEED_FEA`. The routing test uses `FEA_EXECUTION=celery` so `NEED_FEA` queues a job and does not start OpenRadioss.

```bash
make fetch-pinn
python -m pip install -e ".[dev,pinn]"
make test-pinn
make model-verify
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
- Snapshot -> real PINN (`make test-pinn` / `pinn-integration.yml`; fails if `predict.py` or `pinn.pt` is missing)
- Queue -> worker lifecycle (Celery outbox after commit; atomic `QUEUED` claim; lease heartbeat; lease reclaim; `fea-requeue` unpublished outbox)
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

- Mesh checksum repeatability for the same Snapshot and mesh counts (`make fea-validate`)
- Mesh refinement structure (element count and checksum change). Not a published convergence study.
- Quasi-static energy quality (gate on listing ERROR saturation)
- Geometry sensitivity direction from the mapping (higher reduction -> smaller `rf`)
- Solver identity from listing when a listing exists

System:

- Repeat the same Snapshot and config; compare checksums and metrics inside a stated tolerance (tolerance not set; report copies stored metrics only)

## Performance later

Track separately:

- PINN P50 and P95
- API overhead
- FEA queue wait
- FEA runtime
- WebRTC session start (`POST /stream/sessions` and `POST /stream/webrtc/offer`)
- Concurrent operator stream GPU cost

Do not average PINN and FEA latency into one number.

## Display and integration (no Kit in CI)

- Verdict colors: `SAFE` green, `UNSAFE` red, `ANALYSIS_REQUIRED` blue, `INCONCLUSIVE` / `MANUAL_REVIEW` amber, unknown or backend OFFLINE gray
- Backend fetch failure must not become `ANALYSIS_REQUIRED`
- `GET /aas/{id}/view` maps BaSyx ProcessState / EvaluationState / SimulationState; disabled or failing BaSyx returns `OFFLINE` and null submodels
- AAS V3 submodel GET uses unpadded Base64URL IDs
- `GET /aas-inspector` returns the HTML page and points at `/aas/{id}/view`, not Twin SQL routes
- Omniverse panel model conversion from `GET /assets/{id}/live` without `omni.ui`
- USD StatusIndicator attribute mapping without Kit; in-memory `pxr.Usd.Stage` write when `pxr` is installed

Kit window pixels, live BaSyx, and an OpenRadioss RUNNING screenshot are [portfolio-demo.md](portfolio-demo.md), not default `make test`.
