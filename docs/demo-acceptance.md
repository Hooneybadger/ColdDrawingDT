# Demo and acceptance

Terms: [glossary](glossary.md).

The commands in this file are **acceptance targets**. They are not implemented in this version except the contract check.

## What you can run now

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_contracts.py
python scripts/render_factory_layout.py
```

You can also open the worked JSON under [examples/](examples/) and the factory picture [images/factory-layout.svg](images/factory-layout.svg).

## Later executable checks

### A. Model

```bash
make model-verify
```

Must run the released PINN locally with the glossary feature order and print verdict, indicators, and model version.

### B. FEA

```bash
make fea-smoke
```

Must run Gmsh and OpenRadioss, parse quality and physics output, and apply the configured criterion. This cannot pass while `required_thresholds` is empty.

### C. Fast Decision

```bash
make demo-fast
```

Fresh Digital Twin -> Snapshot -> PINN SAFE or UNSAFE -> finalized Decision without FEA.

### D. FEA Decision

```bash
make demo-fea
```

Fresh Digital Twin -> PINN NEED_FEA -> queue -> real OpenRadioss -> postprocess -> Decision or Manual review.

### E. 3D

```bash
make factory-stage
make demo-stream
```

Generate the factory stage and use the operator Kit app through WebRTC.

