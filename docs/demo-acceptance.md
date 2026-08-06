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

Automatic FEA SAFE/UNSAFE cannot pass: the criterion evaluator is not implemented, and `required_thresholds` is empty.

Operator/senior Kit apps poll the HTTP API. They do not write Decisions.
