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
| `INCONCLUSIVE` | FEA ran but quality or metrics are not enough. |
| `MANUAL_REVIEW` | Automatic Decision is blocked. A person must review. |

## Process features

These four names and this order are fixed.

1. `reduction_ratio`
2. `die_half_angle_rad`
3. `friction_coefficient`
4. `normalized_hardening_coefficient`

Do not send them as an unnamed list except inside the PINN process.
