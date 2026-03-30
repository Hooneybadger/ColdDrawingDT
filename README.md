# Cold Drawing Digital Twin

On-site system for a cold drawing mill.

The loop is: read process state, freeze a Snapshot, run a fast PINN check, run OpenRadioss FEA when the PINN returns NEED_FEA, store a Decision, and show the factory in 3D.

This repository holds contracts and documentation first.
