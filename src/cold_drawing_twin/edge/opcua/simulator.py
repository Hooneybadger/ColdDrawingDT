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
    await machine.add_variable(ua.NodeId("DRW04.reduction_ratio", idx), "reduction_ratio", features.reduction_ratio)
    await machine.add_variable(ua.NodeId("DRW04.die_half_angle_rad", idx), "die_half_angle_rad", features.die_half_angle_rad)
    await machine.add_variable(
        ua.NodeId("DRW04.friction_coefficient", idx), "friction_coefficient", features.friction_coefficient
    )
    await machine.add_variable(
        ua.NodeId("DRW04.normalized_hardening_coefficient", idx),
        "normalized_hardening_coefficient",
        features.normalized_hardening_coefficient,
    )
    await machine.add_variable(ua.NodeId("DRW04.pass_index", idx), "pass_index", 1)
    await machine.add_variable(
        ua.NodeId("DRW04.source_timestamp", idx),
        "source_timestamp",
        datetime.now(timezone.utc).isoformat(),
    )
    await machine.add_variable(ua.NodeId("DRW04.quality", idx), "quality", "GOOD")
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
