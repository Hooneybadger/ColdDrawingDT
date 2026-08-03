from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cold_drawing_twin.simulation.preprocess.geometry import AxisymmetricGeometry, die_profile_points


class MeshError(RuntimeError):
    pass


def generate_mesh(
    work_dir: Path,
    geometry: AxisymmetricGeometry,
    deformation_size: float,
    far_size: float,
    *,
    radial_elements: int | None = None,
    axial_elements: int | None = None,
    die_elements: int | None = None,
) -> dict:
    """Structured QUAD mesh in the YZ plane for Radioss N2D3D=1."""
    work_dir.mkdir(parents=True, exist_ok=True)
    nr = radial_elements or max(2, int(round(geometry.r0 / max(deformation_size, 1e-6))))
    nz = axial_elements or max(8, int(round(geometry.bar_length_m / max(far_size, 1e-6))))
    nd = die_elements or max(8, int(round((geometry.inlet_length_m + geometry.cone_length_m + geometry.outlet_length_m) / max(deformation_size, 1e-6))))
    workpiece = _workpiece_quads(geometry, nr, nz)
    die = _die_quads(geometry, nd)
    payload = {
        "frame": {"y": "radial", "z": "axis_of_revolution", "x": "0"},
        "workpiece": workpiece,
        "die": die,
        "node_count": workpiece["node_count"] + die["node_count"],
        "element_count": workpiece["element_count"] + die["element_count"],
        "radial_elements": nr,
        "axial_elements": nz,
        "die_elements": nd,
    }
    digest_src = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload["checksum"] = hashlib.sha256(digest_src).hexdigest()
    (work_dir / "mesh.json").write_text(json.dumps(_summary(payload), indent=2) + "\n", encoding="utf-8")
    _write_geo(work_dir / "drawing.geo", geometry, nr, nz)
    return payload


def _summary(mesh: dict) -> dict:
    return {
        "node_count": mesh["node_count"],
        "element_count": mesh["element_count"],
        "radial_elements": mesh["radial_elements"],
        "axial_elements": mesh["axial_elements"],
        "die_elements": mesh["die_elements"],
        "checksum": mesh["checksum"],
        "frame": mesh["frame"],
    }


def _workpiece_quads(geometry: AxisymmetricGeometry, nr: int, nz: int) -> dict:
    nodes: list[tuple[int, float, float, float]] = []
    nid = 1
    grid: list[list[int]] = []
    for j in range(nz + 1):
        row: list[int] = []
        z = geometry.bar_length_m * j / nz
        for i in range(nr + 1):
            y = geometry.r0 * i / nr
            nodes.append((nid, 0.0, y, z))
            row.append(nid)
            nid += 1
        grid.append(row)
    quads: list[tuple[int, int, int, int, int]] = []
    eid = 1
    for j in range(nz):
        for i in range(nr):
            n00 = grid[j][i]
            n10 = grid[j][i + 1]
            n11 = grid[j + 1][i + 1]
            n01 = grid[j + 1][i]
            quads.append((eid, n00, n10, n11, n01))
            eid += 1
    outer = [grid[j][nr] for j in range(nz + 1)]
    pull = list(grid[-1])
    axis = [grid[j][0] for j in range(nz + 1)]
    return {
        "nodes": nodes,
        "quads": quads,
        "outer_nodes": outer,
        "pull_nodes": pull,
        "axis_nodes": axis,
        "node_count": len(nodes),
        "element_count": len(quads),
        "next_node_id": nid,
        "next_elem_id": eid,
    }


def _die_quads(geometry: AxisymmetricGeometry, n_seg: int) -> dict:
    inner = die_profile_points(geometry, n_seg)
    nodes: list[tuple[int, float, float, float]] = []
    # Die node IDs start after a large offset so workpiece IDs stay small and stable.
    nid = 100000
    inner_ids: list[int] = []
    outer_ids: list[int] = []
    for y, z in inner:
        nodes.append((nid, 0.0, y, z))
        inner_ids.append(nid)
        nid += 1
    for y, z in inner:
        nodes.append((nid, 0.0, y + geometry.die_thickness_m, z))
        outer_ids.append(nid)
        nid += 1
    quads: list[tuple[int, int, int, int, int]] = []
    eid = 100000
    for i in range(len(inner) - 1):
        # Normal +X: inner_i, outer_i, outer_i+1, inner_i+1 would point -X.
        # inner_i, inner_i+1, outer_i+1, outer_i is CCW when viewed from +X
        # if Y increases outward and Z increases along axis.
        quads.append((eid, inner_ids[i], outer_ids[i], outer_ids[i + 1], inner_ids[i + 1]))
        eid += 1
    return {
        "nodes": nodes,
        "quads": quads,
        "inner_nodes": inner_ids,
        "all_nodes": inner_ids + outer_ids,
        "node_count": len(nodes),
        "element_count": len(quads),
    }


def _write_geo(path: Path, geometry: AxisymmetricGeometry, nr: int, nz: int) -> None:
    path.write_text(
        "\n".join(
            [
                f"// Structured YZ drawing mesh. Gmsh inspection only; Radioss uses generate_mesh QUADs.",
                f"lc = {geometry.r0 / max(nr, 1)};",
                f"Point(1) = {{0, 0, 0, lc}};",
                f"Point(2) = {{{geometry.r0}, 0, 0, lc}};",
                f"Point(3) = {{{geometry.r0}, {geometry.bar_length_m}, 0, lc}};",
                f"Point(4) = {{0, {geometry.bar_length_m}, 0, lc}};",
                "Line(1) = {1, 2};",
                "Line(2) = {2, 3};",
                "Line(3) = {3, 4};",
                "Line(4) = {4, 1};",
                "Curve Loop(1) = {1, 2, 3, 4};",
                "Plane Surface(1) = {1};",
                f"Transfinite Curve {{1, 3}} = {nr + 1};",
                f"Transfinite Curve {{2, 4}} = {nz + 1};",
                "Transfinite Surface {1};",
                "Recombine Surface {1};",
                "",
            ]
        ),
        encoding="utf-8",
    )
