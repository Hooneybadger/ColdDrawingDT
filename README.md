# Cold Drawing Digital Twin

This project designs an on-site system for a cold drawing mill.

The system will:

1. Read live process values from machines.
2. Freeze those values as a Snapshot.
3. Run a fast PINN safety check.
4. Run FEA only when the PINN result is `NEED_FEA`, or when site rules require it.
5. Store a Decision with Lineage.
6. Show the factory in 3D.

This version is **contracts and documentation**. There is no running API, PINN adapter, FEA worker, or 3D app yet.

If a word is new, see [docs/glossary.md](docs/glossary.md).

## Current version

| Item | Value |
|---|---|
| Contract set | 1.1 |
| PINN release | v0.1.1 |
| Routing policy | routing-v1 |
| FEA reference | fea-reference-v1 |
| FEA safety criterion | fea-criterion-v1 |
| Primary demo Asset | Drawing 4 (`BG.MIEUM.DRW.04`) |
| Factory hall | 96 m x 41.13 m x 14.2 m |

Not filled in this version:

- FEA numeric safety thresholds (`required_thresholds` is empty)
- Hardening curve numbers behind `hardening-map-v1`
- Application source code

