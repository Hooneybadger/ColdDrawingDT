# Observability and reliability

Terms: [glossary](glossary.md).

Prometheus scrapes `/metrics`. Grafana loads `deploy/grafana/dashboards/cold-drawing.json`. That dashboard queries only series this process emits.

## Implemented

These counters, histograms, and gauges come from the API and evaluation process:

| Series | When |
|---|---|
| `http_requests_total{path,method,status}` | After each HTTP response |
| `twin_updates_total{asset_id,status}` | Operational Twin write (`status` is OPC UA quality) |
| `pinn_inference_duration_seconds` | Around `PinnAdapter.predict` |
| `pinn_results_total{verdict,model_version}` | Parsed PINN result |
| `pinn_failures_total{reason}` | `unavailable` or `invalid_verdict` |
| `evaluations_blocked_total{reason}` | `missing_or_quality` or `stale` |
| `fea_jobs_total{status}` | New `QUEUED`, claimed `RUNNING`, solver terminal status |
| `fea_job_duration_seconds` | Wall time of `run_case` |
| `decisions_total{verdict}` | Decision row insert |
| `manual_review_total{reason}` | Manual-review Decision (`reason` is the verdict) |
| `twin_state_age_seconds{asset_id}` | Set on `/metrics` scrape from Twin `source_timestamp` |
| `fea_queue_depth` | Set on `/metrics` scrape: count of `QUEUED` jobs |
| `fea_running_jobs` | Set on `/metrics` scrape: count of `RUNNING` jobs |

No numeric SLOs are claimed here. Empty Grafana panels mean the process has not served that path yet.

## Planned

Not emitted in this version. Do not treat them as live:

- `twin_sync_failures_total`
- OPC UA reconnect / bad-quality dedicated counters (quality is the Twin `status` label today)
- physics-residual histogram
- Starter vs Engine failure split, mesh element count, energy-quality result count as separate series
- `decision_end_to_end_seconds`
- 3D stream sessions, GPU use, GPU memory

A transactional outbox for FEA publish is implemented as `fea_outbox`. See [deployment.md](deployment.md).

## Alerts

High priority when wired to a real Prometheus rule file (not shipped here):

- Stale critical Digital Twin
- Repeated OPC UA quality failure
- PINN file missing or checksum mismatch
- FEA queue above an operating limit the site sets
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

## Failure meaning

| Failure | Result |
|---|---|
| Source stale | Manual review |
| PINN unavailable | Manual review in `routing-v1` |
| Queue unavailable | Job stays `QUEUED` with unpublished `fea_outbox`; `make fea-requeue` publishes those rows. |
| Solver failed | Manual review |
| Postprocess failed | Manual review |
| Omniverse unavailable | View degraded; stored Decision stays authority |
