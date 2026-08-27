from __future__ import annotations

import logging
from typing import Any

from cold_drawing_twin.display import apply_status_attributes, status_indicator_prim

LOGGER = logging.getLogger(__name__)


def status_binding(usd_prim: str, view: dict[str, Any]) -> dict[str, Any]:
    """Pure mapping from a display view to USD attribute updates."""
    indicator_path = status_indicator_prim(usd_prim) if usd_prim else ""
    return {
        "asset_prim": usd_prim,
        "indicator_prim": indicator_path,
        "color": view.get("color") or (0.45, 0.45, 0.45),
        "attributes": apply_status_attributes({}, view),
    }


def _set_string(prim, name: str, value: str) -> None:
    from pxr import Sdf

    attr = prim.GetAttribute(name)
    if not attr:
        attr = prim.CreateAttribute(name, Sdf.ValueTypeNames.String)
    attr.Set("" if value is None else str(value))


def _set_display_color(prim, color: tuple[float, float, float]) -> None:
    from pxr import Gf, UsdGeom, Vt

    if not prim or not prim.IsValid():
        return
    gprim = UsdGeom.Gprim(prim)
    if not gprim:
        return
    attr = gprim.GetDisplayColorAttr()
    if not attr:
        attr = gprim.CreateDisplayColorAttr()
    attr.Set(Vt.Vec3fArray([Gf.Vec3f(*color)]))


def apply_status_to_stage(stage, usd_prim: str, view: dict[str, Any]) -> bool:
    """Write display attributes onto the live USD stage. No-op without pxr or a prim."""
    if stage is None or not usd_prim:
        return False
    try:
        from pxr import Usd
    except ImportError:
        LOGGER.debug("pxr is not available; USD status bind skipped")
        return False
    binding = status_binding(usd_prim, view)
    asset = stage.GetPrimAtPath(binding["asset_prim"])
    if not asset or not asset.IsValid():
        return False
    for name, value in binding["attributes"].items():
        _set_string(asset, name, value)
    indicator = stage.GetPrimAtPath(binding["indicator_prim"])
    if indicator and indicator.IsValid():
        for name, value in binding["attributes"].items():
            _set_string(indicator, name, value)
        color = binding["color"]
        _set_display_color(indicator.GetChild("proxy"), color)
        _set_display_color(indicator.GetChild("render"), color)
    return True


def current_kit_stage():
    try:
        import omni.usd
    except ImportError:
        return None
    try:
        return omni.usd.get_context().get_stage()
    except Exception:
        return None
