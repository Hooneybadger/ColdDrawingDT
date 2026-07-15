from pathlib import Path

from omniverse.scripts.generate_factory_stage import generate


def test_factory_stage_contains_drawing4(tmp_path: Path):
    path = generate(tmp_path / "bugok_factory.usda")
    text = path.read_text(encoding="utf-8")
    assert "/World" in text or 'def Xform "World"' in text
    assert "BG.MIEUM.DRW.04" in text
    assert "Drawing_04" in text
