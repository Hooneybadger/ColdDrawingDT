# Digital Twin

Terms: [glossary](glossary.md).

AAS stores the current meaning of each Asset. TimescaleDB (or SQLite in local tests) stores history. OpenUSD stores space.

The API writes process state to PostgreSQL tables and, when `BASYX_ENABLED=true`, upserts the same meaning to Eclipse BaSyx.

## AAS shape

Example Asset: Drawing 4. Core source of truth is PostgreSQL. BaSyx is an interoperability projection; a BaSyx failure does not roll back TwinStore.

```text
AAS: urn:bg:mieum:drw:04
  ProcessState
  EvaluationState
  SimulationState
```

ProcessState:

- `reductionRatio`
- `dieHalfAngleRad`
- `frictionCoefficient`
- `normalizedHardeningCoefficient`
- `passIndex`
- `sourceTimestamp`
- `quality`
- `stateVersion`

EvaluationState:

- `latestEvaluationId`
- `latestSnapshotId`
- `latestDecisionId`
- `latestVerdict`

SimulationState:

- `activeFeaJobId`
- `lastCompletedFeaJobId`

BaSyx REST IDs use AAS V3 Base64URL encoding without padding. Project-specific fields are not stuffed into the shell JSON.

Identity map: [config/asset_registry.yaml](../config/asset_registry.yaml).

```text
BG.MIEUM.DRW.04
  AAS  urn:bg:mieum:drw:04
  USD  /World/BugokFactory/Production/Drawing/Drawing_04
```

`GET /aas/{asset_id}/view` reads those three submodels from BaSyx. It does not rebuild them from Twin SQL. If BaSyx is disabled or unreachable the payload is `basyx_status=OFFLINE` with `process`, `evaluation`, and `simulation` set to null. That is not `MANUAL_REVIEW` and not `ANALYSIS_REQUIRED`.

`GET /aas-inspector` is a read-only HTML page for that endpoint. Default Asset ID is `BG.MIEUM.DRW.04`. See [portfolio-demo.md](portfolio-demo.md).

## Snapshot

An Evaluation never reads a moving Digital Twin all the way through. At start it copies an immutable Snapshot.

Worked example: [examples/process_snapshot.example.json](examples/process_snapshot.example.json)

```json
{
  "snapshot_id": "snap-0001",
  "asset_id": "BG.MIEUM.DRW.04",
  "captured_at": "2026-09-14T16:00:00Z",
  "source_timestamp": "2026-09-14T15:59:58Z",
  "ingest_timestamp": "2026-09-14T15:59:59Z",
  "source_state_version": "state-0001",
  "features": {
    "reduction_ratio": 0.3,
    "die_half_angle_rad": 0.2,
    "friction_coefficient": 0.08,
    "normalized_hardening_coefficient": 0.7
  }
}
```

Clocks:

| Field | Meaning |
|---|---|
| `source_timestamp` | OPC UA / measurement time. Null on a legacy Snapshot that predates this field. |
| `source_timestamp_provenance` | `measurement` if `source_timestamp` is a copied equipment clock. `unknown` if the historical source time was never stored. |
| `ingest_timestamp` | Backend ingest of that Twin state |
| `captured_at` | When this immutable Snapshot was frozen |
| Decision `created_at` | When the Decision row was written |

Lineage on both the fast path and the FEA path must keep the original `source_timestamp` when it is known. A Scenario copies it from the base Snapshot. Do not substitute `captured_at`. Do not present `unknown` provenance as a verified OPC UA timestamp.

Startup `ALTER TABLE` adds the time columns on old volumes. It does **not** copy `captured_at` into `source_timestamp`. That copy would look like a measurement clock. Schema migration tooling (Alembic) is still future work.

An operational Snapshot also freezes `source_quality` from the live Twin and sets `input_quality` to `MEASURED`. A Scenario child copies `source_quality` from the base Snapshot and sets `input_quality` to `SCENARIO_ASSUMED`. That marker is the what-if assumption. It does not rewrite equipment quality to GOOD and it does not write the live Twin.

## Freshness

```text
freshness = evaluation_start_time - latest_required_source_timestamp
```

Configuration will set a maximum age per source class. Missing required signal or a stale Snapshot blocks an automatic final Decision.

## BaSyx

First deploy:

- AAS Environment or AAS Repository
- Submodel Repository
- Registry when many services need discovery

Do not add MQTT only because BaSyx can speak MQTT. The edge adapter already covers source data unless a later fan-out need appears.

## History boundary

The Digital Twin holds current values and current references. Every accepted state change is also written to TimescaleDB with source time, ingest time, quality, and Asset ID.
