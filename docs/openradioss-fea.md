# OpenRadioss FEA

Terms: [glossary](glossary.md).

This version writes and, when binaries are installed, runs a 2D axisymmetric cold-drawing reference case. The criterion evaluator is not implemented. Filling `required_thresholds` cannot produce automatic SAFE/UNSAFE.

## Formulation

OpenRadioss `/ANALY` `N2D3D=1` is axisymmetric: elements live in the YZ plane, the element normal is +X, Y is radial, Z is the axis of revolution, and the mesh must not cross Y=0. Official `/QUAD` cards are the 2D solid elements for that analysis. 3D shells (`/SH3N`) are the wrong family.

A thin 3D sector would also be valid, but it costs more and is not required for round-bar drawing. This reference case uses 2D axisymmetry.

| Item | Card | Why |
|---|---|---|
| Analysis | `/ANALY` N2D3D=1 | Documented axisymmetric mode |
| Elements | `/QUAD` + `/PROP/SOLID` Isolid=2, Ismstr=4 | 2D Q4 (Belytschko). Isolid=17 fully integrated quads grew internal energy with **no contact** on OpenRadioss `latest-20260728`, so they are not used. |
| Workpiece | `/MAT/PLAS_TAB` (LAW36) | Tabulated elastoplastic curve from the Altair LAW36 steel example, converted to kg-m-s |
| Die | `/MAT/LAW1` + `/BCS` | Stationary die; nodes fixed |
| Contact | `/INTER/TYPE5` + `/SURF/SEG` | 2D node-to-segment contact; `Fric` is the PINN `friction_coefficient`. Starter `INORI2` orients the bore outward from the die solid. `Inacti=0` does not move nodes. `Gap=0` follows the TYPE5 note that a large gap causes energy jumps. |
| Drawing | `/IMPVEL` on the bar end | Prescribed axial velocity |
| Axis | `/BCS` TX, TY, RX on Y=0 nodes | Axisymmetric constraint (Hopkinson-bar practice) |

## Material

Mill plastic data is still absent (`config/hardening_map.yaml` `plastic_curve: null`, `calibrated: false`).

FEA uses `config/materials/stainless_reference_v1.yaml`:

- Source: Altair `/MAT/LAW36` example `MAT_TABULATED_STEEL_EXAMPLE`, quasi-static FUNCT/1
- Production calibrated: false
- PINN `normalized_hardening_coefficient` is not this curve and is not converted to MPa

## Geometry

The workpiece starts in the cylindrical inlet, short of the cone corner, as an undeformed bar of radius `r0`. `/INTER/TYPE5` uses `Gap=0` (Altair: a large TYPE5 gap causes energy jumps). `Inacti=0` does not move nodes. Drawing motion pulls the bar in +Z through the die.

Demo numbers: `reduction_ratio = 0.3`, `initial_radius_m = 0.01` so `r_f = 0.01 * sqrt(0.7) ≈ 0.00837 m`.

## Timeouts

`fea_job_timeout_s` is one OpenRadioss phase. Starter and Engine each get that budget. Celery soft/hard limits cover both phases plus conversion. The FEA lease and heartbeat track worker liveness, not the per-phase solver budget. See [deployment.md](deployment.md).

## Quality and safety

Solver completion is not a safety verdict. `quasi-static-quality-v1` requires normal termination, required files, finite required metrics, and minimum mesh counts. OpenRadioss clips listing `ERROR` at 99.9%; a saturated clip fails the gate because the solver did not report a usable energy balance. No mill kinetic/internal energy ratio cut-off is invented.

`fea-criterion-v1` sets `automatic_verdict_enabled: false` and `evaluator: unimplemented`. `required_thresholds` is empty. A quality-passing solve is therefore `INCONCLUSIVE` and goes to `MANUAL_REVIEW`. FEA metrics are still stored. Listing numbers in YAML cannot turn this evaluator on.

## How to run

```bash
bash scripts/install_openradioss.sh
export OPENRADIOSS_STARTER_BIN=$HOME/OpenRadioss/exec/starter_linux64_gf
export OPENRADIOSS_ENGINE_BIN=$HOME/OpenRadioss/exec/engine_linux64_gf
make fea-smoke
```

The manual GitHub Actions workflow `.github/workflows/fea-integration.yml` does that install and smoke on `ubuntu-latest`, uploads `simulation/workspaces/fea-smoke`, and prints `result.json` fields. A green run means Starter and Engine actually ran (`solver_status=SUCCEEDED`, `NORMAL_TERMINATION`). `INCONCLUSIVE` is expected. The job does not fail because the unimplemented criterion is inconclusive.

Artifacts land in `simulation/workspaces/<job-id>/`: starter deck, engine deck, solver logs, parsed `result.json`.

Parser unit tests under `tests/fea/fixtures/` are labeled fixtures. They are not actual solves.

`make fea-validate` writes a mesh-repeatability checksum, a mesh-refinement **structure** (more elements, different checksum), and a geometry sensitivity **direction** (higher reduction -> smaller mapped `rf`) without requiring the Engine. If `simulation/workspaces/fea-smoke/result.json` exists, the report copies radius, reaction, and energy from that file. It does not invent a solve.

GitHub Actions workflow `fea-integration.yml` is manual (`workflow_dispatch`) and runs the real solver when invoked.

## Actual smoke execution

On a local OpenRadioss `latest-20260728` Linux GNU build, `make fea-smoke` reached **NORMAL TERMINATION**.

Parsed from listing + `th_to_csv` + `anim_to_vtk` (not placeholders), **fea-reference-v2** (`Isolid=2`):

- listing energy error does not saturate; last cycle about 27%, peak about 48%
- pull-end outer radius ≈ 8.57 mm versus geometric `r_f` ≈ 8.37 mm
- drawing reaction on the pull nodes on the order of 10⁴ N
- peak von Mises ≈ 0.74 GPa and peak equivalent plastic strain ≈ 0.35 on workpiece quads
- kinetic energy ≪ internal energy (quasi-static intent)

`Isolid=17` was rejected: a no-contact run still saturated listing `ERROR` at 99.9% while internal energy grew without matching external work. That is a 2D Q4 formulation failure on this solver build, not a mill fracture threshold.

TYPE5 still reports `CONTACT ENERGY = 0` in the T01 file. Quality uses listing `ERROR` saturation, required files, and finite required metrics. The unimplemented criterion still forces `INCONCLUSIVE` / `MANUAL_REVIEW` after a quality-passing solve.

`Inacti=3` was rejected: it moved the nose node across the inlet clearance and destroyed the bar at t=0.
