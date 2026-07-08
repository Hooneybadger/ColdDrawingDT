from __future__ import annotations

from pathlib import Path

from cold_drawing_twin.config_files import hardening_map
from cold_drawing_twin.simulation.preprocess.geometry import AxisymmetricGeometry


def write_radioss_decks(
    work_dir: Path,
    geometry: AxisymmetricGeometry,
    mesh: dict,
    friction: float,
    job_id: str,
) -> dict[str, str]:
    work_dir.mkdir(parents=True, exist_ok=True)
    starter = work_dir / f"{job_id}_0000.rad"
    engine = work_dir / f"{job_id}_0001.rad"
    mapping = hardening_map()
    material_note = "uncalibrated; plastic_curve is null; not a safety input"
    if mapping.get("calibrated"):
        material_note = "calibrated mill card"
    nodes = mesh["nodes"]
    elements = mesh["elements"]
    node_lines = "\n".join(
        f"{nid:10d}{x:20.12E}{y:20.12E}{0.0:20.12E}" for nid, x, y in nodes
    )
    tria_lines = "\n".join(
        f"{eid:10d}{n1:10d}{n2:10d}{n3:10d}" for eid, n1, n2, n3 in elements
    )
    starter.write_text(
        f"""#RADIOSS STARTER
# job {job_id}
# material: {material_note}
# mapping_version: {mapping.get('version')}
# friction: {friction}
# r0={geometry.r0} rf={geometry.rf} cone={geometry.cone_length_m}
/BEGIN
{job_id}
    2026     0
/UNIT/MASS
kg
/UNIT/LENGTH
m
/UNIT/TIME
s
/NODE
{node_lines}
/SH3N/1
{tria_lines}
/END
""",
        encoding="utf-8",
    )
    engine.write_text(
        f"""#RADIOSS ENGINE
/RUN/{job_id}/1
/TSTOP
0.001
/ANIM/DT
0 0.001
/END
""",
        encoding="utf-8",
    )
    return {"starter": str(starter), "engine": str(engine)}
