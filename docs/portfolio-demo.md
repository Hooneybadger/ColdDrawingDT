# Portfolio demonstration

Terms: [glossary](glossary.md).

This is the visual check that one Drawing 4 Evaluation is the same object on the backend, on BaSyx, and in Omniverse. It does not add physics, routing, or safety rules.

Drawing 4 Asset ID: `BG.MIEUM.DRW.04`.
AAS ID: `urn:bg:mieum:drw:04`.
OpenUSD prim: `/World/BugokFactory/Production/Drawing/Drawing_04`.
Status indicator: `/World/BugokFactory/Production/Drawing/Drawing_04/StatusIndicator`.

Omniverse and the AAS Inspector are read-only. They do not invent a verdict when transport fails.

## What this sequence proves

```text
Backend Decision
      |
      v
AAS / BaSyx
      |
      v
OpenUSD / Omniverse
```

Compare these four fields on every surface:

```text
latestDecisionId
latestVerdict
latestEvaluationId
latestSnapshotId
```

Use the IDs the backend stored. Do not type presentation UUIDs.

## Start order

### 1. Start backend dependencies

Compose (BaSyx on, FEA through Celery):

```bash
cp .env.example .env
docker compose up -d postgres-timescale rabbitmq basyx
```

Local API without Compose still works. Default `.env.example` sets `BASYX_ENABLED=false`. In that mode the AAS Inspector shows `basyx_status=OFFLINE` and null submodels. That is a transport state, not a Decision.

### 2. Start the API

With Compose:

```bash
docker compose up -d api fea-worker
```

Or on the host (after `python -m pip install -e ".[dev]"`):

```bash
export PYTHONPATH=src:.
make fetch-pinn
make api
```

`make api` listens on `http://127.0.0.1:8000`. Confirm `/health` returns `{"status":"ok"}`.

### 3. Start the Omniverse Kit extension

On the RTX host that has Kit:

```text
omniverse/apps/operator/cold_drawing_operator.kit
```

or

```text
omniverse/apps/senior/cold_drawing_senior.kit
```

Put `omniverse/extensions` on the Kit extension search path. Put this repository `src` on `PYTHONPATH` so Kit can import `cold_drawing_twin`. The extension polls `GET /assets/BG.MIEUM.DRW.04/live` and draws an `omni.ui` panel. It does not compute SAFE or UNSAFE.

Kit 3D livestream (`omni.kit.livestream.webrtc`) still needs that host binary. The browser page `/operator` is Twin JSON, not a rendered factory frame.

### 4. Open the factory USD stage

```bash
make factory-stage
```

Open `usd/factory/bugok_factory.usda` in the Kit app. Drawing 4 is the referenced asset `usd/assets/drawing/Drawing_04.usda`. The live bind writes `displayColor` on `StatusIndicator/proxy` and `StatusIndicator/render`, and writes `coldDrawing:verdict`, `coldDrawing:quality`, `coldDrawing:feaRunning`, `coldDrawing:lastUpdate`, `coldDrawing:indicator`, and `coldDrawing:backendStatus` on the asset prim and the indicator prim.

### 5. Open the AAS Inspector

```text
http://127.0.0.1:8000/aas-inspector
```

The page is labeled `Read-only AAS / BaSyx view`. It calls `GET /aas/{asset_id}/view` only. It does not read Twin SQL. Default Asset ID is `BG.MIEUM.DRW.04`.

Also useful:

```text
http://127.0.0.1:8000/operator
```

### 6. Load Drawing 4 state

Fast-path process vector (in-domain demo):

```bash
curl -sS -X PUT http://127.0.0.1:8000/assets/BG.MIEUM.DRW.04/state \
  -H "Content-Type: application/json" \
  -d '{"reduction_ratio":0.3,"die_half_angle_rad":0.2,"friction_coefficient":0.08,"normalized_hardening_coefficient":0.7,"state_version":"state-0001","quality":"GOOD"}'
```

Or seed through the OPC UA helper (`make seed-opcua`) when that simulator is the source you want to show.

### 7. Run the fast-path Evaluation

```bash
curl -sS -X POST http://127.0.0.1:8000/assets/BG.MIEUM.DRW.04/evaluations \
  -H "Content-Type: application/json" \
  -d '{"mode":"OPERATIONAL","expected_state_version":"state-0001"}'
```

Released PINN v0.1.1 on that vector is expected to return `SAFE` or `UNSAFE` with no FEA. CLI equivalent against the process database (not the HTTP surfaces) is `make demo-fast`.

### 8. Verify the same Decision ID

Read all three (replace IDs with the values you just received):

```bash
curl -sS http://127.0.0.1:8000/assets/BG.MIEUM.DRW.04/state
curl -sS http://127.0.0.1:8000/assets/BG.MIEUM.DRW.04/live
curl -sS http://127.0.0.1:8000/aas/BG.MIEUM.DRW.04/view
```

| Surface | Where the IDs appear |
|---|---|
| Backend state | `latest_decision_id`, `latest_verdict`, `latest_evaluation_id`, `latest_snapshot_id` |
| Backend live | `decision.decision_id`, `decision.latest_verdict`, `decision.evaluation_id`, `decision.snapshot_id` |
| AAS Inspector | EvaluationState `latestDecisionId`, `latestVerdict`, `latestEvaluationId`, `latestSnapshotId` |
| Omniverse panel | DECISION: Decision ID, Latest Verdict, Evaluation ID, Snapshot ID |

The four ID fields must match. If BaSyx is disabled, the Inspector shows `OFFLINE` and null EvaluationState. Do not copy SQL into that page and call it AAS data.

### 9. Run the selective FEA path

Out-of-domain reduction (real `NEED_FEA` from `ReleasedPinnAdapter`):

```bash
curl -sS -X PUT http://127.0.0.1:8000/assets/BG.MIEUM.DRW.04/state \
  -H "Content-Type: application/json" \
  -d '{"reduction_ratio":0.55,"die_half_angle_rad":0.2,"friction_coefficient":0.08,"normalized_hardening_coefficient":0.7,"state_version":"state-fea","quality":"GOOD"}'

curl -sS -X POST http://127.0.0.1:8000/assets/BG.MIEUM.DRW.04/evaluations \
  -H "Content-Type: application/json" \
  -d '{"mode":"OPERATIONAL","expected_state_version":"state-fea"}'
```

CLI equivalent: `make demo-fea`. Compose `FEA_EXECUTION=celery` queues OpenRadioss. A local default `FEA_EXECUTION=inline` runs the solver in-process when binaries are set.

### 10. Capture FEA RUNNING

Poll until the live payload shows a running job:

```bash
curl -sS http://127.0.0.1:8000/assets/BG.MIEUM.DRW.04/live
curl -sS http://127.0.0.1:8000/aas/BG.MIEUM.DRW.04/view
```

Record one frame with:

```text
FEA Status = RUNNING
active FEA job ID (backend live `decision.fea_job_id` / AAS `activeFeaJobId`)
Omniverse FEA section
AAS SimulationState
```

Do not treat FEA completion as SAFE or UNSAFE unless the backend Decision already stores that verdict. This mill YAML leaves automatic FEA SAFE/UNSAFE off.

### 11. Capture the fail-safe final state

When the solver finishes with a quality pass and no mill-enabled automatic criterion, the stored verdict is `INCONCLUSIVE` (often with status `MANUAL_REVIEW`). Compare that same verdict and Decision ID on backend live, AAS EvaluationState, and the Omniverse DECISION section.

Do not change thresholds to force this frame.

## Offline checks

### Backend unreachable

Stop the API or block `http://127.0.0.1:8000`. Expected:

```text
Omniverse CONNECTION STATUS: Backend: OFFLINE
Browser /operator: Backend OFFLINE. State unavailable.
StatusIndicator: gray
Latest Verdict: not ANALYSIS_REQUIRED, not SAFE, not UNSAFE
```

Restart the API. The panel returns to ONLINE and shows stored engineering state again.

### BaSyx unreachable

Stop the `basyx` service or set `BASYX_ENABLED=false`. Expected:

```text
GET /aas/{id}/view -> basyx_status=OFFLINE, process/evaluation/simulation null
AAS Inspector: BaSyx OFFLINE
GET /assets/{id}/state and /live still return Twin/Decision rows
```

Twin rows are not rolled back. Missing BaSyx is not `MANUAL_REVIEW`.

## Display colors

| Backend verdict | Indicator |
|---|---|
| `SAFE` | green |
| `UNSAFE` | red |
| `ANALYSIS_REQUIRED` | blue |
| `INCONCLUSIVE` | amber |
| `MANUAL_REVIEW` | amber |
| unknown / missing / backend OFFLINE | gray |

`ANALYSIS_REQUIRED` is shown only when the backend actually stored that string. Fetch failure is gray, not blue.

## Screenshots and clips

Capture these files during a live run. They are not stored in this repository.

| ID | Frame |
|---|---|
| A | Omniverse factory with Drawing 4 StatusIndicator green and a SAFE Decision |
| B | Omniverse panel PROCESS / DECISION / FEA / CONNECTION, including Decision, Evaluation, and Snapshot IDs |
| C | AAS Inspector EvaluationState with the same IDs and `latestVerdict` |
| D | FEA RUNNING on the Omniverse panel and AAS SimulationState `activeFeaJobId` |
| E | Final `INCONCLUSIVE` or `MANUAL_REVIEW` on backend, AAS, and Omniverse |
| F | Optional: GitHub Actions green on `fea-integration.yml` / default tests after this revision is on the remote |

## Automated vs runtime-only

Covered by `make test` without Kit:

- Verdict color mapping and offline != engineering verdict
- `GET /assets/{id}/live` lineage IDs
- `GET /aas-inspector` HTML and `GET /aas/{id}/view` BaSyx OFFLINE when BaSyx is disabled
- Mocked BaSyx submodel mapping and unpadded Base64URL IDs
- Panel view-model conversion
- USD attribute mapping; in-memory `pxr` stage write when `pxr` is installed

Not launched in default CI:

- Omniverse Kit window and `omni.ui` widgets
- RTX livestream of the factory
- Live Eclipse BaSyx process
- OpenRadioss RUNNING frame on a GPU host

## Claims

Safe to say after this sequence is actually captured:

- Real-time Digital Twin state projection
- Backend-authoritative Decision pipeline
- AAS V3 / BaSyx projection
- OpenUSD / Omniverse visualization of backend state
- Selective OpenRadioss execution
- Fail-safe manual review / inconclusive behavior as configured
- Decision lineage visible across integration layers
- WebRTC / browser operator display of Twin JSON

Do not say unless proven elsewhere:

- Production deployment
- Mill-calibrated material model
- Physically validated fracture prediction
- Certified safety system
- Production-grade exactly-once messaging
- Plant-wide scalability
- Validated automatic FEA SAFE/UNSAFE verdict (the evaluator exists; mill YAML leaves it off)
