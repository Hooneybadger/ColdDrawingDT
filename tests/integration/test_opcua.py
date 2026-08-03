import pytest
from asyncua import Client

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.edge.opcua.adapter import read_process, write_twin
from cold_drawing_twin.edge.opcua.simulator import serve_drawing4
from cold_drawing_twin.orchestration.container import build_container
from tests.conftest import DEMO, PRIMARY


@pytest.mark.asyncio
async def test_simulator_to_twin_preserves_source_metadata(settings):
    endpoint = "opc.tcp://127.0.0.1:4851/cold-drawing/"
    container = build_container(settings=settings)
    server = await serve_drawing4(DEMO, endpoint)
    async with server:
        async with Client(url=endpoint) as client:
            reading = await read_process(client)
    assert reading.quality == "GOOD"
    assert reading.source_timestamp_missing is False
    assert reading.source_timestamp is not None
    write_twin(container, reading)
    session = container.open()
    twin, _events, _evaluation = container.services(session)
    row = twin.require(PRIMARY)
    assert row.features["reduction_ratio"] == pytest.approx(0.3)
    assert row.quality == "GOOD"
    assert row.source_timestamp is not None
    assert row.state_version
    from cold_drawing_twin.history.store import history_for

    points = history_for(session, PRIMARY)
    assert points
    assert {item["field"] for item in points} >= set(ProcessFeatures(0.3, 0.2, 0.08, 0.7).as_dict())
    session.close()
