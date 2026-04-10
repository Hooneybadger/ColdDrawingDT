# PINN and FEA flow

Terms: [glossary](glossary.md).

This version defines the flow. It does not run PINN or OpenRadioss yet.

## PINN artifact

Release: Cold Drawing PINN v0.1.1

Files: https://huggingface.co/MongsangGa/cold-drawing-pinn-poc

Planned local call:

```bash
python predict.py --features 0.3 0.2 0.08 0.7
```

That list is the glossary feature order. The same numbers are in [examples/process_snapshot.example.json](examples/process_snapshot.example.json).

Output fields:

- `SAFE`, `UNSAFE`, or `NEED_FEA`
- stress indicator
- damage indicator
- physics residual
- model version
- optional probability or confidence (`null` means unused)

