# Repository layout

## This version

```text
ColdDrawingDT/
  README.md
  .env.example
  requirements.txt
  requirements-ci.txt
  MANIFEST.json
  config/
  schemas/
  docs/
    examples/
    images/
    adr/
    contribution-units.md
  scripts/
    validate_contracts.py
    render_factory_layout.py
  .github/
```

`MANIFEST.json` is a checksum list of public files in this contract set.

## Planned code layout

```text
src/cold_drawing_twin/
  domain/
  edge/opcua/
  twin/basyx/
  history/
  inference/pinn/
  reliability/
  simulation/preprocess/
  simulation/solver/
  simulation/postprocess/
  orchestration/
  api/
  observability/
omniverse/
  apps/senior/
  apps/operator/
  extensions/
  scripts/generate_factory_stage.py
usd/factory/
usd/assets/
workers/
tests/unit/
tests/integration/
tests/e2e/
tests/fea/
compose.yaml
```

