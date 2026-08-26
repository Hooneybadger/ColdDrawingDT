# Demo and acceptance

Terms: [glossary](glossary.md).

```bash
python -m pip install -e ".[dev]"
python scripts/validate_contracts.py
make test
make fetch-pinn
make test-pinn
make seed-opcua
make demo-fast
make demo-fea
make demo-system
make factory-stage
```

OpenRadioss (actual solver, optional):

```bash
bash scripts/install_openradioss.sh
export OPENRADIOSS_STARTER_BIN=$HOME/OpenRadioss/exec/starter_linux64_gf
export OPENRADIOSS_ENGINE_BIN=$HOME/OpenRadioss/exec/engine_linux64_gf
make fea-smoke
make fea-validate
```

`make fea-smoke` without binaries writes decks and exits non-zero. That is not a mocked success.

`make fea-validate` does not need the Engine. Missing `result.json` leaves solver metrics absent.

`make demo-fea` uses `ReleasedPinnAdapter` and an out-of-domain feature vector so PINN returns `NEED_FEA`. It does not use `StaticPinnAdapter`.

`make test-pinn` runs in-domain inference through `predict.py` and `pinn.pt`. Missing bundle files fail that target. Default `make test` does not require the files.

Automatic FEA SAFE/UNSAFE stays off on the mill YAML: `automatic_verdict_enabled` is false and `required_thresholds` is empty. The `thresholds_v1` evaluator runs only when a site enables it with mill-validated numbers.

`pinn-integration.yml` is a `workflow_dispatch` job for real `predict.py` evidence. `fea-integration.yml` runs OpenRadioss on every push/PR to `main`. Neither is part of default `make test`.

Operator/senior Kit apps poll the HTTP API and register stream sessions. The browser page `/operator` uses a WebRTC datachannel with HTTP poll fallback. They do not write Decisions.
