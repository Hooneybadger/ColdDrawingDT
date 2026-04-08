# System architecture

Terms: [glossary](glossary.md).

This version describes the target system. Only contracts exist today.

## Style

Each layer owns one job. A machine protocol, an AI model, a solver, or a 3D client must not own another layer's rules.

## Parts

```mermaid
flowchart TD
  equipment[Equipment] --> edge[Edge adapter]
  edge --> twin[Digital Twin AAS]
  twin --> history[History store]
  twin --> eval[Evaluation]
  eval --> pinn[PINN]
  pinn --> route[Routing policy]
  route -->|SAFE or UNSAFE| decision[Decision store]
  route -->|NEED_FEA| queue[FEA job queue]
  queue --> solver[Gmsh and OpenRadioss]
  solver --> post[FEA postprocess]
  post --> decision
  decision --> twin
  decision --> view[OpenUSD view]
  decision --> metrics[Metrics]
```

## Who owns which data

| Data | Owner |
|---|---|
| Asset identity and live meaning | AAS / BaSyx |
| Time history of measurements | TimescaleDB |
| Evaluation and Decision lifecycle | PostgreSQL tables |
| PINN files and version | Local model manifest |
| FEA job lifecycle | Database row plus queue |
| FEA raw files | On-site artifact store |
| Spatial factory | OpenUSD |
| Metrics | Prometheus |

