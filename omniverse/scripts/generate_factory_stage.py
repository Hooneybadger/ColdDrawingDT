from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from cold_drawing_twin.paths import CONFIG_DIR, REPO_ROOT
from omniverse.scripts.visual_usd import (
    CLASS_FOLDER,
    facility_lines,
    lights_and_cameras,
    write_drawing_04,
    write_machine_asset,
    write_shared_assets,
)

OUTPUT = REPO_ROOT / "usd" / "factory" / "bugok_factory.usda"


def generate(output: Path = OUTPUT) -> Path:
    write_shared_assets()
    write_drawing_04()
    layout = yaml.safe_load((CONFIG_DIR / "factory_layout.yaml").read_text(encoding="utf-8"))
    registry = yaml.safe_load((CONFIG_DIR / "asset_registry.yaml").read_text(encoding="utf-8"))["assets"]
    hall = layout["main_factory"]["size"]
    placed: dict[str, list[str]] = defaultdict(list)

    def add_machine(prim: str, x: float, y: float, z: float, l: float, w: float, h: float, asset_id: str, kind: str) -> None:
        parent = prim.rsplit("/", 1)[0]
        name = prim.rsplit("/", 1)[1]
        cx, cy = x + l / 2.0, y + w / 2.0
        if asset_id == "BG.MIEUM.DRW.04":
            rel = "../assets/drawing/Drawing_04.usda"
            z_pos = 0.0
        else:
            path = write_machine_asset(name, kind, l, w, h, asset_id)
            folder = CLASS_FOLDER.get(kind, "machines")
            rel = f"../assets/{folder}/{path.name}"
            z_pos = z if kind == "OverheadCrane" else 0.0
        placed[parent].append(
            "\n".join(
                [
                    f'            def Xform "{name}" (',
                    f"                prepend references = @{rel}@",
                    "            )",
                    "            {",
                    f"                double3 xformOp:translate = ({cx}, {cy}, {z_pos})",
                    '                uniform token[] xformOpOrder = ["xformOp:translate"]',
                    f'                custom string coldDrawing:assetId = "{asset_id}"',
                    "            }",
                ]
            )
        )

    for asset in layout["assets"]:
        item = registry[asset["id"]]
        add_machine(
            item["usd_prim"],
            asset["x"],
            asset["y"],
            asset["z"],
            asset["l"],
            asset["w"],
            asset["h"],
            asset["id"],
            item["class"],
        )
    for crane in layout["cranes"]:
        item = registry[crane["id"]]
        add_machine(
            item["usd_prim"],
            crane["x_min"],
            crane["y_min"],
            12.0,
            crane["x_max"] - crane["x_min"],
            crane["y_max"] - crane["y_min"],
            0.6,
            crane["id"],
            item["class"],
        )

    folders = {
        "/World/BugokFactory/Production": [
            "Drawing",
            "Pilger",
            "HeatTreatment",
            "Pointing",
            "Cleaning",
            "Straightening",
            "Cutting",
            "Packaging",
        ],
        "/World/BugokFactory/Inspection": ["ECT", "Hydro", "Dimension", "Visual"],
        "/World/BugokFactory/MaterialHandling": ["Racks", "Cranes"],
        "/World/BugokFactory/Utilities": ["HeatRecovery", "OilCirculation", "Gas", "Electrical", "Maintenance", "General"],
    }

    lines = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "World"',
        "    metersPerUnit = 1",
        '    upAxis = "Z"',
        '    doc = "Conceptual OpenUSD industrial Digital Twin scene. Not mill CAD."',
        ")",
        "",
        'def Xform "World"',
        "{",
        '    def Xform "BugokFactory"',
        "    {",
        '        def Xform "Facility"',
        "        {",
    ]
    lines.extend(facility_lines(hall["x"], hall["y"], layout["main_factory"]["grid"]["x"], layout["main_factory"]["grid"]["y"], indent=12))
    lines.append("        }")
    for section, children in folders.items():
        section_name = section.rsplit("/", 1)[1]
        lines.append(f'        def Xform "{section_name}"')
        lines.append("        {")
        for child in children:
            child_path = f"{section}/{child}"
            lines.append(f'            def Xform "{child}"')
            lines.append("            {")
            for block in placed.get(child_path, []):
                for raw in block.splitlines():
                    lines.append("    " + raw)
            lines.append("            }")
        lines.append("        }")
    lines.append("    }")
    lines.extend(lights_and_cameras(hall["x"], hall["y"], indent=4))
    lines.append("}")
    lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(generate())
