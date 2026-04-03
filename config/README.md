# Configuration

These files are versioned engineering inputs. They belong in Decision and FEA Lineage.

Do not copy the same numbers into application constants.

| File | Role | This version |
|---|---|---|
| `pinn_contract.yaml` | Released PINN names and ranges | v0.1.1 |
| `routing_policy.yaml` | PINN vs FEA vs Manual review | routing-v1 |
| `fea_reference_case.yaml` | Geometry, mesh, contact, material IDs | fea-reference-v1 |
| `fea_safety_criterion.yaml` | Engineering acceptance policy | fea-criterion-v1, empty thresholds |
| `factory_layout.yaml` | Hall size and Asset coordinates | 23 placed Assets plus 3 cranes |
| `asset_registry.yaml` | Asset ID, AAS ID, OpenUSD prim | 26 IDs |

Secrets and URLs stay in `.env` / `.env.example`, not in these files.
