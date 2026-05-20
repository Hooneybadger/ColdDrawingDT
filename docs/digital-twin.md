# Digital Twin

Terms: [glossary](glossary.md).

AAS stores the current meaning of each Asset. TimescaleDB stores history. OpenUSD stores space.

This version defines the model. BaSyx is not deployed here yet.

## AAS shape

Example Asset: Drawing 4

```text
AAS: urn:bg:mieum:drw:04
  Identification
  ProcessState
  MaterialState
  EquipmentState
  EvaluationState
  SimulationState
  OperationMetadata
```

ProcessState:

- `pass_index`
- `reduction_ratio`
- `die_half_angle_rad`
- `drawing_speed` when available
- `friction_coefficient` or the configured effective value
- `source_timestamp`

MaterialState:

- `material_profile_id`
- `normalized_hardening_coefficient`
- lot or workpiece reference when applicable

EvaluationState:

- `latest_evaluation_id`
- `latest_snapshot_id`
- status
- final verdict
- `updated_at`

SimulationState:

- `active_fea_job_id`
- `last_completed_fea_job_id`
- solver version
- result status
- artifact reference

Identity map: [config/asset_registry.yaml](../config/asset_registry.yaml).

```text
BG.MIEUM.DRW.04
  AAS  urn:bg:mieum:drw:04
  USD  /World/BugokFactory/Production/Drawing/Drawing_04
```

## Snapshot

An Evaluation never reads a moving Digital Twin all the way through. At start it copies an immutable Snapshot.

Worked example: [examples/process_snapshot.example.json](examples/process_snapshot.example.json)

```json
{
  "snapshot_id": "snap-0001",
  "asset_id": "BG.MIEUM.DRW.04",
  "captured_at": "2026-09-14T16:00:00Z",
  "source_state_version": "state-0001",
  "features": {
    "reduction_ratio": 0.3,
    "die_half_angle_rad": 0.2,
    "friction_coefficient": 0.08,
    "normalized_hardening_coefficient": 0.7
  }
}
```

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
