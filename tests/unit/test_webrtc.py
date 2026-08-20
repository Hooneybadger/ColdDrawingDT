from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi.testclient import TestClient

from cold_drawing_twin.api.app import create_app
from cold_drawing_twin.orchestration.container import build_container
from tests.conftest import PRIMARY, make_pinn


def test_operator_page_is_display_only(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    client = TestClient(create_app(container))
    page = client.get("/operator")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "does not write Decisions" in page.text


async def test_webrtc_offer_returns_answer(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    client = TestClient(create_app(container))
    pc = RTCPeerConnection()
    pc.createDataChannel("operator")
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    response = client.post(
        "/stream/webrtc/offer",
        json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type, "asset_id": PRIMARY},
    )
    await pc.close()
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "answer"
    assert "sdp" in body
    assert body["sdp"]
