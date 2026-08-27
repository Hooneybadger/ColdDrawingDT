from datetime import datetime, timezone

from fastapi.testclient import TestClient

from cold_drawing_twin.api.app import create_app
from cold_drawing_twin.domain.features import ProcessFeatures
from tests.conftest import DEMO, PRIMARY, make_pinn
from cold_drawing_twin.orchestration.container import build_container


def test_http_contracts(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, _evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD", state_version="state-0001"
    )
    session.commit()
    client = TestClient(create_app(container))
    asset = client.get(f"/assets/{PRIMARY}").json()
    assert asset["aas_id"] == "urn:bg:mieum:drw:04"
    assert asset["usd_prim"].endswith("Drawing_04")
    state = client.get(f"/assets/{PRIMARY}/state").json()
    assert state["features"]["reduction_ratio"] == 0.3
    assets = client.get("/assets").json()
    assert any(item["asset_id"] == PRIMARY for item in assets["assets"])
    posted = client.post(
        f"/assets/{PRIMARY}/evaluations",
        json={"mode": "OPERATIONAL", "expected_state_version": "state-0001"},
    )
    assert posted.status_code == 200
    body = posted.json()
    assert body["snapshot"]["features"]["reduction_ratio"] == 0.3
    decision = client.get(f"/decisions/{body['decision_id']}").json()
    assert decision["verdict"] == "SAFE"
    assert decision["routing_policy_version"] == "routing-v1"
    state = client.get(f"/assets/{PRIMARY}/state").json()
    assert state["latest_decision_id"] == body["decision_id"]
    live = client.get(f"/assets/{PRIMARY}/live").json()
    assert live["backend_status"] == "ONLINE"
    assert live["decision"]["decision_id"] == body["decision_id"]
    assert live["decision"]["latest_verdict"] == "SAFE"
    assert live["decision"]["evaluation_id"] == body["evaluation_id"]
    assert live["decision"]["snapshot_id"] == body["snapshot"]["snapshot_id"]
    assert live["usd_prim"].endswith("Drawing_04")
    history = client.get(f"/assets/{PRIMARY}/history").json()
    assert history["points"]
    inspector = client.get("/aas-inspector")
    assert inspector.status_code == 200
    assert "Read-only AAS / BaSyx view" in inspector.text
    assert "/aas/" in inspector.text
    assert "/assets/" not in inspector.text
    aas = client.get(f"/aas/{PRIMARY}/view").json()
    assert aas["asset_id"] == PRIMARY
    assert aas["basyx_status"] == "OFFLINE"
    assert aas["process"] is None
    assert aas["evaluation"] is None
