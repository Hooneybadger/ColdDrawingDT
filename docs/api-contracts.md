# Data and API contracts

Terms: [glossary](glossary.md).

The HTTP API is implemented in `src/cold_drawing_twin/api`. The JSON below is the contract the API follows.

## Process features

One name and one order everywhere: API, Snapshot, PINN adapter, FEA mapping.

| Index | Field | PINN range |
|---:|---|---|
| 0 | `reduction_ratio` | 0.10 to 0.50 |
| 1 | `die_half_angle_rad` | 0.07 to 0.35 |
| 2 | `friction_coefficient` | 0.03 to 0.15 |
| 3 | `normalized_hardening_coefficient` | 0.20 to 1.20 |

Do not send an unnamed four-value list outside the PINN process.

Source: [config/pinn_contract.yaml](../config/pinn_contract.yaml) and [schemas/process_snapshot.schema.json](../schemas/process_snapshot.schema.json).

## Snapshot times

[examples/process_snapshot.example.json](examples/process_snapshot.example.json) keeps these clocks:

| Field | Clock |
|---|---|
| `source_timestamp` | OPC UA / measurement time, or null when unknown |
| `source_timestamp_provenance` | `measurement` or `unknown` |
| `ingest_timestamp` | Backend ingest of Twin state |
| `captured_at` | Snapshot freeze time |
| Decision `created_at` | Decision write time |

Fast-path and FEA Lineage both store the Snapshot `source_timestamp`. They must not replace it with `captured_at`. A null `source_timestamp` with provenance `unknown` is a legacy row, not a verified equipment clock.

`source_quality` is the frozen equipment quality. `input_quality` is `MEASURED` on an operational Snapshot and `SCENARIO_ASSUMED` on a Scenario child. Scenario evaluation may run under that assumption without rewriting the base equipment quality to GOOD.

## Evaluation request

The client names the Asset. The server copies live values from the Digital Twin. The client does not submit safety-critical feature values for a live Evaluation.

[examples/evaluation_request.example.json](examples/evaluation_request.example.json):

```json
{
  "asset_id": "BG.MIEUM.DRW.04",
  "mode": "OPERATIONAL",
  "expected_state_version": "state-0001"
}
```

## Scenario request

A Scenario is labeled `SCENARIO` everywhere. It cannot overwrite live factory state.

[examples/scenario_request.example.json](examples/scenario_request.example.json):

```json
{
  "base_snapshot_id": "snap-0001",
  "overrides": {
    "reduction_ratio": 0.3,
    "die_half_angle_rad": 0.2,
    "friction_coefficient": 0.08,
    "normalized_hardening_coefficient": 0.7
  }
}
```

## PINN result

[examples/prediction_result.example.json](examples/prediction_result.example.json):

```json
{
  "verdict": "NEED_FEA",
  "stress_indicator": 0.0,
  "damage_indicator": 0.0,
  "physics_residual": 0.0,
  "confidence": null,
  "model_version": "v0.1.1",
  "supported_range": true
}
```

`confidence: null` means unused, not zero.

## FEA job

[examples/fea_job.example.json](examples/fea_job.example.json):

```json
{
  "job_id": "fea-0001",
  "evaluation_id": "eval-0002",
  "snapshot_id": "snap-0002",
  "status": "QUEUED",
  "solver": "OpenRadioss",
  "solver_version": "unset",
  "material_mapping_version": "hardening-map-v1",
  "safety_criterion_version": "fea-criterion-v1"
}
```

`solver_version` is `unset` until a worker pins a real solver build.

## Decision

Schema: [schemas/decision.schema.json](../schemas/decision.schema.json).

Fast path: [examples/decision.example.json](examples/decision.example.json)

```json
{
  "decision_id": "dec-0001",
  "evaluation_id": "eval-0001",
  "snapshot_id": "snap-0001",
  "status": "FINALIZED",
  "verdict": "SAFE",
  "model_version": "v0.1.1",
  "routing_policy_version": "routing-v1",
  "fea_job_id": null
}
```

FEA path that needs a person: [examples/decision_fea.example.json](examples/decision_fea.example.json)

## HTTP API

```text
GET  /assets/{asset_id}
GET  /assets/{asset_id}/state
PUT  /assets/{asset_id}/state
GET  /assets/{asset_id}/history
POST /assets/{asset_id}/evaluations
GET  /evaluations/{evaluation_id}
POST /scenarios
GET  /scenarios/{scenario_id}
GET  /fea-jobs/{job_id}
GET  /decisions/{decision_id}
POST /stream/sessions
GET  /stream/sessions
GET  /stream/sessions/{session_id}
POST /stream/sessions/{session_id}/heartbeat
DELETE /stream/sessions/{session_id}
POST /stream/webrtc/offer
GET  /operator
GET  /health
GET  /metrics
```

A stream session is display liveness. Creating or heartbeating a session must not write a Decision. Kit and the browser client both register here so `/metrics` can scrape `stream_sessions`. An optional `gpu` object on heartbeat is the RTX-host sample; the API does not invent GPU numbers.

## Events

Event names:

- `TWIN_UPDATED`
- `EVALUATION_STATE_CHANGED`
- `FEA_JOB_STATE_CHANGED`
- `DECISION_FINALIZED`
- `ALERT_RAISED`

HTTP remains the source for commands and queries. Events only notify, and they include IDs so a client can fetch again.
