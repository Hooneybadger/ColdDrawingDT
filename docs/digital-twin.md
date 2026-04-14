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

