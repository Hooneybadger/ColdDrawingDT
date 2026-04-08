# Data and API contracts

Terms: [glossary](glossary.md).

The HTTP API is not implemented in this version. The JSON below is the contract the API must follow.

## Process features

One name and one order everywhere: API, Snapshot, PINN adapter, FEA mapping.

| Index | Field | PINN range |
|---:|---|---|
| 0 | `reduction_ratio` | 0.10 to 0.50 |
| 1 | `die_half_angle_rad` | 0.07 to 0.35 |
| 2 | `friction_coefficient` | 0.03 to 0.15 |
| 3 | `normalized_hardening_coefficient` | 0.20 to 1.20 |

Do not send an unnamed four-value list outside the PINN process.

Source: [config/pinn_contract.yaml](../config/pinn_contract.yaml) and [schemas/process_snapshot.schema.json](../schemas/process_snapshot.schema.json).

