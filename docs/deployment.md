# On-site deployment

Terms: [glossary](glossary.md).

This version has no Compose file and no containers yet. The layout below is the target.

## Zones

```mermaid
flowchart TD
  ot[OT zone: equipment and OPC UA] --> integration[Integration zone: edge adapter]
  integration --> app[Application zone]
  app --> gpu[GPU view zone: Omniverse]
```

Application zone services:

- API and Evaluation
- BaSyx
- PostgreSQL with TimescaleDB
- RabbitMQ
- Celery FEA workers
- PINN files
- FEA files
- Prometheus and Grafana

Network zones may collapse on a laptop. The interfaces stay separate in code.

