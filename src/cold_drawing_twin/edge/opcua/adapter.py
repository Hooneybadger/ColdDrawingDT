from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone

from asyncua import Client, ua

from cold_drawing_twin.config_files import opcua_map
from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.edge.opcua.mapping import ProcessReading, coerce_timestamp, nodes_for, quality_from_status
from cold_drawing_twin.orchestration.container import AppContainer, build_container
from cold_drawing_twin.settings import load_settings

LOGGER = logging.getLogger("edge.opcua")
PRIMARY = "BG.MIEUM.DRW.04"
FEATURE_NODES = (
    "reduction_ratio",
    "die_half_angle_rad",
    "friction_coefficient",
    "normalized_hardening_coefficient",
)


async def read_datavalue(client: Client, node_id: str) -> ua.DataValue:
    node = client.get_node(node_id)
    return await node.read_data_value()


async def read_process(client: Client, asset_id: str = PRIMARY) -> ProcessReading:
    nodes = nodes_for(asset_id)
    values: dict[str, ua.DataValue] = {}
    for name in FEATURE_NODES:
        values[name] = await read_datavalue(client, nodes[name])
    pass_index = None
    if nodes.get("pass_index"):
        pass_dv = await read_datavalue(client, nodes["pass_index"])
        if pass_dv.Value is not None and pass_dv.Value.Value is not None:
            pass_index = int(pass_dv.Value.Value)
    statuses = [item.StatusCode for item in values.values()]
    qualities = [quality_from_status(status) for status in statuses]
    if "BAD" in qualities:
        quality = "BAD"
    elif "UNCERTAIN" in qualities:
        quality = "UNCERTAIN"
    else:
        quality = "GOOD"
    source_candidates = [coerce_timestamp(item.SourceTimestamp) for item in values.values()]
    source_timestamp = max((item for item in source_candidates if item is not None), default=None)
    server_candidates = [coerce_timestamp(item.ServerTimestamp) for item in values.values()]
    server_timestamp = max((item for item in server_candidates if item is not None), default=None)
    missing = source_timestamp is None
    if missing and quality == "GOOD":
        quality = "UNCERTAIN"
    status_text = ",".join(str(status) for status in statuses)
    return ProcessReading(
        reduction_ratio=float(values["reduction_ratio"].Value.Value),
        die_half_angle_rad=float(values["die_half_angle_rad"].Value.Value),
        friction_coefficient=float(values["friction_coefficient"].Value.Value),
        normalized_hardening_coefficient=float(values["normalized_hardening_coefficient"].Value.Value),
        pass_index=pass_index,
        source_timestamp=source_timestamp,
        server_timestamp=server_timestamp,
        quality=quality,
        source_timestamp_missing=missing,
        status_code=status_text,
    )


def write_twin(container: AppContainer, reading: ProcessReading, asset_id: str = PRIMARY) -> None:
    features = ProcessFeatures(
        reading.reduction_ratio,
        reading.die_half_angle_rad,
        reading.friction_coefficient,
        reading.normalized_hardening_coefficient,
    )
    source_timestamp = reading.source_timestamp or datetime.now(timezone.utc)
    session = container.open()
    try:
        twin, _events, _evaluation = container.services(session)
        twin.put_process_state(
            asset_id,
            features,
            source_timestamp=source_timestamp,
            quality=reading.quality,
            pass_index=reading.pass_index,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def loop(endpoint: str, interval_s: float, container: AppContainer | None = None) -> None:
    container = container or build_container()
    delay = interval_s
    while True:
        try:
            async with Client(url=endpoint) as client:
                delay = interval_s
                while True:
                    reading = await read_process(client)
                    write_twin(container, reading)
                    LOGGER.info(
                        "updated Digital Twin from OPC UA quality=%s source_timestamp=%s missing=%s",
                        reading.quality,
                        reading.source_timestamp,
                        reading.source_timestamp_missing,
                    )
                    await asyncio.sleep(interval_s)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("OPC UA poll failed: %s", exc)
            delay = min(delay * 2, 60)
            await asyncio.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(description="OPC UA edge adapter")
    parser.add_argument("--endpoint", default=None)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    settings = load_settings()
    endpoint = args.endpoint or settings.opcua_endpoint or opcua_map()["endpoint"]
    logging.basicConfig(level=logging.INFO)
    container = build_container(settings)
    LOGGER.info("edge adapter started; AppContainer lives for the process")
    asyncio.run(loop(endpoint, args.interval, container))


if __name__ == "__main__":
    main()
