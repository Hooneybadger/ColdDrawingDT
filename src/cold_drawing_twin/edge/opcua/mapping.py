from __future__ import annotations

from cold_drawing_twin.config_files import opcua_map


def nodes_for(asset_id: str) -> dict[str, str]:
    mapping = opcua_map()
    assets = mapping["assets"]
    if asset_id not in assets:
        raise KeyError(asset_id)
    return dict(assets[asset_id])
