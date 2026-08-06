from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any


LISTING_SUFFIXES = {".out", ".txt", ".log"}
WORKPIECE_NODE_LIMIT = 100000
CYCLE_ROW = re.compile(
    r"^\s*\d+\s+"
    r"(?P<time>[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)\s+"
    r"(?P<dt>[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)\s+"
    r"\S+\s+\d+\s+"
    r"(?P<err>[+-]?(?:\d+\.\d*|\d*\.\d+|\d+))%\s+"
    r"(?P<ie>[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)\s+"
    r"(?P<ke>[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)\s+"
    r"(?P<ker>[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)\s+"
    r"(?P<work>[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"
)


def parse_solver_outputs(work_dir: Path) -> dict[str, Any]:
    """Read OpenRadioss listing, time-history CSV, and converted ANIM VTK.

    This parser never invents a successful solve. Missing files stay None.
    """
    listing_text = _concat_listings(work_dir)
    termination = parse_termination(listing_text)
    identity = parse_solver_identity(listing_text)
    energies = parse_energy_listing(listing_text)
    th = parse_time_history_csv(work_dir)
    fields = parse_field_files(work_dir)
    drawing_force = _peak(th.get("drawing_force") or energies.get("drawing_force"))
    contact_force = _peak(th.get("contact_force"))
    metrics = {
        "peak_von_mises_pa": fields.get("peak_von_mises_pa"),
        "peak_plastic_strain": fields.get("peak_plastic_strain"),
        "drawing_force_n": drawing_force,
        "contact_force_n": contact_force,
        "kinetic_energy": _last(th.get("kinetic_energy") or energies.get("kinetic_energy")),
        "internal_energy": _last(th.get("internal_energy") or energies.get("internal_energy")),
        "external_work": _last(th.get("external_work") or energies.get("external_work")),
        "contact_energy": _last(th.get("contact_energy") or energies.get("contact_energy")),
        "total_energy": _last(th.get("total_energy") or energies.get("total_energy")),
        "energy_error": _last(th.get("energy_error") or energies.get("energy_error")),
        "listing_energy_error_peak": _peak(th.get("energy_error") or energies.get("energy_error")),
        "final_outer_radius_m": fields.get("final_outer_radius_m"),
        "maximum_damage": fields.get("maximum_damage"),
    }
    return {
        "parser": "openradioss_listing_v1",
        "placeholder": False,
        "termination": termination,
        "solver_identity": identity,
        "histories": {
            "kinetic_energy": th.get("kinetic_energy") or energies.get("kinetic_energy") or [],
            "internal_energy": th.get("internal_energy") or energies.get("internal_energy") or [],
            "external_work": th.get("external_work") or energies.get("external_work") or [],
            "contact_energy": th.get("contact_energy") or energies.get("contact_energy") or [],
            "total_energy": th.get("total_energy") or energies.get("total_energy") or [],
            "energy_error": th.get("energy_error") or energies.get("energy_error") or [],
            "drawing_force": th.get("drawing_force") or energies.get("drawing_force") or [],
            "contact_force": th.get("contact_force") or [],
        },
        "metrics": metrics,
        "fields": fields,
        "files": sorted(path.name for path in work_dir.iterdir() if path.is_file()),
    }


def parse_termination(text: str) -> dict[str, Any]:
    upper = text.upper()
    if "NORMAL TERMINATION" in upper:
        status = "NORMAL_TERMINATION"
    elif "ERROR TERMINATION" in upper or "ABNORMAL TERMINATION" in upper:
        status = "ERROR_TERMINATION"
    elif text.strip():
        status = "UNKNOWN"
    else:
        status = "MISSING"
    return {"status": status, "normal": status == "NORMAL_TERMINATION"}


def parse_solver_identity(text: str) -> dict[str, Any]:
    """Read a version string from listing text. Missing text stays None."""
    if not text.strip():
        return {"solver": "OpenRadioss", "version": None, "banner": None, "source": None}
    banner_match = re.search(r".*(OpenRadioss|RADIOSS).{0,80}", text, re.I)
    banner = banner_match.group(0).strip() if banner_match else None
    version = None
    version_match = re.search(
        r"(?:VERSION|REV(?:ISION)?)\s*[:=]\s*([0-9A-Za-z._-]+)",
        text,
        re.I,
    )
    if version_match:
        version = version_match.group(1)
    else:
        dated = re.search(r"(latest-\d{8}|\d{8})", text)
        if dated:
            version = dated.group(1)
    return {
        "solver": "OpenRadioss",
        "version": version,
        "banner": banner,
        "source": "listing",
    }


def parse_energy_listing(text: str) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {
        "kinetic_energy": [],
        "internal_energy": [],
        "external_work": [],
        "contact_energy": [],
        "total_energy": [],
        "energy_error": [],
        "drawing_force": [],
    }
    patterns = (
        ("kinetic_energy", r"K(?:INETIC)?(?:\s|\.|-)ENERGY\s*[:=]\s*([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"),
        ("internal_energy", r"I(?:NTERNAL)?(?:\s|\.|-)ENERGY\s*[:=]\s*([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"),
        ("external_work", r"EXT(?:ERNAL)?(?:\s|\.|-)WORK\s*[:=]\s*([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"),
        ("contact_energy", r"CONTACT(?:\s|\.|-)ENERGY\s*[:=]\s*([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"),
        ("total_energy", r"T(?:OTAL)?(?:\s|\.|-)ENERGY\s*[:=]\s*([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"),
        ("energy_error", r"ENERGY\s+ERROR\s*[:=]?\s*([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"),
        ("drawing_force", r"(?:REACZ|DRAWING\s+FORCE|REACTION\s+FORCE)\s*[:=]\s*([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?)"),
    )
    for name, pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            values[name].append(float(match.group(1)))
    cycle = _parse_cycle_table(text)
    for name, series in cycle.items():
        if series:
            values[name].extend(series)
    return values


def parse_time_history_csv(work_dir: Path) -> dict[str, list[float]]:
    result: dict[str, list[float]] = {
        "kinetic_energy": [],
        "internal_energy": [],
        "external_work": [],
        "contact_energy": [],
        "total_energy": [],
        "energy_error": [],
        "drawing_force": [],
        "contact_force": [],
    }
    for path in sorted(work_dir.glob("*.csv")):
        with path.open(encoding="utf-8", errors="replace", newline="") as handle:
            rows = list(csv.reader(handle))
        if not rows:
            continue
        header = [cell.strip() for cell in rows[0]]
        pull_groups = _pull_groups(header)
        for row in rows[1:]:
            mapped = {header[i].upper(): row[i] if i < len(row) else "" for i in range(len(header))}
            _append_exact(result["kinetic_energy"], mapped, ("KINETIC ENERGY", "KENERGY"))
            _append_exact(result["internal_energy"], mapped, ("INTERNAL ENERGY", "IENERGY"))
            _append_exact(result["external_work"], mapped, ("EXTERNAL WORK", "EXT-WORK"))
            _append_exact(result["contact_energy"], mapped, ("CONTACT ENERGY",))
            _append_exact(result["total_energy"], mapped, ("TOTAL ENERGY", "TENERGY"))
            force = _row_drawing_force(row, pull_groups)
            if force is not None:
                result["drawing_force"].append(force)
    return result


def parse_field_files(work_dir: Path) -> dict[str, Any]:
    summary = work_dir / "fields.json"
    if summary.exists():
        import json

        payload = json.loads(summary.read_text(encoding="utf-8"))
        payload.setdefault("source", "fields.json")
        return payload
    vtk_values: dict[str, list[float]] = {"von_mises": [], "plastic_strain": [], "exit_radius": []}
    vtk_files = sorted(work_dir.glob("*.vtk"))
    for path in vtk_files:
        parsed = _parse_vtk(path.read_text(encoding="utf-8", errors="replace"))
        vtk_values["von_mises"].extend(parsed["von_mises"])
        vtk_values["plastic_strain"].extend(parsed["plastic_strain"])
        if parsed["exit_radius"] is not None:
            vtk_values["exit_radius"].append(parsed["exit_radius"])
    source = "vtk" if vtk_files else None
    return {
        "peak_von_mises_pa": _peak(vtk_values["von_mises"]),
        "peak_plastic_strain": _peak(vtk_values["plastic_strain"]),
        "final_outer_radius_m": _last(vtk_values["exit_radius"]),
        "maximum_damage": None,
        "source": source,
    }


def _concat_listings(work_dir: Path) -> str:
    chunks: list[str] = []
    for path in sorted(work_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in LISTING_SUFFIXES or path.name.lower().endswith(".out"):
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _parse_cycle_table(text: str) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {
        "internal_energy": [],
        "kinetic_energy": [],
        "energy_error": [],
        "total_energy": [],
        "external_work": [],
    }
    for raw in text.splitlines():
        match = CYCLE_ROW.match(raw)
        if not match:
            continue
        ie = float(match.group("ie"))
        ke = float(match.group("ke"))
        work = float(match.group("work"))
        values["internal_energy"].append(ie)
        values["kinetic_energy"].append(ke)
        values["energy_error"].append(float(match.group("err")) / 100.0)
        values["total_energy"].append(ie + ke)
        values["external_work"].append(work)
    return values


def _pull_groups(header: list[str]) -> list[list[int]]:
    indices = [i for i, cell in enumerate(header) if "PULL" in cell.upper()]
    return [indices[i : i + 3] for i in range(0, len(indices), 3)]


def _row_drawing_force(row: list[str], groups: list[list[int]]) -> float | None:
    """OpenRadioss T01 column order for TH/NODE is not the request order.

    Each pull node emits three channels (displacement, radius, reaction).
    Reaction is the large-magnitude channel; axial travel and radius stay O(1e-2).
    """
    total = 0.0
    found = False
    for group in groups:
        values: list[float] = []
        for index in group:
            if index >= len(row):
                continue
            try:
                values.append(float(row[index]))
            except ValueError:
                continue
        if not values:
            continue
        reaction = max(values, key=abs)
        # Axial travel and radius stay O(1e-2 m). Drawing reaction is newtons.
        if abs(reaction) <= 1.0:
            continue
        total += reaction
        found = True
    return total if found else None


def _append_exact(target: list[float], mapped: dict[str, str], names: tuple[str, ...]) -> None:
    for key, value in mapped.items():
        stripped = key.strip()
        if stripped in names:
            try:
                target.append(float(value))
            except ValueError:
                return
            return


def _parse_vtk(text: str) -> dict[str, Any]:
    node_ids = _vtk_scalars(text, ("NODE_ID",), point=True)
    part_ids = _vtk_scalars(text, ("PART_ID",), point=False)
    von = _vtk_scalars(text, ("2DELEM_VON_MISES", "VON_MISES", "VONMISES"), point=False)
    epsp = _vtk_scalars(text, ("2DELEM_PLASTIC_STRAIN", "PLASTIC_STRAIN", "EPSP"), point=False)
    points = _vtk_points(text)
    workpiece_cells = [i for i, part in enumerate(part_ids) if int(part) == 1] if part_ids else list(range(len(von)))
    von_w = [von[i] for i in workpiece_cells if i < len(von)]
    epsp_w = [epsp[i] for i in workpiece_cells if i < len(epsp)]
    exit_radius = None
    if points and node_ids and len(points) == len(node_ids):
        work = [(node_ids[i], points[i]) for i in range(len(points)) if node_ids[i] < WORKPIECE_NODE_LIMIT]
        if work:
            max_z = max(point[2] for _nid, point in work)
            ring = [point[1] for _nid, point in work if point[2] >= max_z - 1.0e-6]
            exit_radius = max(ring) if ring else None
    return {
        "von_mises": von_w,
        "plastic_strain": epsp_w,
        "exit_radius": exit_radius,
    }


def _vtk_scalars(text: str, names: tuple[str, ...], *, point: bool) -> list[float]:
    values: list[float] = []
    capture = False
    for raw in text.splitlines():
        upper = raw.strip().upper()
        if upper.startswith("SCALARS") and any(name in upper.replace(" ", "_") or name in upper for name in names):
            capture = True
            values = []
            continue
        if capture and (
            upper.startswith("SCALARS")
            or upper.startswith("VECTORS")
            or upper.startswith("FIELD")
            or upper.startswith("CELL_DATA")
            or upper.startswith("POINT_DATA")
        ):
            capture = False
        if not capture:
            continue
        if upper.startswith("LOOKUP"):
            continue
        for token in raw.split():
            try:
                values.append(float(token))
            except ValueError:
                capture = False
                break
    return values


def _vtk_points(text: str) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    capture = False
    remaining = 0
    coords: list[float] = []
    for raw in text.splitlines():
        if raw.startswith("POINTS"):
            parts = raw.split()
            remaining = int(parts[1]) if len(parts) > 1 else 0
            capture = True
            coords = []
            continue
        if not capture:
            continue
        coords.extend(float(tok) for tok in raw.split() if _is_float(tok))
        if len(coords) >= remaining * 3:
            for index in range(0, remaining * 3, 3):
                points.append((coords[index], coords[index + 1], coords[index + 2]))
            return points
    return points


def _is_float(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def _peak(values: list[float] | None) -> float | None:
    finite = [value for value in values or [] if _finite(value)]
    if not finite:
        return None
    return max(abs(value) for value in finite)


def _last(values: list[float] | None) -> float | None:
    finite = [value for value in values or [] if _finite(value)]
    if not finite:
        return None
    return finite[-1]


def _finite(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)
