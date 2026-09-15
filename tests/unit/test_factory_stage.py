from pathlib import Path

from cold_drawing_twin.config_files import asset_registry
from cold_drawing_twin.paths import REPO_ROOT
from omniverse.scripts.generate_factory_stage import generate


def test_factory_stage_contains_drawing4(tmp_path: Path):
    path = generate(tmp_path / "bugok_factory.usda")
    text = path.read_text(encoding="utf-8")
    assert 'def Xform "World"' in text
    assert "BG.MIEUM.DRW.04" in text
    assert "Drawing_04.usda" in text
    assert 'def Xform "Facility"' in text
    assert "MainFactory" not in text
    assert 'def Camera "FactoryOverview"' in text
    assert 'def Camera "DrawingLine"' in text
    assert 'def Camera "Drawing04Hero"' in text
    assert 'def Camera "Drawing04Process"' in text
    assert 'def Camera "StatusDetail"' in text
    assert 'def Camera "CAM_FACTORY_OVERVIEW"' in text
    assert 'def Camera "CAM_DRAWING_LINE"' in text
    assert 'def Camera "CAM_DRAWING_04"' in text
    assert 'def Camera "CAM_STATUS_DETAIL"' in text
    assert 'def DomeLight "Env"' in text
    assert 'def Xform "Ceiling"' in text or 'def Cube "Ceiling"' in text
    hero = (REPO_ROOT / "usd" / "assets" / "drawing" / "Drawing_04.usda").read_text(encoding="utf-8")
    for name in (
        "Frame",
        "Die",
        "Workpiece",
        "Entry",
        "Exit",
        "StatusIndicator",
        "StatusTower",
        "DieHousing",
        "GreenLamp",
        "AmberLamp",
        "BlueLamp",
        "RedLamp",
        "PullingSection",
        "CarriageGuideRails",
        "ControlCabinet",
        "OperatorStation",
        "CableTray",
        "Service",
        "DieSupport",
        "Guarding",
        "AccessGate",
        "LabelPlate",
    ):
        assert f'"{name}"' in hero
    assert "AccessGate" in hero
    assert "GripHousing" in hero
    assert "Workpiece_Input" in hero
    assert "Workpiece_Output" in hero
    assert "PullingSection" in hero
    assert 'purpose = "proxy"' in hero
    assert 'purpose = "render"' in hero
    assert "conceptual" in hero.lower() or "Conceptual" in hero
    cameras = (REPO_ROOT / "usd" / "cameras" / "stage_cameras.usda").read_text(encoding="utf-8")
    assert "FactoryOverview" in cameras
    assert "Drawing04Hero" in cameras
    assert "Drawing04Process" in cameras
    assert "StatusDetail" in cameras
    materials = (REPO_ROOT / "usd" / "materials" / "industrial_materials.usda").read_text(encoding="utf-8")
    assert "UsdPreviewSurface" in materials
    assert "MAT_FactoryFloor" in materials
    assert "MAT_Workpiece" in materials
    assert "MAT_StatusGreen" in materials
    registry = asset_registry()
    for item in registry.values():
        leaf = item["usd_prim"].rsplit("/", 1)[1]
        assert leaf in text
    assert (REPO_ROOT / "usd" / "assets" / "pilger" / "Pilger_01.usda").is_file()
    assert (REPO_ROOT / "usd" / "assets" / "pointing" / "Pointing_01.usda").is_file()
    assert "StatusIndicator" in hero
