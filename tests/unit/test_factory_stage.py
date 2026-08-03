from pathlib import Path

from cold_drawing_twin.paths import REPO_ROOT
from omniverse.scripts.generate_factory_stage import generate


def test_factory_stage_contains_drawing4(tmp_path: Path):
    path = generate(tmp_path / "bugok_factory.usda")
    text = path.read_text(encoding="utf-8")
    assert 'def Xform "World"' in text
    assert "BG.MIEUM.DRW.04" in text
    assert "Drawing_04.usda" in text
    hero = (REPO_ROOT / "usd" / "assets" / "drawing" / "Drawing_04.usda").read_text(encoding="utf-8")
    for name in ("Frame", "Die", "Workpiece", "Entry", "Exit", "StatusIndicator"):
        assert f'"{name}"' in hero
    assert 'purpose = "proxy"' in hero
    assert 'purpose = "render"' in hero
