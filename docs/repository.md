# Repository layout

```text
ColdDrawingDT/
  README.md
  compose.yaml
  Makefile
  pyproject.toml
  .env.example
  config/
  schemas/
  src/cold_drawing_twin/
    domain/
    edge/opcua/
    twin/
    history/
    inference/pinn/
    simulation/preprocess/
    simulation/solver/
    simulation/postprocess/
    orchestration/
    api/
    observability/
  workers/
  omniverse/
    apps/senior/
    apps/operator/
    extensions/
    scripts/generate_factory_stage.py
  usd/factory/
  usd/assets/
  tests/unit/
  tests/integration/
  tests/e2e/
  tests/fea/
  docs/
  scripts/
  docker/
  deploy/
  .github/
```

`MANIFEST.json` lists checksums of the public contract set. Application files live beside it.

## Dependency direction

```text
api and Omniverse adapters
  -> orchestration
  -> domain interfaces
       -> Digital Twin
       -> PINN inference
       -> FEA simulation
```

Infrastructure code depends inward on interfaces. Domain and orchestration never import Omniverse UI code.
