from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from cold_drawing_twin.paths import CONFIG_DIR, REPO_ROOT

OUTPUT = REPO_ROOT / "usd" / "factory" / "bugok_factory.usda"


def generate(output: Path = OUTPUT) -> Path:
    layout = yaml.safe_load((CONFIG_DIR / "factory_layout.yaml").read_text(encoding="utf-8"))
    registry = yaml.safe_load((CONFIG_DIR / "asset_registry.yaml").read_text(encoding="utf-8"))["assets"]
    hall = layout["main_factory"]["size"]
    placed: dict[str, list[str]] = defaultdict(list)

    def add_box(prim: str, x: float, y: float, z: float, l: float, w: float, h: float, asset_id: str) -> None:
        parent = prim.rsplit("/", 1)[0]
        name = prim.rsplit("/", 1)[1]
        cx, cy, cz = x + l / 2.0, y + w / 2.0, z + h / 2.0
        placed[parent].append(
            "\n".join(
                [
                    f'            def Xform "{name}"',
                    "            {",
                    f"                double3 xformOp:translate = ({cx}, {cy}, {cz})",
                    '                uniform token[] xformOpOrder = ["xformOp:translate"]',
                    f'                custom string coldDrawing:assetId = "{asset_id}"',
                    '                def Cube "proxy" (purpose = "proxy")',
                    "                {",
                    "                    double size = 1",
                    f"                    float3 xformOp:scale = ({l}, {w}, {h})",
                    '                    uniform token[] xformOpOrder = ["xformOp:scale"]',
                    "                }",
                    '                def Cube "render" (purpose = "render")',
                    "                {",
                    "                    double size = 1",
                    f"                    float3 xformOp:scale = ({l}, {w}, {h})",
                    '                    uniform token[] xformOpOrder = ["xformOp:scale"]',
                    "                }",
                    "            }",
                ]
            )
        )

    for asset in layout["assets"]:
        prim = registry[asset["id"]]["usd_prim"]
        add_box(prim, asset["x"], asset["y"], asset["z"], asset["l"], asset["w"], asset["h"], asset["id"])
    for crane in layout["cranes"]:
        prim = registry[crane["id"]]["usd_prim"]
        add_box(
            prim,
            crane["x_min"],
            crane["y_min"],
            12.0,
            crane["x_max"] - crane["x_min"],
            crane["y_max"] - crane["y_min"],
            0.6,
            crane["id"],
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
        ")",
        "",
        'def Xform "World"',
        "{",
        '    def Xform "BugokFactory"',
        "    {",
        '        def Xform "Buildings"',
        "        {",
        '            def Cube "MainFactory"',
        "            {",
        "                double size = 1",
        f"                float3 xformOp:scale = ({hall['x']}, {hall['y']}, 0.2)",
        f"                double3 xformOp:translate = ({hall['x'] / 2.0}, {hall['y'] / 2.0}, -0.1)",
        '                uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]',
        "            }",
        "        }",
    ]
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
    lines.append("}")
    lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    drawing = REPO_ROOT / "usd" / "assets" / "drawing" / "Drawing_04.usda"
    drawing.parent.mkdir(parents=True, exist_ok=True)
    drawing.write_text(
        '#usda 1.0\n(\n    defaultPrim = "Drawing_04"\n)\n\ndef Xform "Drawing_04"\n{\n    custom string coldDrawing:assetId = "BG.MIEUM.DRW.04"\n}\n',
        encoding="utf-8",
    )
    return output


if __name__ == "__main__":
    print(generate())
