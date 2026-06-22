from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone

from asyncua import Client

from cold_drawing_twin.config_files import opcua_map
from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.edge.opcua.mapping import nodes_for
from cold_drawing_twin.orchestration.container import build_container

LOGGER = logging.getLogger("edge.opcua")
PRIMARY = "BG.MIEUM.DRW.04"


async def poll_once(endpoint: str) -> ProcessFeatures:
    nodes = nodes_for(PRIMARY)
    async with Client(url=endpoint) as client:
        reduction = await (await client.nodes.root.get_child(["0:Objects", "2:DRW04", "2:reduction_ratio"])).read_value()
        angle = await (await client.nodes.root.get_child(["0:Objects", "2:DRW04", "2:die_half_angle_rad"])).read_value()
        friction = await (await client.nodes.root.get_child(["0:Objects", "2:DRW04", "2:friction_coefficient"])).read_value()
        hardening = await (
            await client.nodes.root.get_child(["0:Objects", "2:DRW04", "2:normalized_hardening_coefficient"])
        ).read_value()
    return ProcessFeatures(float(reduction), float(angle), float(friction), float(hardening))


def write_twin(features: ProcessFeatures) -> None:
    container = build_container()
    session = container.open()
    twin, _events, _evaluation = container.services(session)
    twin.put_process_state(PRIMARY, features, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    session.commit()
    session.close()


async def loop(endpoint: str, interval_s: float) -> None:
    delay = interval_s
    while True:
        try:
            features = await poll_once(endpoint)
            write_twin(features)
            LOGGER.info("updated Digital Twin from OPC UA")
            delay = interval_s
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("OPC UA poll failed: %s", exc)
            delay = min(delay * 2, 60)
        await asyncio.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(description="OPC UA edge adapter")
    parser.add_argument("--endpoint", default=opcua_map()["endpoint"])
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(loop(args.endpoint, args.interval))


if __name__ == "__main__":
    main()
