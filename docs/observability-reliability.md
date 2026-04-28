# Observability and reliability

Terms: [glossary](glossary.md).

No metrics backend is deployed in this version. The names below are the contract for later dashboards.

## Signals

### Digital Twin

- `twin_state_age_seconds{asset_id}`
- `twin_updates_total{asset_id,status}`
- `twin_sync_failures_total`
- OPC UA reconnect count and bad-quality count

### PINN

- `pinn_inference_duration_seconds`
- `pinn_results_total{verdict,model_version}`
- `pinn_failures_total{reason}`
- physics-residual distribution

### FEA

- `fea_queue_depth`
- `fea_job_duration_seconds`
- `fea_jobs_total{status}`
- Starter and Engine failure count
- mesh element count
- energy-quality result count

### Decision

- `decisions_total{verdict}`
- `manual_review_total{reason}`
- `decision_end_to_end_seconds`

### 3D stream

- active sessions
- session start time
- stream disconnects
- server GPU use and memory

## Alerts

High priority:

- Stale critical Digital Twin
- Repeated OPC UA quality failure
- PINN file missing or checksum mismatch
- FEA queue above operating limit
- Repeated FEA failure or timeout
- Database write failure

A 3D stream outage matters for operations. It must not change stored Decisions.

## Logs

Structured logs should include:

- Evaluation ID
- Asset ID
- Snapshot ID
- Job ID when present
- Model or solver version
- State transition

Do not log secrets. Do not dump full sensitive process payloads without need.

## Lineage query

From `decision_id` `dec-0001` the system must rebuild:

```text
Decision
  -> Evaluation
  -> Snapshot
  -> source state version and times
  -> PINN version and output
  -> routing policy version
  -> FEA job and solver, material, mesh, criterion versions when used
  -> final Digital Twin update
```

