# PINN files

This folder is not stored in git.

Release: Cold Drawing PINN v0.1.1
Source: https://huggingface.co/MongsangGa/cold-drawing-pinn-poc

Fetch:

```bash
make fetch-pinn
```

Expected files:

- `predict.py`
- `pinn.pt`
- `inference_config.json`

The product calls those files. It does not reimplement the network.
