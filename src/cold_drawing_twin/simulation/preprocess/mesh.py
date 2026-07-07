from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from cold_drawing_twin.simulation.preprocess.geometry import AxisymmetricGeometry, write_geo


class MeshError(RuntimeError):
    pass


def _gmsh_bin() -> str:
    found = shutil.which("gmsh")
    if not found:
        raise MeshError("gmsh is not on PATH")
    return found


def generate_mesh(work_dir: Path, geometry: AxisymmetricGeometry, deformation_size: float, far_size: float) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    geo = work_dir / "workpiece.geo"
    msh = work_dir / "workpiece.msh"
    write_geo(geo, geometry, deformation_size, far_size)
    command = [_gmsh_bin(), str(geo), "-2", "-format", "msh2", "-o", str(msh)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0 or not msh.exists():
        raise MeshError(completed.stderr.strip() or "gmsh failed")
    nodes, elements = _parse_msh2(msh)
    digest = hashlib.sha256(msh.read_bytes()).hexdigest()
    return {
        "mesh_file": str(msh),
        "node_count": len(nodes),
        "element_count": len(elements),
        "checksum": digest,
        "nodes": nodes,
        "elements": elements,
    }


def _parse_msh2(path: Path) -> tuple[list[tuple[int, float, float]], list[tuple[int, int, int, int]]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nodes: list[tuple[int, float, float]] = []
    elements: list[tuple[int, int, int, int]] = []
    section = None
    for line in lines:
        if line.startswith("$Nodes"):
            section = "nodes"
            continue
        if line.startswith("$EndNodes") or line.startswith("$EndElements"):
            section = None
            continue
        if line.startswith("$Elements"):
            section = "elements"
            continue
        if section == "nodes":
            parts = line.split()
            if len(parts) >= 4 and parts[0].isdigit():
                nodes.append((int(parts[0]), float(parts[1]), float(parts[2])))
        elif section == "elements":
            parts = line.split()
            if len(parts) >= 8 and parts[1] == "2":
                n_tags = int(parts[2])
                ids = [int(item) for item in parts[3 + n_tags : 6 + n_tags]]
                if len(ids) == 3:
                    elements.append((int(parts[0]), ids[0], ids[1], ids[2]))
    if not nodes or not elements:
        raise MeshError("mesh parser found no triangles")
    return nodes, elements
