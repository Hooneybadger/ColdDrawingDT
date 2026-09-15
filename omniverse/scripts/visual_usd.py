"""Conceptual OpenUSD industrial geometry. Display only. Not mill CAD."""

from __future__ import annotations

from pathlib import Path

from cold_drawing_twin.paths import REPO_ROOT

DRAWING_04 = REPO_ROOT / "usd" / "assets" / "drawing" / "Drawing_04.usda"

FLOOR = (0.07, 0.07, 0.068)
STEEL = (0.14, 0.15, 0.16)
HOUSING = (0.44, 0.46, 0.49)
GUARD = (0.64, 0.65, 0.66)
WORK = (0.97, 0.98, 0.995)
WORK_OUT = (0.90, 0.91, 0.93)
DIE = (0.03, 0.031, 0.035)
CABINET = (0.74, 0.75, 0.72)
YELLOW = (0.80, 0.64, 0.14)
FURNACE = (0.42, 0.33, 0.26)
TANK = (0.28, 0.38, 0.40)
MARK = (0.84, 0.72, 0.16)
COLUMN = (0.24, 0.25, 0.26)
CONCRETE = (0.22, 0.22, 0.21)
WALL = (0.18, 0.185, 0.19)
CEILING = (0.14, 0.145, 0.15)
LAMP_OFF = (0.14, 0.14, 0.14)
LAMP_G = (0.08, 0.22, 0.10)
LAMP_A = (0.28, 0.20, 0.05)
LAMP_B = (0.08, 0.14, 0.28)
LAMP_R = (0.28, 0.08, 0.08)

CLASS_FOLDER = {
    "DrawingMachine": "drawing",
    "PointingMachine": "pointing",
    "PilgerMill": "pilger",
    "HeatTreatmentLine": "heat_treatment",
    "WashingLine": "cleaning",
    "StraighteningLine": "straightening",
    "CuttingLine": "cutting",
    "PackingZone": "packaging",
    "FinishedGoodsRack": "packaging",
    "RawMaterialRack": "packaging",
    "DimensionInspection": "inspection",
    "EddyCurrentInspection": "inspection",
    "HydroTest": "inspection",
    "VisualInspection": "inspection",
    "OverheadCrane": "handling",
    "HeatRecovery": "utilities",
    "OilCirculation": "utilities",
    "GasSystem": "utilities",
    "ControlElectrical": "utilities",
    "MaintenanceZone": "utilities",
    "UtilityZone": "utilities",
}

MATERIALS = REPO_ROOT / "usd" / "materials" / "industrial_materials.usda"
CAMERAS = REPO_ROOT / "usd" / "cameras" / "stage_cameras.usda"


def _c(color: tuple[float, float, float]) -> str:
    return f"({color[0]}, {color[1]}, {color[2]})"


def cube(name: str, sx: float, sy: float, sz: float, x: float, y: float, z: float, color, *, purpose: str | None = "render", indent: int = 4) -> list[str]:
    pad = " " * indent
    header = f'{pad}def Cube "{name}"' + (f" (\n{pad}    purpose = \"{purpose}\"\n{pad})" if purpose else "")
    return [
        header,
        f"{pad}{{",
        f"{pad}    double size = 1",
        f"{pad}    float3 xformOp:scale = ({sx:.4f}, {sy:.4f}, {sz:.4f})",
        f"{pad}    double3 xformOp:translate = ({x:.4f}, {y:.4f}, {z:.4f})",
        f'{pad}    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]',
        f"{pad}    color3f[] primvars:displayColor = [{_c(color)}]",
        f"{pad}}}",
    ]


def cylinder(name: str, radius: float, height: float, x: float, y: float, z: float, color, *, axis: str = "X", purpose: str = "render", indent: int = 4) -> list[str]:
    pad = " " * indent
    return [
        f'{pad}def Cylinder "{name}" (',
        f'{pad}    purpose = "{purpose}"',
        f"{pad})",
        f"{pad}{{",
        f"{pad}    double radius = {radius:.4f}",
        f"{pad}    double height = {height:.4f}",
        f'{pad}    token axis = "{axis}"',
        f"{pad}    double3 xformOp:translate = ({x:.4f}, {y:.4f}, {z:.4f})",
        f'{pad}    uniform token[] xformOpOrder = ["xformOp:translate"]',
        f"{pad}    color3f[] primvars:displayColor = [{_c(color)}]",
        f"{pad}}}",
    ]


def sphere(name: str, radius: float, x: float, y: float, z: float, color, *, purpose: str = "render", indent: int = 4) -> list[str]:
    pad = " " * indent
    return [
        f'{pad}def Sphere "{name}" (',
        f'{pad}    purpose = "{purpose}"',
        f"{pad})",
        f"{pad}{{",
        f"{pad}    double radius = {radius:.4f}",
        f"{pad}    double3 xformOp:translate = ({x:.4f}, {y:.4f}, {z:.4f})",
        f'{pad}    uniform token[] xformOpOrder = ["xformOp:translate"]',
        f"{pad}    color3f[] primvars:displayColor = [{_c(color)}]",
        f"{pad}}}",
    ]


def xform(name: str, children: list[str], indent: int = 4) -> list[str]:
    pad = " " * indent
    out = [f'{pad}def Xform "{name}"', f"{pad}{{"]
    for line in children:
        out.append(line if line.startswith(" ") else (" " * (indent + 4) + line))
    out.append(f"{pad}}}")
    return out


def _shift(lines: list[str], extra: int) -> list[str]:
    pad = " " * extra
    return [pad + line if line else line for line in lines]


def drawing_04_usda() -> str:
    """Hero cold-drawing line. Conceptual proportions. Origin at floor center.

    Storm may draw purpose=proxy, so proxy volumes stay tiny. The render
    silhouette is rails + die portal + workpiece + carriage, not a slab.
    Status tower sits on the -Y (south) side so a 3/4 south camera sees it.
    """
    z_bar = 1.08
    ty = -2.15
    lines: list[str] = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "Drawing_04"',
        "    metersPerUnit = 1",
        '    upAxis = "Z"',
        '    doc = "Conceptual OpenUSD industrial equipment representation for Drawing 4. Not mill CAD."',
        ")",
        "",
        'def Xform "Drawing_04"',
        "{",
        '    custom string coldDrawing:assetId = "BG.MIEUM.DRW.04"',
        '    custom string coldDrawing:verdict = ""',
        '    custom string coldDrawing:quality = ""',
        '    custom string coldDrawing:feaRunning = "false"',
        '    custom string coldDrawing:lastUpdate = ""',
        "",
        '    def Xform "Frame"',
        "    {",
    ]
    lines += cube("proxy", 0.04, 0.04, 0.04, 0, 0, 0.04, STEEL, purpose="proxy", indent=8)
    lines += cube("WebL", 33.5, 0.10, 0.48, 0, -0.82, 0.42, STEEL, indent=8)
    lines += cube("FlangeLT", 33.5, 0.28, 0.08, 0, -0.82, 0.68, HOUSING, indent=8)
    lines += cube("FlangeLB", 33.5, 0.28, 0.08, 0, -0.82, 0.18, HOUSING, indent=8)
    lines += cube("WebR", 33.5, 0.10, 0.48, 0, 0.82, 0.42, STEEL, indent=8)
    lines += cube("FlangeRT", 33.5, 0.28, 0.08, 0, 0.82, 0.68, HOUSING, indent=8)
    lines += cube("FlangeRB", 33.5, 0.28, 0.08, 0, 0.82, 0.18, HOUSING, indent=8)
    for i, x in enumerate((-15.5, -8.0, 0.0, 8.0, 15.5)):
        lines += cube(f"Sleeper{i}", 0.35, 2.2, 0.16, x, 0, 0.10, STEEL, indent=8)
        lines += cube(f"FootL{i}", 0.38, 0.38, 0.14, x, -1.15, 0.08, STEEL, indent=8)
        lines += cube(f"FootR{i}", 0.38, 0.38, 0.14, x, 1.15, 0.08, STEEL, indent=8)
    lines += ["    }", ""]

    lines += ['    def Xform "Base"', "    {"]
    lines += cube("Pad", 34.2, 3.4, 0.10, 0, 0, 0.05, CONCRETE, indent=8)
    lines += ["    }", ""]

    lines += ['    def Xform "MainFrame"', "    {"]
    lines += cube("PostSW", 0.22, 0.22, 2.6, -16.0, -1.7, 1.4, STEEL, indent=8)
    lines += cube("PostSE", 0.22, 0.22, 2.6, 16.0, -1.7, 1.4, STEEL, indent=8)
    lines += cube("PostNW", 0.22, 0.22, 2.6, -16.0, 1.7, 1.4, STEEL, indent=8)
    lines += cube("PostNE", 0.22, 0.22, 2.6, 16.0, 1.7, 1.4, STEEL, indent=8)
    lines += cube("TieS", 32.0, 0.12, 0.12, 0, -1.7, 2.65, STEEL, indent=8)
    lines += cube("TieN", 32.0, 0.12, 0.12, 0, 1.7, 2.65, STEEL, indent=8)
    lines += cube("BraceA", 0.12, 3.4, 0.12, -8.0, 0, 2.65, STEEL, indent=8)
    lines += cube("BraceB", 0.12, 3.4, 0.12, 8.0, 0, 2.65, STEEL, indent=8)
    lines += ["    }", ""]

    lines += ['    def Xform "Entry"', "    {"]
    lines += cube("proxy", 0.04, 0.04, 0.04, -14, 0, 0.05, HOUSING, purpose="proxy", indent=8)
    lines += cube("render", 5.6, 1.6, 0.10, -13.6, 0, 0.62, HOUSING, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "EntryTable"', "    {"]
    lines += cube("Deck", 5.8, 1.7, 0.10, -13.6, 0, 0.72, HOUSING, indent=8)
    lines += cube("LegA", 0.16, 0.16, 0.72, -16.1, -0.65, 0.36, STEEL, indent=8)
    lines += cube("LegB", 0.16, 0.16, 0.72, -16.1, 0.65, 0.36, STEEL, indent=8)
    lines += cube("LegC", 0.16, 0.16, 0.72, -11.2, -0.65, 0.36, STEEL, indent=8)
    lines += cube("LegD", 0.16, 0.16, 0.72, -11.2, 0.65, 0.36, STEEL, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "EntryGuide"', "    {"]
    for i, x in enumerate((-15.2, -13.8, -12.4, -11.0, -9.6)):
        lines += cylinder(f"Roll{i}", 0.13, 1.22, x, 0, 0.82, GUARD, axis="Y", indent=8)
        lines += cube(f"Stand{i}L", 0.14, 0.14, 0.78, x, -0.68, 0.48, STEEL, indent=8)
        lines += cube(f"Stand{i}R", 0.14, 0.14, 0.78, x, 0.68, 0.48, STEEL, indent=8)
        lines += cylinder(f"Cap{i}L", 0.08, 0.10, x, -0.68, 0.92, STEEL, axis="Y", indent=8)
        lines += cylinder(f"Cap{i}R", 0.08, 0.10, x, 0.68, 0.92, STEEL, axis="Y", indent=8)
    lines += cube("Throat", 0.42, 1.15, 1.12, -8.55, 0, z_bar, STEEL, indent=8)
    lines += cylinder("ThroatBore", 0.28, 0.44, -8.55, 0, z_bar, DIE, axis="X", indent=8)
    lines += ["    }", ""]

    lines += ['    def Xform "Die"', "    {"]
    lines += cube("proxy", 0.04, 0.04, 0.04, -2.1, 0, 0.05, DIE, purpose="proxy", indent=8)
    lines += cylinder("render", 0.52, 0.38, -2.10, 0, z_bar, DIE, axis="X", indent=8)
    lines += cylinder("FlangeW", 0.78, 0.12, -2.58, 0, z_bar, DIE, axis="X", indent=8)
    lines += cylinder("StackA", 0.70, 0.10, -2.42, 0, z_bar, DIE, axis="X", indent=8)
    lines += cylinder("StackB", 0.62, 0.10, -2.30, 0, z_bar, (0.07, 0.07, 0.08), axis="X", indent=8)
    lines += cylinder("StackC", 0.54, 0.12, -2.16, 0, z_bar, DIE, axis="X", indent=8)
    lines += cylinder("Collar", 0.66, 0.10, -1.78, 0, z_bar, (0.20, 0.20, 0.21), axis="X", indent=8)
    lines += cylinder("FlangeE", 0.74, 0.12, -1.62, 0, z_bar, DIE, axis="X", indent=8)
    lines += cylinder("Bore", 0.16, 0.72, -2.10, 0, z_bar, (0.02, 0.02, 0.02), axis="X", indent=8)
    lines += ["    }"]
    lines += ['    def Xform "DieSupport"', "    {"]
    lines += cube("Plinth", 2.35, 2.05, 0.28, -2.10, 0, 0.20, STEEL, indent=8)
    lines += cube("ColumnL", 0.32, 0.38, 1.15, -2.85, 0.55, 0.85, STEEL, indent=8)
    lines += cube("ColumnR", 0.32, 0.38, 1.15, -1.35, 0.55, 0.85, STEEL, indent=8)
    lines += cube("BraceN", 1.85, 0.16, 0.16, -2.10, 0.72, 1.55, STEEL, indent=8)
    lines += cube("Sill", 2.10, 0.22, 0.18, -2.10, -0.85, 0.42, STEEL, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "DieHousing"', "    {"]
    lines += cube("WallN", 1.85, 0.32, 1.55, -2.10, 0.92, 1.28, DIE, indent=8)
    lines += cube("Roof", 1.90, 0.95, 0.16, -2.10, 0.48, 2.12, DIE, indent=8)
    lines += cube("Anvil", 1.90, 1.15, 0.28, -2.10, 0.18, 0.36, STEEL, indent=8)
    lines += cube("CheekW", 0.18, 0.85, 1.15, -2.95, 0.28, 1.18, DIE, indent=8)
    lines += cube("CheekE", 0.18, 0.85, 1.15, -1.25, 0.28, 1.18, DIE, indent=8)
    lines += cube("ToolBand", 1.90, 0.06, 0.08, -2.10, -0.72, 0.55, YELLOW, indent=8)
    lines += cube("FaceMark", 0.06, 0.55, 0.55, -2.95, -0.05, z_bar, YELLOW, indent=8)
    lines += ["    }", ""]

    lines += ['    def Xform "Workpiece"', "    {"]
    lines += cube("proxy", 0.04, 0.04, 0.04, 0, 0, 0.05, WORK, purpose="proxy", indent=8)
    lines += cylinder("render", 0.16, 0.8, -2.1, 0, z_bar, WORK, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "Workpiece_Input"', "    {"]
    lines += cylinder("Bar", 0.26, 10.8, -8.05, 0, z_bar, WORK, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "Workpiece_ThroughDie"', "    {"]
    lines += cylinder("Bar", 0.18, 1.55, -2.10, 0, z_bar, WORK, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "Workpiece_Output"', "    {"]
    lines += cylinder("Bar", 0.13, 15.4, 6.55, 0, z_bar, WORK_OUT, indent=8)
    lines += ["    }", ""]

    lines += ['    def Xform "CarriageGuideRails"', "    {"]
    lines += cube("HeadL", 22.5, 0.14, 0.12, 4.2, -0.82, 0.78, HOUSING, indent=8)
    lines += cube("HeadR", 22.5, 0.14, 0.12, 4.2, 0.82, 0.78, HOUSING, indent=8)
    for i, x in enumerate((0.0, 4.0, 8.0, 12.0)):
        lines += cube(f"ClipL{i}", 0.22, 0.32, 0.10, x, -0.82, 0.72, STEEL, indent=8)
        lines += cube(f"ClipR{i}", 0.22, 0.32, 0.10, x, 0.82, 0.72, STEEL, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "PullingSection"', "    {"]
    lines += cube("Carriage", 2.15, 1.18, 0.38, 8.85, 0, 1.18, HOUSING, indent=8)
    lines += cube("Chassis", 2.40, 1.62, 0.16, 8.85, 0, 0.86, STEEL, indent=8)
    lines += cube("Stripe", 2.15, 0.08, 0.08, 8.85, -0.58, 1.24, YELLOW, indent=8)
    lines += cube("MastL", 0.16, 0.16, 1.45, 8.05, -0.48, 1.78, STEEL, indent=8)
    lines += cube("MastR", 0.16, 0.16, 1.45, 8.05, 0.48, 1.78, STEEL, indent=8)
    lines += cube("Yoke", 0.16, 1.12, 0.16, 8.05, 0, 2.48, STEEL, indent=8)
    lines += cube("Winch", 0.68, 0.68, 0.48, 9.55, 0, 1.52, STEEL, indent=8)
    lines += cylinder("Drum", 0.20, 0.58, 9.55, 0, 1.72, DIE, axis="Y", indent=8)
    lines += cube("Ram", 1.35, 0.26, 0.26, 7.45, 0, z_bar, STEEL, indent=8)
    lines += cube("GripHousing", 0.85, 0.72, 0.58, 7.05, 0, z_bar, DIE, indent=8)
    lines += cube("JawS", 0.48, 0.14, 0.28, 6.72, -0.20, z_bar, DIE, indent=8)
    lines += cube("JawN", 0.48, 0.14, 0.28, 6.72, 0.20, z_bar, DIE, indent=8)
    lines += cube("JawFace", 0.10, 0.42, 0.22, 6.48, 0, z_bar, (0.22, 0.22, 0.23), indent=8)
    lines += cube("Drawbar", 3.8, 0.06, 0.06, 5.2, 0, z_bar, STEEL, indent=8)
    lines += cube("Drive", 1.35, 0.88, 0.58, 10.45, 0, 0.66, STEEL, indent=8)
    lines += cylinder("WheelS", 0.22, 0.24, 8.15, -0.82, 0.52, HOUSING, axis="Y", indent=8)
    lines += cylinder("WheelN", 0.22, 0.24, 8.15, 0.82, 0.52, HOUSING, axis="Y", indent=8)
    lines += cylinder("WheelS2", 0.22, 0.24, 9.55, -0.82, 0.52, HOUSING, axis="Y", indent=8)
    lines += cylinder("WheelN2", 0.22, 0.24, 9.55, 0.82, 0.52, HOUSING, axis="Y", indent=8)
    lines += ["    }"]
    lines += ['    def Xform "Exit"', "    {"]
    lines += cube("proxy", 0.04, 0.04, 0.04, 14.2, 0, 0.05, GUARD, purpose="proxy", indent=8)
    lines += cube("render", 0.22, 0.78, 0.78, 14.2, 0, z_bar, GUARD, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "ExitGuide"', "    {"]
    for i, x in enumerate((12.4, 13.8, 15.2, 16.6)):
        lines += cylinder(f"Roll{i}", 0.10, 0.95, x, 0, 0.92, GUARD, axis="Y", indent=8)
        lines += cube(f"Stand{i}L", 0.12, 0.12, 0.7, x, -0.52, 0.50, STEEL, indent=8)
        lines += cube(f"Stand{i}R", 0.12, 0.12, 0.7, x, 0.52, 0.50, STEEL, indent=8)
    lines += cube("OutTable", 4.4, 1.35, 0.10, 16.6, 0, 0.66, HOUSING, indent=8)
    lines += ["    }", ""]

    lines += ['    def Xform "Guarding"', "    {"]
    for i, x in enumerate((-12.0, 4.0, 10.5, 16.0)):
        lines += cube(f"PostS{i}", 0.10, 0.10, 1.55, x, -1.88, 1.05, STEEL, indent=8)
        lines += cube(f"PostN{i}", 0.10, 0.10, 1.55, x, 1.88, 1.05, STEEL, indent=8)
    lines += cube("RailN", 22.0, 0.05, 0.05, 3.0, 1.88, 1.72, GUARD, indent=8)
    lines += cube("RailN2", 22.0, 0.05, 0.05, 3.0, 1.88, 1.12, GUARD, indent=8)
    lines += cube("RailSW", 6.4, 0.05, 0.05, -12.6, -1.88, 1.72, GUARD, indent=8)
    lines += cube("RailSW2", 6.4, 0.05, 0.05, -12.6, -1.88, 1.12, GUARD, indent=8)
    lines += cube("RailSE", 10.4, 0.05, 0.05, 11.4, -1.88, 1.72, GUARD, indent=8)
    lines += cube("RailSE2", 10.4, 0.05, 0.05, 11.4, -1.88, 1.12, GUARD, indent=8)
    lines += cube("KickS", 22.5, 0.08, 0.16, 2.5, -1.88, 0.26, YELLOW, indent=8)
    lines += cube("KickN", 22.5, 0.08, 0.16, 2.5, 1.88, 0.26, YELLOW, indent=8)
    lines += cube("MeshHintN", 6.5, 0.02, 0.85, 4.0, 1.88, 1.42, (0.55, 0.56, 0.57), indent=8)
    lines += ["    }"]
    lines += ['    def Xform "AccessGate"', "    {"]
    lines += cube("PostW", 0.12, 0.12, 1.65, 1.55, -1.88, 1.10, YELLOW, indent=8)
    lines += cube("PostE", 0.12, 0.12, 1.65, 3.05, -1.88, 1.10, YELLOW, indent=8)
    lines += cube("Leaf", 1.35, 0.04, 1.15, 2.30, -2.05, 1.05, GUARD, indent=8)
    lines += cube("Latch", 0.16, 0.08, 0.10, 2.95, -2.10, 1.15, STEEL, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "ControlCabinet"', "    {"]
    lines += cube("Body", 0.95, 0.48, 1.72, 3.55, ty - 0.55, 0.98, CABINET, indent=8)
    lines += cube("Door", 0.82, 0.05, 1.40, 3.55, ty - 0.80, 1.00, (0.58, 0.59, 0.56), indent=8)
    lines += cube("Screen", 0.42, 0.03, 0.28, 3.40, ty - 0.83, 1.42, (0.08, 0.09, 0.10), indent=8)
    lines += cube("Handle", 0.08, 0.08, 0.22, 3.85, ty - 0.84, 0.95, STEEL, indent=8)
    lines += cube("Lamp", 0.08, 0.08, 0.08, 3.85, ty - 0.84, 1.58, YELLOW, indent=8)
    lines += cube("Seam", 0.02, 0.02, 1.25, 3.15, ty - 0.80, 1.00, STEEL, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "OperatorStation"', "    {"]
    lines += cube("Desk", 1.15, 0.55, 0.08, 4.6, ty - 0.95, 0.85, HOUSING, indent=8)
    lines += cube("StoolTop", 0.34, 0.34, 0.06, 4.55, ty - 1.35, 0.52, STEEL, indent=8)
    lines += cube("StoolPost", 0.07, 0.07, 0.46, 4.55, ty - 1.35, 0.26, STEEL, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "CableTray"', "    {"]
    lines += cube("Tray", 8.5, 0.16, 0.08, 7.2, ty - 0.35, 2.38, STEEL, indent=8)
    lines += cube("DropA", 0.08, 0.08, 1.15, 3.5, ty - 0.35, 1.75, STEEL, indent=8)
    lines += cube("DropB", 0.08, 0.08, 1.15, 10.4, ty - 0.35, 1.75, STEEL, indent=8)
    lines += ["    }"]
    lines += ['    def Xform "Service"', "    {"]
    lines += cube("Walk", 10.0, 0.75, 0.05, 5.5, ty + 0.05, 0.10, CONCRETE, indent=8)
    lines += cube("Box", 0.55, 0.38, 0.42, 6.4, ty - 0.05, 0.42, STEEL, indent=8)
    lines += cube("Extinguisher", 0.12, 0.12, 0.42, 1.6, ty - 0.55, 0.55, (0.45, 0.12, 0.10), indent=8)
    lines += ["    }"]
    lines += ['    def Xform "LabelPlate"', "    {"]
    lines += cube("Plate", 1.65, 0.05, 0.46, -14.8, ty, 1.55, YELLOW, indent=8)
    lines += cube("PlateInner", 1.42, 0.04, 0.30, -14.8, ty - 0.01, 1.55, (0.12, 0.12, 0.12), indent=8)
    lines += ["    }"]
    tx = -3.55
    lines += ['    def Xform "StatusTower"', "    {"]
    lines += cube("Mount", 0.86, 0.86, 0.24, tx, ty, 0.52, STEEL, indent=8)
    lines += cube("Pole", 0.18, 0.18, 2.85, tx, ty, 1.90, STEEL, indent=8)
    lines += cube("Cable", 0.04, 0.04, 2.05, tx - 0.24, ty, 1.70, STEEL, indent=8)
    lines += cube("Housing", 0.86, 0.52, 2.62, tx, ty, 3.78, (0.035, 0.035, 0.038), indent=8)
    lines += cube("Bezel", 0.92, 0.08, 2.58, tx, ty - 0.30, 3.78, (0.02, 0.02, 0.022), indent=8)
    lines += cylinder("GreenLamp", 0.38, 0.46, tx, ty - 0.38, 2.82, LAMP_OFF, axis="Y", indent=8)
    lines += cylinder("AmberLamp", 0.38, 0.46, tx, ty - 0.38, 3.46, LAMP_OFF, axis="Y", indent=8)
    lines += cylinder("BlueLamp", 0.38, 0.46, tx, ty - 0.38, 4.10, LAMP_OFF, axis="Y", indent=8)
    lines += cylinder("RedLamp", 0.38, 0.46, tx, ty - 0.38, 4.74, LAMP_OFF, axis="Y", indent=8)
    lines += cube("Cap", 0.92, 0.58, 0.10, tx, ty, 5.16, STEEL, indent=8)
    lines += cube("ActiveLamp", 0.02, 0.02, 0.02, tx, ty - 0.38, 4.74, LAMP_OFF, purpose="proxy", indent=8)
    lines += ["    }"]
    lines += [
        '    def Xform "StatusIndicator"',
        "    {",
        '        custom string coldDrawing:role = "verdictDisplay"',
    ]
    lines += cube("proxy", 0.04, 0.04, 0.04, tx, ty, 3.78, (0.45, 0.45, 0.45), purpose="proxy", indent=8)
    lines += cube("render", 0.04, 0.04, 0.04, tx, ty, 3.78, (0.45, 0.45, 0.45), purpose="render", indent=8)
    lines += ["    }", "}"]
    lines.append("")
    return "\n".join(lines) + "\n"


def write_drawing_04(path: Path = DRAWING_04) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(drawing_04_usda(), encoding="utf-8")
    return path


def silhouette(kind: str, l: float, w: float, h: float, indent: int = 16) -> list[str]:
    """Conceptual machine body in local space, origin at footprint center, z = 0."""
    hx, hy = l / 2.0, w / 2.0
    zh = max(h, 0.8)
    parts: list[str] = []

    def add(*blocks: list[str]) -> None:
        for block in blocks:
            parts.extend(_shift(block, 0))

    pad_indent = indent
    if kind == "DrawingMachine":
        add(
            cube("Bed", l * 0.98, w * 0.72, 0.22, 0, 0, 0.11, STEEL, indent=pad_indent),
            cube("RailA", l * 0.92, 0.16, 0.14, 0, -hy * 0.45, 0.32, HOUSING, indent=pad_indent),
            cube("RailB", l * 0.92, 0.16, 0.14, 0, hy * 0.45, 0.32, HOUSING, indent=pad_indent),
            cube("Head", min(2.2, l * 0.12), w * 0.7, zh * 0.7, -hx + 1.4, 0, zh * 0.45, HOUSING, indent=pad_indent),
            cube("Carriage", min(2.4, l * 0.1), w * 0.55, zh * 0.4, hx * 0.25, 0, zh * 0.4, HOUSING, indent=pad_indent),
            cylinder("Bar", min(0.12, w * 0.08), l * 0.7, 0, 0, 0.55, WORK, indent=pad_indent),
            cube("GuardL", l * 0.45, 0.06, zh * 0.35, hx * 0.1, -hy * 0.7, zh * 0.4, GUARD, indent=pad_indent),
            cube("GuardR", l * 0.45, 0.06, zh * 0.35, hx * 0.1, hy * 0.7, zh * 0.4, GUARD, indent=pad_indent),
        )
    elif kind == "PointingMachine":
        add(
            cube("FeedBed", l * 0.95, w * 0.55, 0.14, 0, 0, 0.42, STEEL, indent=pad_indent),
            cube("Head", l * 0.32, w * 0.7, zh * 0.7, hx * 0.28, 0, 1.15, STEEL, indent=pad_indent),
            cylinder("RollA", 0.12, w * 0.5, -hx * 0.25, 0, 0.7, WORK, axis="Y", indent=pad_indent),
            cylinder("RollB", 0.12, w * 0.5, hx * 0.02, 0, 0.7, WORK, axis="Y", indent=pad_indent),
            cylinder("RollC", 0.12, w * 0.5, hx * 0.18, 0, 0.7, WORK, axis="Y", indent=pad_indent),
            cube("Guide", 0.2, w * 0.4, 0.35, -hx * 0.4, 0, 0.8, GUARD, indent=pad_indent),
            cube("DieBlock", 0.35, w * 0.35, 0.4, hx * 0.12, 0, 0.85, DIE, indent=pad_indent),
        )
    elif kind == "PilgerMill":
        add(
            cube("Base", l * 0.96, w * 0.9, 0.35, 0, 0, 0.18, STEEL, indent=pad_indent),
            cube("Housing", l * 0.28, w * 0.85, zh * 0.95, -hx * 0.15, 0, zh * 0.55, HOUSING, indent=pad_indent),
            cylinder("RollU", min(0.55, w * 0.18), w * 0.7, -hx * 0.15, 0, zh * 0.62, DIE, axis="Y", indent=pad_indent),
            cylinder("RollL", min(0.55, w * 0.18), w * 0.7, -hx * 0.15, 0, zh * 0.32, DIE, axis="Y", indent=pad_indent),
            cube("Feed", l * 0.4, w * 0.45, 0.7, hx * 0.28, 0, 0.55, HOUSING, indent=pad_indent),
            cube("FramePostA", 0.35, 0.35, zh, -hx * 0.42, -hy * 0.35, zh / 2, STEEL, indent=pad_indent),
            cube("FramePostB", 0.35, 0.35, zh, -hx * 0.42, hy * 0.35, zh / 2, STEEL, indent=pad_indent),
        )
    elif kind == "HeatTreatmentLine":
        add(
            cube("Tunnel", l * 0.96, w * 0.78, zh * 0.85, 0, 0, zh * 0.5, FURNACE, indent=pad_indent),
            cube("Insulation", l * 0.9, w * 0.86, zh * 0.12, 0, 0, zh * 0.92, CONCRETE, indent=pad_indent),
            cube("EntryHood", 0.8, w * 0.7, zh * 0.55, -hx + 0.5, 0, zh * 0.45, STEEL, indent=pad_indent),
            cube("ExitHood", 0.8, w * 0.7, zh * 0.55, hx - 0.5, 0, zh * 0.45, STEEL, indent=pad_indent),
            cube("Belt", l * 0.9, w * 0.35, 0.08, 0, 0, 0.45, (0.28, 0.28, 0.27), indent=pad_indent),
            cylinder("StackA", 0.28, zh * 0.7, -hx * 0.25, 0, zh + 0.2, STEEL, axis="Z", indent=pad_indent),
            cylinder("StackB", 0.28, zh * 0.7, hx * 0.25, 0, zh + 0.2, STEEL, axis="Z", indent=pad_indent),
        )
        for i in range(4):
            x = -hx * 0.6 + i * (l * 0.35)
            add(cube(f"Rib{i}", 0.12, w * 0.82, zh * 0.9, x, 0, zh * 0.5, STEEL, indent=pad_indent))
    elif kind == "WashingLine":
        add(
            cube("Tank", l * 0.9, w * 0.8, zh * 0.55, 0, 0, zh * 0.35, TANK, indent=pad_indent),
            cube("Canopy", l * 0.7, w * 0.6, 0.12, 0, 0, zh * 0.75, STEEL, indent=pad_indent),
            cylinder("PipeA", 0.08, w * 0.9, -hx * 0.2, 0, zh * 0.7, STEEL, axis="Y", indent=pad_indent),
            cylinder("PipeB", 0.08, w * 0.9, hx * 0.2, 0, zh * 0.7, STEEL, axis="Y", indent=pad_indent),
            cylinder("Riser", 0.07, zh * 0.5, hx * 0.15, hy * 0.2, zh * 0.55, STEEL, axis="Z", indent=pad_indent),
            cube("Pump", 0.7, 0.45, 0.45, hx * 0.35, 0, 0.45, STEEL, indent=pad_indent),
        )
    elif kind == "StraighteningLine":
        add(
            cube("Bed", l * 0.98, w * 0.7, 0.2, 0, 0, 0.12, STEEL, indent=pad_indent),
        )
        span = l * 0.78
        for i in range(7):
            x = -span / 2 + span * i / 6
            add(cylinder(f"Roll{i}", min(0.16, w * 0.11), w * 0.55, x, 0, 0.52, WORK, axis="Y", indent=pad_indent))
            add(cylinder(f"Pinch{i}", min(0.12, w * 0.08), w * 0.4, x, 0, 0.82, HOUSING, axis="Y", indent=pad_indent))
        add(cube("StandL", 0.2, w * 0.65, zh * 0.7, -hx * 0.4, 0, zh * 0.4, HOUSING, indent=pad_indent))
        add(cube("StandR", 0.2, w * 0.65, zh * 0.7, hx * 0.4, 0, zh * 0.4, HOUSING, indent=pad_indent))
    elif kind == "CuttingLine":
        add(
            cube("Table", l * 0.9, w * 0.75, 0.18, 0, 0, 0.55, HOUSING, indent=pad_indent),
            cube("Hood", l * 0.28, w * 0.7, zh * 0.7, 0, 0, zh * 0.55, STEEL, indent=pad_indent),
            cube("Outfeed", l * 0.35, w * 0.5, 0.14, hx * 0.35, 0, 0.52, HOUSING, indent=pad_indent),
            cube("BladeGuard", 0.12, w * 0.45, zh * 0.4, 0, 0, zh * 0.5, YELLOW, indent=pad_indent),
            cylinder("Saw", 0.45, 0.08, 0, 0, zh * 0.55, DIE, axis="Y", indent=pad_indent),
            cube("Clamp", 0.35, w * 0.3, 0.25, -hx * 0.15, 0, 0.85, STEEL, indent=pad_indent),
        )
    elif kind in {"PackingZone", "FinishedGoodsRack", "RawMaterialRack"}:
        add(cube("Deck", l * 0.95, w * 0.9, 0.16, 0, 0, 0.1, STEEL, indent=pad_indent))
        for i, zlev in enumerate((0.7, 1.35, 2.0)):
            add(cube(f"Shelf{i}", l * 0.9, w * 0.8, 0.08, 0, 0, min(zlev, zh * 0.9), HOUSING, indent=pad_indent))
        add(
            cube("PostA", 0.16, 0.16, zh, -hx * 0.42, -hy * 0.4, zh / 2, STEEL, indent=pad_indent),
            cube("PostB", 0.16, 0.16, zh, hx * 0.42, -hy * 0.4, zh / 2, STEEL, indent=pad_indent),
            cube("PostC", 0.16, 0.16, zh, -hx * 0.42, hy * 0.4, zh / 2, STEEL, indent=pad_indent),
            cube("PostD", 0.16, 0.16, zh, hx * 0.42, hy * 0.4, zh / 2, STEEL, indent=pad_indent),
        )
        if kind == "PackingZone":
            add(cube("Pallet", 1.2, 1.0, 0.16, hx * 0.2, 0, 0.28, YELLOW, indent=pad_indent))
    elif kind in {"DimensionInspection", "EddyCurrentInspection", "HydroTest", "VisualInspection"}:
        add(
            cube("Booth", l * 0.9, w * 0.85, zh * 0.8, 0, 0, zh * 0.45, CABINET, indent=pad_indent),
            cube("Window", 0.08, w * 0.45, zh * 0.35, hx * 0.45, 0, zh * 0.5, (0.3, 0.38, 0.42), indent=pad_indent),
            cube("Bench", l * 0.7, w * 0.4, 0.12, 0, 0, 0.7, HOUSING, indent=pad_indent),
        )
    elif kind == "OverheadCrane":
        add(
            cube("Girder", l * 0.98, w * 0.18, 0.35, 0, 0, 0, STEEL, indent=pad_indent),
            cube("Trolley", min(2.4, l * 0.08), w * 0.28, 0.4, 0, 0, -0.35, HOUSING, indent=pad_indent),
        )
    elif kind in {"HeatRecovery", "OilCirculation", "GasSystem"}:
        add(
            cube("Skid", l * 0.9, w * 0.85, 0.2, 0, 0, 0.1, STEEL, indent=pad_indent),
            cylinder("Vessel", min(w * 0.28, 0.7), zh * 0.8, 0, 0, zh * 0.5, HOUSING, axis="Z", indent=pad_indent),
            cube("Cabinet", l * 0.25, w * 0.4, zh * 0.55, hx * 0.3, 0, zh * 0.35, CABINET, indent=pad_indent),
        )
    elif kind in {"ControlElectrical", "MaintenanceZone", "UtilityZone"}:
        add(
            cube("Room", l * 0.92, w * 0.88, zh * 0.7, 0, 0, zh * 0.4, CABINET, indent=pad_indent),
            cube("Door", 0.12, w * 0.25, zh * 0.5, hx * 0.46, 0, zh * 0.35, HOUSING, indent=pad_indent),
        )
    else:
        add(cube("Body", l * 0.9, w * 0.8, zh * 0.7, 0, 0, zh * 0.4, HOUSING, indent=pad_indent))
    add(cube("Plaque", min(1.2, l * 0.18), 0.05, 0.28, -hx + 0.8, hy * 0.85, 1.35, YELLOW, indent=pad_indent))
    return parts


def facility_lines(hall_x: float, hall_y: float, grid_x: list, grid_y: list, indent: int = 8) -> list[str]:
    """Hall enclosure. South wall is a knee wall so the overview camera can look in."""
    lines: list[str] = []
    wall_h = 9.4
    ceil_z = 11.2
    lines += cube("Floor", hall_x, hall_y, 0.16, hall_x / 2, hall_y / 2, -0.08, FLOOR, purpose=None, indent=indent)
    lines += cube("ApronS", hall_x, 6.0, 0.16, hall_x / 2, -3.0, -0.08, FLOOR, purpose=None, indent=indent)
    ceil_y0 = 10.8
    ceil_span = hall_y - ceil_y0 + 1.2
    lines += cube("Ceiling", hall_x + 1.0, ceil_span, 0.22, hall_x / 2, ceil_y0 + ceil_span / 2, ceil_z, CEILING, purpose=None, indent=indent)
    for i, y in enumerate(grid_y[1:-1]):
        lines += cube(f"AisleY{i}", hall_x * 0.92, 0.42, 0.025, hall_x / 2, y, 0.012, MARK, purpose=None, indent=indent)
    lines += cube("WalkSouth", hall_x * 0.7, 0.16, 0.02, 48.0, 6.55, 0.012, MARK, purpose=None, indent=indent)
    for i, x in enumerate((16.0, 36.0, 56.0, 74.0, 86.0)):
        lines += cube(f"FlowTick{i}", 1.8, 0.22, 0.03, x, 6.55, 0.022, YELLOW, purpose=None, indent=indent)
        lines += cube(f"FlowHead{i}", 0.35, 0.45, 0.03, x + 1.05, 6.55, 0.022, YELLOW, purpose=None, indent=indent)
    cx, cy, l, w = 18 + 17.75, 7.4 + 2.75, 35.7, 5.7
    lines += cube("ZoneDraw4S", l, 0.08, 0.03, cx, cy - w / 2, 0.02, YELLOW, purpose=None, indent=indent)
    lines += cube("ZoneDraw4N", l, 0.08, 0.03, cx, cy + w / 2, 0.02, YELLOW, purpose=None, indent=indent)
    lines += cube("ZoneDraw4W", 0.08, w, 0.03, cx - l / 2, cy, 0.02, YELLOW, purpose=None, indent=indent)
    lines += cube("ZoneDraw4E", 0.08, w, 0.03, cx + l / 2, cy, 0.02, YELLOW, purpose=None, indent=indent)
    for i in range(8):
        x = 18.4 + i * 1.1
        color = YELLOW if i % 2 == 0 else DIE
        lines += cube(f"Hazard{i}", 0.9, 0.14, 0.03, x, 6.95, 0.025, color, purpose=None, indent=indent)
    n = 0
    for x in grid_x[1:-1]:
        for y in grid_y[1:-1]:
            n += 1
            lines += cube(f"Col{n}", 0.55, 0.55, wall_h, x, y, wall_h / 2, COLUMN, purpose=None, indent=indent)
            lines += cube(f"ColBase{n}", 0.95, 0.95, 0.28, x, y, 0.14, CONCRETE, purpose=None, indent=indent)
            lines += cube(f"ColCap{n}", 0.85, 0.85, 0.22, x, y, wall_h - 0.2, STEEL, purpose=None, indent=indent)
    for i, x in enumerate((16.0, 32.0, 48.0, 64.0, 80.0)):
        lines += cube(f"Truss{i}", 0.16, hall_y * 0.94, 0.22, x, hall_y / 2, ceil_z - 0.45, COLUMN, purpose=None, indent=indent)
        lines += cube(f"Purlin{i}", hall_x * 0.9, 0.10, 0.10, hall_x / 2, 8 + i * 7.0 if i < 4 else hall_y - 4, ceil_z - 0.55, COLUMN, purpose=None, indent=indent)
    lines += cube("WallS", hall_x, 0.32, 0.62, hall_x / 2, 0.16, 0.31, WALL, purpose=None, indent=indent)
    lines += cube("WallN", hall_x + 0.6, 0.55, wall_h, hall_x / 2, hall_y - 0.22, wall_h / 2, WALL, purpose=None, indent=indent)
    lines += cube("WallW", 0.55, hall_y, wall_h, 0.22, hall_y / 2, wall_h / 2, WALL, purpose=None, indent=indent)
    for i in range(6):
        lines += cube(f"WallWRib{i}", 0.18, 0.22, wall_h * 0.9, 0.45, 6 + i * 6.0, wall_h / 2, COLUMN, purpose=None, indent=indent)
    lines += cube("WallE", 0.55, hall_y, wall_h, hall_x - 0.22, hall_y / 2, wall_h / 2, WALL, purpose=None, indent=indent)
    lines += cube("BackdropN", hall_x + 12, 0.8, 16.0, hall_x / 2, hall_y + 4.0, 8.0, WALL, purpose=None, indent=indent)
    lines += cube("SignDraw", 1.8, 0.08, 0.42, 36.0, 1.15, 1.55, YELLOW, purpose=None, indent=indent)
    lines += cube("SignPilger", 1.6, 0.08, 0.42, 33.0, 13.9, 2.15, YELLOW, purpose=None, indent=indent)
    lines += cube("SignHT", 2.2, 0.08, 0.42, 32.0, 27.9, 2.15, YELLOW, purpose=None, indent=indent)
    lines += cube("SignCut", 1.4, 0.08, 0.42, 79.0, 0.9, 2.15, YELLOW, purpose=None, indent=indent)
    return lines


def _camera_block(name: str, x: float, y: float, z: float, rot: tuple[float, float, float], focal: float, clip: tuple[float, float], indent: int) -> list[str]:
    pad = " " * indent
    return [
        f'{pad}def Camera "{name}"',
        f"{pad}{{",
        f"{pad}    double3 xformOp:translate = ({x:.2f}, {y:.2f}, {z:.2f})",
        f"{pad}    float3 xformOp:rotateXYZ = ({rot[0]}, {rot[1]}, {rot[2]})",
        f'{pad}    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]',
        f"{pad}    float focalLength = {focal}",
        f"{pad}    float2 clippingRange = ({clip[0]}, {clip[1]})",
        f"{pad}}}",
    ]


def cameras_usda() -> str:
    body = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "Cameras"',
        "    metersPerUnit = 1",
        '    upAxis = "Z"',
        '    doc = "Viewport camera presets for the conceptual factory stage."',
        ")",
        "",
        'def Xform "Cameras"',
        "{",
    ]
    specs = (
        ("FactoryOverview", 78.0, -16.0, 22.0, (48, 0, 38), 18, (0.1, 400)),
        ("DrawingLine", 58.0, 3.0, 12.0, (28, 0, 18), 24, (0.1, 200)),
        ("Drawing04Hero", 49.0, 4.6, 6.4, (18, 0, 22), 26, (0.1, 80)),
        ("Drawing04Process", 36.0, 5.2, 3.4, (10, 0, 12), 32, (0.1, 60)),
        ("StatusDetail", 53.5, 5.4, 4.2, (12, 0, 28), 32, (0.05, 40)),
        ("CAM_FACTORY_OVERVIEW", 78.0, -16.0, 22.0, (48, 0, 38), 18, (0.1, 400)),
        ("CAM_DRAWING_LINE", 58.0, 3.0, 12.0, (28, 0, 18), 24, (0.1, 200)),
        ("CAM_DRAWING_04", 49.0, 4.6, 6.4, (18, 0, 22), 26, (0.1, 80)),
        ("CAM_STATUS_DETAIL", 53.5, 5.4, 4.2, (12, 0, 28), 32, (0.05, 40)),
    )
    for name, x, y, z, rot, focal, clip in specs:
        body += _camera_block(name, x, y, z, rot, focal, clip, 4)
    body += ["}", ""]
    return "\n".join(body) + "\n"


def materials_usda() -> str:
    def mat(name: str, diffuse: tuple[float, float, float], metallic: float, roughness: float, emit=None) -> list[str]:
        parts = [
            f'    def Material "{name}"',
            "    {",
            f'        token outputs:surface.connect = </Looks/{name}/Preview.outputs:surface>',
            '        def Shader "Preview"',
            "        {",
            '            uniform token info:id = "UsdPreviewSurface"',
            f"            color3f inputs:diffuseColor = {_c(diffuse)}",
            f"            float inputs:metallic = {metallic}",
            f"            float inputs:roughness = {roughness}",
        ]
        if emit:
            parts.append(f"            color3f inputs:emissiveColor = {_c(emit)}")
        parts += [
            "            token outputs:surface",
            "        }",
            "    }",
        ]
        return parts

    lines = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "Looks"',
        "    metersPerUnit = 1",
        '    upAxis = "Z"',
        '    doc = "Restrained industrial preview materials. Conceptual display only."',
        ")",
        "",
        'def Scope "Looks"',
        "{",
    ]
    for block in (
        mat("MAT_FactoryFloor", FLOOR, 0.0, 0.82),
        mat("MAT_StructuralSteel", STEEL, 0.72, 0.40),
        mat("MAT_MachineFrame", STEEL, 0.55, 0.45),
        mat("MAT_MachineHousing", HOUSING, 0.32, 0.50),
        mat("MAT_Guard", GUARD, 0.18, 0.55),
        mat("MAT_Workpiece", WORK, 0.88, 0.22),
        mat("MAT_Tooling", DIE, 0.82, 0.28),
        mat("MAT_ControlCabinet", CABINET, 0.04, 0.55),
        mat("MAT_SafetyYellow", YELLOW, 0.05, 0.45),
        mat("MAT_StatusGreen", LAMP_G, 0.1, 0.35, emit=(0.05, 0.35, 0.08)),
        mat("MAT_StatusAmber", LAMP_A, 0.1, 0.35, emit=(0.35, 0.22, 0.04)),
        mat("MAT_StatusBlue", LAMP_B, 0.1, 0.35, emit=(0.06, 0.14, 0.40)),
        mat("MAT_StatusRed", LAMP_R, 0.1, 0.35, emit=(0.40, 0.06, 0.06)),
        mat("MAT_StatusOffline", LAMP_OFF, 0.05, 0.7),
        mat("Concrete", FLOOR, 0.0, 0.78),
        mat("Steel", STEEL, 0.65, 0.42),
        mat("Housing", HOUSING, 0.35, 0.5),
        mat("Guard", GUARD, 0.2, 0.55),
        mat("Workpiece", WORK, 0.85, 0.28),
        mat("Die", DIE, 0.8, 0.32),
        mat("Cabinet", CABINET, 0.05, 0.55),
        mat("SafetyYellow", YELLOW, 0.05, 0.45),
    ):
        lines.extend(block)
    lines += ["}", ""]
    return "\n".join(line for line in lines if line is not None) + "\n"


def lights_and_cameras(hall_x: float, hall_y: float, indent: int = 8) -> list[str]:
    pad = " " * indent
    lines = [
        f'{pad}def DomeLight "Env"',
        f"{pad}{{",
        f"{pad}    float intensity = 3200",
        f"{pad}    color3f color = (0.84, 0.86, 0.88)",
        f"{pad}}}",
        f'{pad}def DistantLight "Key"',
        f"{pad}{{",
        f"{pad}    float intensity = 7400",
        f"{pad}    color3f color = (1.0, 0.97, 0.92)",
        f"{pad}    float3 xformOp:rotateXYZ = (-38, 42, 0)",
        f'{pad}    uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]',
        f"{pad}}}",
        f'{pad}def DistantLight "Fill"',
        f"{pad}{{",
        f"{pad}    float intensity = 2100",
        f"{pad}    color3f color = (0.82, 0.86, 0.90)",
        f"{pad}    float3 xformOp:rotateXYZ = (22, -52, 0)",
        f'{pad}    uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]',
        f"{pad}}}",
        f'{pad}def DistantLight "Rim"',
        f"{pad}{{",
        f"{pad}    float intensity = 900",
        f"{pad}    color3f color = (0.75, 0.78, 0.82)",
        f"{pad}    float3 xformOp:rotateXYZ = (8, 160, 0)",
        f'{pad}    uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]',
        f"{pad}}}",
        f'{pad}def Xform "Cameras"',
        f"{pad}{{",
    ]
    nested = indent + 4
    specs = (
        ("FactoryOverview", 78.0, -16.0, 22.0, (48, 0, 38), 18, (0.1, 400)),
        ("DrawingLine", 58.0, 3.0, 12.0, (28, 0, 18), 24, (0.1, 200)),
        ("Drawing04Hero", 49.0, 4.6, 6.4, (18, 0, 22), 26, (0.1, 80)),
        ("Drawing04Process", 36.0, 5.2, 3.4, (10, 0, 12), 32, (0.1, 60)),
        ("StatusDetail", 53.5, 5.4, 4.2, (12, 0, 28), 32, (0.05, 40)),
        ("CAM_FACTORY_OVERVIEW", 78.0, -16.0, 22.0, (48, 0, 38), 18, (0.1, 400)),
        ("CAM_DRAWING_LINE", 58.0, 3.0, 12.0, (28, 0, 18), 24, (0.1, 200)),
        ("CAM_DRAWING_04", 49.0, 4.6, 6.4, (18, 0, 22), 26, (0.1, 80)),
        ("CAM_STATUS_DETAIL", 53.5, 5.4, 4.2, (12, 0, 28), 32, (0.05, 40)),
    )
    for name, x, y, z, rot, focal, clip in specs:
        lines += _camera_block(name, x, y, z, rot, focal, clip, nested)
    lines += [f"{pad}}}"]
    n = 0
    for x in (12, 28, 44, 60, 76, 88):
        for y in (6, 18, 30):
            n += 1
            lines += cube(f"BayLight{n}", 3.8, 0.55, 0.14, x, y, 10.55, (0.98, 0.97, 0.86), purpose=None, indent=indent)
    return lines


def machine_usda(prim_name: str, kind: str, length: float, width: float, height: float, asset_id: str) -> str:
    lines = [
        "#usda 1.0",
        "(",
        f'    defaultPrim = "{prim_name}"',
        "    metersPerUnit = 1",
        '    upAxis = "Z"',
        '    doc = "Conceptual OpenUSD industrial equipment representation. Not mill CAD."',
        ")",
        "",
        f'def Xform "{prim_name}"',
        "{",
        f'    custom string coldDrawing:assetId = "{asset_id}"',
    ]
    lines += silhouette(kind, length, width, height, indent=4)
    lines += ["}", ""]
    return "\n".join(lines) + "\n"


def write_machine_asset(prim_name: str, kind: str, length: float, width: float, height: float, asset_id: str) -> Path:
    folder = CLASS_FOLDER.get(kind, "machines")
    path = REPO_ROOT / "usd" / "assets" / folder / f"{prim_name}.usda"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(machine_usda(prim_name, kind, length, width, height, asset_id), encoding="utf-8")
    return path


def write_shared_assets() -> None:
    MATERIALS.parent.mkdir(parents=True, exist_ok=True)
    CAMERAS.parent.mkdir(parents=True, exist_ok=True)
    MATERIALS.write_text(materials_usda(), encoding="utf-8")
    CAMERAS.write_text(cameras_usda(), encoding="utf-8")
