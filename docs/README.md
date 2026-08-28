# Documents

Start with the [root README](../README.md) and the [glossary](glossary.md).

All public docs use the same names, ASCII punctuation, and real examples from this version.

## Current version

This repository holds contracts, not a running product.

Present:

- Versioned YAML under `config/`
- JSON Schema under `schemas/`
- Worked JSON under `docs/examples/`
- Factory picture under `docs/images/`
- Contract check script `scripts/validate_contracts.py`

Not present:

- HTTP API
- PINN adapter
- OpenRadioss worker
- Omniverse app
- Filled FEA safety thresholds
- Filled hardening curve numbers

## Map

| Doc | Read it for |
|---|---|
| [glossary.md](glossary.md) | Shared names |
| [architecture.md](architecture.md) | Parts and data owners |
| [repository.md](repository.md) | Current files and planned code |
| [api-contracts.md](api-contracts.md) | Snapshot, Decision, planned API |
| [ai-fea-orchestration.md](ai-fea-orchestration.md) | PINN, routing, FEA job flow |
| [digital-twin.md](digital-twin.md) | AAS, Snapshot, Freshness |
| [openradioss-fea.md](openradioss-fea.md) | First FEA model |
| [factory-reconstruction.md](factory-reconstruction.md) | Hall, grid, Asset layout |
| [openusd-omniverse.md](openusd-omniverse.md) | 3D factory and two user views |
| [deployment.md](deployment.md) | On-site layout for later phases |
| [observability-reliability.md](observability-reliability.md) | Metrics, alerts, Lineage |
| [test-validation.md](test-validation.md) | Tests we will require |
| [demo-acceptance.md](demo-acceptance.md) | Later demo gates |
| [adr/README.md](adr/README.md) | Why these tools were chosen |
| [contribution-units.md](contribution-units.md) | Branch and commit size |

## Examples

These files are the demonstration data used in the docs. CI checks the Snapshot and Decision examples against the schemas.

| File | Path |
|---|---|
| Snapshot | [examples/process_snapshot.example.json](examples/process_snapshot.example.json) |
| Evaluation request | [examples/evaluation_request.example.json](examples/evaluation_request.example.json) |
| Scenario request | [examples/scenario_request.example.json](examples/scenario_request.example.json) |
| PINN `NEED_FEA` result | [examples/prediction_result.example.json](examples/prediction_result.example.json) |
| FEA job | [examples/fea_job.example.json](examples/fea_job.example.json) |
| Fast Decision | [examples/decision.example.json](examples/decision.example.json) |
| FEA review Decision | [examples/decision_fea.example.json](examples/decision_fea.example.json) |

## How we write docs

- English
- First-time reader
- Names from the glossary
- Short sections
- ASCII only
- Show this version as it is
- Prefer pictures, mermaid, and JSON examples
