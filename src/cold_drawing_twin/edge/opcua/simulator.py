from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from asyncua import Server, ua

from cold_drawing_twin.config_files import opcua_map
from cold_drawing_twin.domain.features import ProcessFeatures


async def serve_drawing4(features: ProcessFeatures, endpoint: str | None = None) -> Server:
    mapping = opcua_map()
    server = Server()
    await server.init()
    server.set_endpoint(endpoint or mapping["endpoint"])
    uri = mapping["namespace_uri"]
    idx = await server.register_namespace(uri)
    objects = server.nodes.objects
    machine = await objects.add_object(idx, "DRW04")
    now = datetime.now(timezone.utc)
    for name, value in (
        ("reduction_ratio", features.reduction_ratio),
        ("die_half_angle_rad", features.die_half_angle_rad),
        ("friction_coefficient", features.friction_coefficient),
        ("normalized_hardening_coefficient", features.normalized_hardening_coefficient),
        ("pass_index", 1),
        ("source_timestamp", now.isoformat()),
        ("quality", "GOOD"),
    ):
        node = await machine.add_variable(ua.NodeId(f"DRW04.{name}", idx), name, value)
        await node.set_writable()
        await node.write_value(value)
    return server


def main() -> None:
    features = ProcessFeatures(0.3, 0.2, 0.08, 0.7)

    async def _run() -> None:
        server = await serve_drawing4(features)
        async with server:
            while True:
                await asyncio.sleep(1)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
