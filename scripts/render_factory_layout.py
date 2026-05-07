#!/usr/bin/env python3
"""Draw docs/images/factory-layout.svg from config/factory_layout.yaml."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / "config" / "factory_layout.yaml"
OUTPUT = ROOT / "docs" / "images" / "factory-layout.svg"

SCALE = 10.0
PAD_LEFT = 56.0
PAD_TOP = 40.0
PAD_RIGHT = 24.0
PAD_BOTTOM = 110.0
HALL_X = 96.0
HALL_Y = 41.13

ASSET_RE = re.compile(
    r"\{id:\s*(?P<id>[\w.]+),\s*type:\s*(?P<type>\w+),"
    r"\s*x:\s*(?P<x>[-0-9.]+),\s*y:\s*(?P<y>[-0-9.]+),"
    r"\s*z:\s*(?P<z>[-0-9.]+),\s*l:\s*(?P<l>[-0-9.]+),"
    r"\s*w:\s*(?P<w>[-0-9.]+),\s*h:\s*(?P<h>[-0-9.]+)\}"
)
CRANE_RE = re.compile(
    r"\{id:\s*(?P<id>[\w.]+),\s*x_min:\s*(?P<x_min>[-0-9.]+),"
    r"\s*x_max:\s*(?P<x_max>[-0-9.]+),\s*y_min:\s*(?P<y_min>[-0-9.]+),"
    r"\s*y_max:\s*(?P<y_max>[-0-9.]+)\}"
)

TYPE_FILL = {
    "DrawingMachine": "#93c5fd",
    "PilgerMill": "#86efac",
    "HeatTreatmentLine": "#fdba74",
    "EddyCurrentInspection": "#c4b5fd",
    "HydroTest": "#c4b5fd",
    "DimensionInspection": "#c4b5fd",
    "VisualInspection": "#c4b5fd",
    "StraighteningLine": "#67e8f9",
    "CuttingLine": "#67e8f9",
    "WashingLine": "#f9a8d4",
    "PointingMachine": "#fde047",
    "RawMaterialRack": "#e2e8f0",
    "FinishedGoodsRack": "#e2e8f0",
    "PackingZone": "#cbd5e1",
    "HeatRecovery": "#fecaca",
    "OilCirculation": "#fecaca",
    "GasSystem": "#fecaca",
    "ControlElectrical": "#fecaca",
    "MaintenanceZone": "#fcd34d",
    "UtilityZone": "#fcd34d",
}


def sx(x: float) -> float:
    return PAD_LEFT + x * SCALE


def sy_top(y: float, height: float) -> float:
    return PAD_TOP + (HALL_Y - (y + height)) * SCALE


def short_id(asset_id: str) -> str:
    parts = asset_id.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return asset_id


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def parse_layout(text: str) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
    assets = []
    for match in ASSET_RE.finditer(text):
        assets.append(
            {
                "id": match.group("id"),
                "type": match.group("type"),
                "x": float(match.group("x")),
                "y": float(match.group("y")),
                "l": float(match.group("l")),
                "w": float(match.group("w")),
            }
        )
    cranes = []
    for match in CRANE_RE.finditer(text):
        cranes.append(
            {
                "id": match.group("id"),
                "x_min": float(match.group("x_min")),
                "x_max": float(match.group("x_max")),
                "y_min": float(match.group("y_min")),
                "y_max": float(match.group("y_max")),
            }
        )
    return assets, cranes


def main() -> None:
    text = LAYOUT.read_text(encoding="utf-8")
    assets, cranes = parse_layout(text)
    if len(assets) != 23:
        raise SystemExit(f"expected 23 assets, found {len(assets)}")
    if len(cranes) != 3:
        raise SystemExit(f"expected 3 cranes, found {len(cranes)}")

    width = PAD_LEFT + HALL_X * SCALE + PAD_RIGHT
    height = PAD_TOP + HALL_Y * SCALE + PAD_BOTTOM
    hall_y0 = PAD_TOP
    hall_h = HALL_Y * SCALE
    bay_h = 13.71 * SCALE

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" width="{width:.0f}" height="{height:.0f}" role="img" aria-label="Main factory floor plan in meters">',
        "<title>Main factory floor plan</title>",
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#0f172a} .muted{fill:#475569} .tiny{font-size:10px} .label{font-size:11px;font-weight:700} .axis{font-size:11px}</style>',
        f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="#f8fafc"/>',
        f'<text x="{PAD_LEFT:.1f}" y="24" font-size="18" font-weight="700">Main factory floor plan (meters)</text>',
        '<text x="56" y="38" class="tiny muted">Origin is the south-west floor corner. X is hall length. Y is hall width. Highlighted box is Drawing 4.</text>',
        f'<rect x="{PAD_LEFT:.1f}" y="{hall_y0:.1f}" width="{HALL_X * SCALE:.1f}" height="{bay_h:.1f}" fill="#ffedd5"/>',
        f'<rect x="{PAD_LEFT:.1f}" y="{hall_y0 + bay_h:.1f}" width="{HALL_X * SCALE:.1f}" height="{bay_h:.1f}" fill="#dcfce7"/>',
        f'<rect x="{PAD_LEFT:.1f}" y="{hall_y0 + 2 * bay_h:.1f}" width="{HALL_X * SCALE:.1f}" height="{bay_h:.1f}" fill="#dbeafe"/>',
        f'<text x="{PAD_LEFT + 8:.1f}" y="{hall_y0 + hall_h - 8:.1f}" class="tiny muted">Bay A</text>',
        f'<text x="{PAD_LEFT + 8:.1f}" y="{hall_y0 + hall_h - bay_h - 8:.1f}" class="tiny muted">Bay B</text>',
        f'<text x="{PAD_LEFT + 8:.1f}" y="{hall_y0 + hall_h - 2 * bay_h - 8:.1f}" class="tiny muted">Bay C</text>',
    ]

    for x in range(0, 97, 8):
        x_px = sx(x)
        parts.append(
            f'<line x1="{x_px:.1f}" y1="{hall_y0:.1f}" x2="{x_px:.1f}" y2="{hall_y0 + hall_h:.1f}" stroke="#94a3b8" stroke-width="0.6"/>'
        )
        parts.append(f'<text x="{x_px:.1f}" y="{hall_y0 + hall_h + 14:.1f}" text-anchor="middle" class="axis muted">{x}</text>')

    for y in (0.0, 13.71, 27.42, 41.13):
        y_px = PAD_TOP + (HALL_Y - y) * SCALE
        parts.append(
            f'<line x1="{PAD_LEFT:.1f}" y1="{y_px:.1f}" x2="{PAD_LEFT + HALL_X * SCALE:.1f}" y2="{y_px:.1f}" stroke="#64748b" stroke-width="0.8"/>'
        )
        parts.append(
            f'<text x="{PAD_LEFT - 8:.1f}" y="{y_px + 4:.1f}" text-anchor="end" class="axis muted">{y:g}</text>'
        )

    for crane in cranes:
        x = sx(float(crane["x_min"]))
        y = sy_top(float(crane["y_min"]), float(crane["y_max"]) - float(crane["y_min"]))
        w = (float(crane["x_max"]) - float(crane["x_min"])) * SCALE
        h = (float(crane["y_max"]) - float(crane["y_min"])) * SCALE
        label = short_id(str(crane["id"]))
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="#334155" stroke-width="1.2" stroke-dasharray="6 4"/>'
        )
        parts.append(
            f'<text x="{x + 6:.1f}" y="{y + 14:.1f}" class="tiny muted">{xml_escape(label)} crane</text>'
        )

    for asset in assets:
        x = sx(float(asset["x"]))
        y = sy_top(float(asset["y"]), float(asset["w"]))
        w = float(asset["l"]) * SCALE
        h = float(asset["w"]) * SCALE
        fill = TYPE_FILL.get(str(asset["type"]), "#e2e8f0")
        asset_id = str(asset["id"])
        is_hero = asset_id == "BG.MIEUM.DRW.04"
        stroke = "#1e3a8a" if is_hero else "#1e293b"
        stroke_w = 2.4 if is_hero else 0.9
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}" rx="2"/>'
        )
        label = short_id(asset_id)
        font_size = 12 if is_hero else 10
        parts.append(
            f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + 4:.1f}" text-anchor="middle" class="label" font-size="{font_size}">{xml_escape(label)}</text>'
        )

    parts.append(
        f'<rect x="{PAD_LEFT:.1f}" y="{hall_y0:.1f}" width="{HALL_X * SCALE:.1f}" height="{hall_h:.1f}" fill="none" stroke="#0f172a" stroke-width="2"/>'
    )

    legend_y = hall_y0 + hall_h + 36
    legend = [
        ("#93c5fd", "Drawing"),
        ("#86efac", "Pilger"),
        ("#fdba74", "Heat treatment"),
        ("#c4b5fd", "Inspection"),
        ("#e2e8f0", "Racks"),
        ("#fecaca", "Utilities"),
    ]
    cursor = PAD_LEFT
    parts.append(f'<text x="{PAD_LEFT:.1f}" y="{legend_y:.1f}" class="tiny muted">96 m x 41.13 m x 14.2 m hall. Coordinates come from config/factory_layout.yaml.</text>')
    for fill, name in legend:
        parts.append(f'<rect x="{cursor:.1f}" y="{legend_y + 10:.1f}" width="14" height="14" fill="{fill}" stroke="#1e293b"/>')
        parts.append(f'<text x="{cursor + 20:.1f}" y="{legend_y + 21:.1f}" class="tiny">{name}</text>')
        cursor += 120

    parts.append("</svg>")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
