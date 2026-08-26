# Glossary

Use these names in every document.

| Name | Meaning |
|---|---|
| Cold drawing | Pulling metal through a die to reduce its size. |
| Digital Twin | Live software model of the factory and process. |
| Asset | One machine, crane, or zone with a stable ID. |
| Asset ID | Public ID such as `BG.MIEUM.DRW.04`. |
| Site ID | Factory site code. This site is `BG.MIEUM`. |
| Drawing 4 | Primary demonstration machine. Asset ID `BG.MIEUM.DRW.04`. |
| Snapshot | Frozen copy of process values used for one Evaluation. |
| Evaluation | One safety check run. |
| Decision | Stored result of an Evaluation. |
| PINN | Fast local AI model that estimates drawing safety. |
| FEA | Slower physics simulation of the same drawing step. |
| OpenRadioss | Open FEA solver used in this project. |
| Routing policy | Rules that choose PINN-only, FEA, or Manual review. |
| Scenario | What-if run that must not change live factory state. |
| Freshness | How recent the required source data is. |
| Lineage | Record of versions and inputs behind a Decision. |
| AAS | Asset Administration Shell. Industrial model of an Asset. |
| BaSyx | Software that stores AAS data. |
| OpenUSD | 3D scene format for the factory. |
| Omniverse | 3D app used to view the factory. |

## Verdicts

| Verdict | Meaning |
|---|---|
| `SAFE` | The check accepted the condition. |
| `UNSAFE` | The check rejected the condition. |
| `NEED_FEA` | PINN asks for FEA before a final Decision. |
| `INCONCLUSIVE` | FEA ran but numerical quality or metrics are not enough. |
| `MANUAL_REVIEW` | Automatic Decision is blocked. A person must review. |

## Clocks

These are different times. Do not mix them.

| Name | Meaning |
|---|---|
| Source timestamp | OPC UA / measurement time on Twin and Snapshot. Null when unknown. |
| Source timestamp provenance | `measurement` when the source clock was copied. `unknown` on a legacy Snapshot that never stored it. |
| Ingest timestamp | Backend ingest of that Twin state. |
| Snapshot `captured_at` | Immutable freeze time of the Snapshot. Not a substitute for source time. |
| Decision timestamp | When the Decision row was written. |

## Timeouts

These are different budgets. Do not mix them.

| Name | Meaning |
|---|---|
| OpenRadioss phase timeout | `fea_job_timeout_s`. Maximum for one Starter or Engine run. |
| Celery worker outer timeout | Soft/hard limits covering Starter + Engine + conversion + grace. |
| FEA lease expiration | When a `RUNNING` job may be reclaimed if the worker is silent. |
| Lease heartbeat | Worker renews `lease_expires_at` while the solver still runs. |
| Reclaim | `make fea-reclaim` recovers an expired lease without a second Engine on the same files. |

## Quality words

These are different clocks and gates. Do not mix them.

| Name | Meaning |
|---|---|
| Source quality | Equipment / OPC UA quality frozen on the Snapshot (`GOOD`, `BAD`, `UNCERTAIN`). |
| Snapshot input quality | `MEASURED` for a live reading. `SCENARIO_ASSUMED` for a what-if that must not be read as a verified GOOD measurement. |
| FEA numerical quality | Solver output gate (`quasi-static-quality-v1`). Pass is not a safety verdict. |
| FEA safety criterion | Engineering SAFE/UNSAFE thresholds (`thresholds_v1`). Default mill YAML leaves automatic verdict off. |

## Process features

These four names and this order are fixed.

1. `reduction_ratio`
2. `die_half_angle_rad`
3. `friction_coefficient`
4. `normalized_hardening_coefficient`

Do not send them as an unnamed list except inside the PINN process.
