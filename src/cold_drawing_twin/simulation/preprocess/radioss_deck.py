from __future__ import annotations

from pathlib import Path

from cold_drawing_twin.config_files import fea_reference
from cold_drawing_twin.simulation.preprocess.geometry import AxisymmetricGeometry
from cold_drawing_twin.simulation.preprocess.material import load_reference_material
from cold_drawing_twin.simulation.preprocess.radioss_format import chunked, e20, i10, trarot


def write_radioss_decks(
    work_dir: Path,
    geometry: AxisymmetricGeometry,
    mesh: dict,
    friction: float,
    job_id: str,
) -> dict[str, str]:
    """Write a 2D axisymmetric cold-drawing Starter/Engine pair that OpenRadioss can run."""
    work_dir.mkdir(parents=True, exist_ok=True)
    run_name = job_id.replace("-", "_")
    starter = work_dir / f"{run_name}_0000.rad"
    engine = work_dir / f"{run_name}_0001.rad"
    material = load_reference_material()
    reference = fea_reference()
    drawing = reference["drawing"]
    contact = reference["contact"]
    duration = float(drawing["duration_s"])
    velocity = float(drawing["velocity_m_s"])
    ramp = float(drawing["ramp_s"])
    gap = float(contact["gap_m"])
    stfac = float(contact["stiffness_scale"])
    irm = int(contact.get("irm", 2))
    inacti = int(contact.get("inacti", 0))

    workpiece = mesh["workpiece"]
    die = mesh["die"]
    starter.write_text(
        _starter_text(
            job_id=run_name,
            geometry=geometry,
            workpiece=workpiece,
            die=die,
            material=material,
            friction=float(friction),
            duration=duration,
            velocity=velocity,
            ramp=ramp,
            gap=gap,
            stfac=stfac,
            irm=irm,
            inacti=inacti,
        ),
        encoding="utf-8",
    )
    engine.write_text(_engine_text(run_name, duration), encoding="utf-8")
    return {"starter": str(starter), "engine": str(engine)}


def _starter_text(
    *,
    job_id: str,
    geometry: AxisymmetricGeometry,
    workpiece: dict,
    die: dict,
    material: dict,
    friction: float,
    duration: float,
    velocity: float,
    ramp: float,
    gap: float,
    stfac: float,
    irm: int,
    inacti: int,
) -> str:
    nodes = workpiece["nodes"] + die["nodes"]
    node_block = "\n".join(i10(nid) + e20(x, y, z) for nid, x, y, z in nodes)
    work_quads = "\n".join(i10(eid, n1, n2, n3, n4) for eid, n1, n2, n3, n4 in workpiece["quads"])
    die_quads = "\n".join(i10(eid, n1, n2, n3, n4) for eid, n1, n2, n3, n4 in die["quads"])
    curve = "\n".join(e20(strain, stress) for strain, stress in material["curve"])
    axis_grp = _grnod(1, "axis_y0", workpiece["axis_nodes"])
    pull_grp = _grnod(2, "draw_end", workpiece["pull_nodes"])
    die_grp = _grnod(3, "die_fixed", die["all_nodes"])
    secondary_grp = _grnod(4, "workpiece_outer", workpiece["outer_nodes"])
    die_surf = _surf_seg(1, "die_bore", die["inner_nodes"])
    th_nodes = _th_nodes(workpiece["pull_nodes"][: min(8, len(workpiece["pull_nodes"]))])
    source = material["source"]
    return f"""#RADIOSS STARTER
# Cold-drawing reference case, 2D axisymmetric (N2D3D=1).
# Frame: Y radial, Z axis of revolution, X=0, element normal +X.
# job {job_id}
# material_profile {material['id']} version {material['version']}
# production_calibrated {material['production_calibrated']}
# mill_calibrated {material['calibrated']}
# mapping_version {material['mapping_version']}
# source_type {source.get('type')}
# friction_coefficient mapped to /INTER/TYPE5 Fric={friction}
# r0={geometry.r0} rf={geometry.rf} cone={geometry.cone_length_m}
#---1----|----2----|----3----|----4----|----5----|----6----|----7----|----8----|----9----|---10----|
/BEGIN
{job_id}
      2022         0
                  kg                   m                   s
                  kg                   m                   s
/ANALY
{i10(1, None, 0)}
/NODE
{node_block}
/PART/1
workpiece
{i10(1, 1)}
/PART/2
die
{i10(2, 2)}
/PROP/SOLID/1
workpiece_quad
{i10(17, 4, 0, 2, 0, 0, 0, 1)}
{e20(1.10, 0.05, 0.10)}
{e20(0.0, 0.0, 0.0, 0.0, 0.0)}
{i10(0, 0, 0)}
/PROP/SOLID/2
die_quad
{i10(17, 4, 0, 2, 0, 0, 0, 1)}
{e20(1.10, 0.05, 0.10)}
{e20(0.0, 0.0, 0.0, 0.0, 0.0)}
{i10(0, 0, 0)}
/MAT/PLAS_TAB/1
stainless_reference_v1
{e20(material['density_kg_m3'])}
{e20(material['young_modulus_pa'], material['poisson_ratio'])}
{i10(1)}{" " * 80}{i10(0)}
{i10(0)}{e20(0.0)}{i10(0)}{e20(0.0, 0.0)}
{i10(1)}
{e20(1.0)}
{e20(0.0)}
/FUNCT/1
TrueYieldStressPa_vs_TruePlasticStrain_QUASI_STATIC
{curve}
/MAT/LAW1/2
die_elastic_fixed
{e20(material['density_kg_m3'])}
{e20(material['young_modulus_pa'], material['poisson_ratio'])}
/QUAD/1
{work_quads}
/QUAD/2
{die_quads}
{axis_grp}
{pull_grp}
{die_grp}
{secondary_grp}
{die_surf}
/BCS/1
axis_symmetry
{trarot(1, 1, 0, 1, 0, 0)}{i10(0, 1)}
/BCS/2
die_fixed
{trarot(1, 1, 1)}{i10(0, 3)}
/FUNCT/2
draw_velocity
{e20(0.0, 0.0)}
{e20(ramp, velocity)}
{e20(duration, velocity)}
/IMPVEL/1
drawing
{i10(2)}{"         Z"}{i10(0, 0, 2, 0, 0)}
{e20(1.0, 1.0, 0.0, duration)}
/INTER/TYPE5/1
workpiece_die
{i10(4, 1)}{" " * 40}{i10(0, 0)}
{e20(stfac, friction, gap, 0.0, duration)}
{_type5_ibc(irm=irm, inacti=inacti)}
{i10(0, 0)}{e20(0.0)}{" " * 10}{i10(0)}{e20(1.0e30)}
{th_nodes}
/TH/PART/1
energies
IE        KE
{i10(1)}
{i10(2)}
/END
"""


def _engine_text(job_id: str, duration: float) -> str:
    anim_dt = max(duration / 10.0, 1.0e-4)
    th_dt = max(duration / 100.0, 1.0e-5)
    return f"""#RADIOSS ENGINE
/RUN/{job_id}/1
{duration}
/ANIM/DT
0 {anim_dt}
/ANIM/VECT/DISP
/ANIM/ELEM/EPSP
/ANIM/ELEM/VONM
/ANIM/NODA/DT
/TFILE
{th_dt}
/END
"""


def _grnod(group_id: int, title: str, node_ids: list[int]) -> str:
    lines = [f"/GRNOD/NODE/{group_id}", title]
    for group in chunked(node_ids, 10):
        lines.append(i10(*group))
    return "\n".join(lines)


def _type5_ibc(*, irm: int, inacti: int) -> str:
    """I_BC packed flags, I_Rm, Inacti. I_Rm=2 keeps SURF winding (Altair TYPE5)."""
    return f"{' ':7}000{' ':10}{irm:10d}{inacti:10d}"


def _surf_seg(surf_id: int, title: str, node_ids: list[int]) -> str:
    """2-node 2D segments walking +Z. Normal in YZ then points toward the axis/workpiece."""
    lines = [f"/SURF/SEG/{surf_id}", title]
    for index in range(len(node_ids) - 1):
        lines.append(i10(index + 1, node_ids[index], node_ids[index + 1]))
    return "\n".join(lines)


def _th_nodes(node_ids: list[int]) -> str:
    lines = ["/TH/NODE/1", "draw_end", "REACZ     DZ        Y"]
    for nid in node_ids:
        lines.append(f"{i10(nid, 0)}PULL")
    return "\n".join(lines)
