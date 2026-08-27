from cold_drawing_twin.display import NEUTRAL_INDICATOR, panel_model
from cold_drawing_twin.kit_runtime import LiveViewController
from cold_drawing_twin.usd_status import apply_status_to_stage, status_binding
from tests.conftest import PRIMARY


class FakeLiveClient:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error

    def fetch_live(self):
        if self.error:
            raise self.error
        return self.payload


def test_status_binding_safe_is_green():
    model = panel_model(
        {
            "usd_prim": "/World/BugokFactory/Production/Drawing/Drawing_04",
            "decision": {"latest_verdict": "SAFE", "decision_id": "dec-1"},
        }
    )
    bound = status_binding(model["usd_prim"], model)
    assert bound["indicator_prim"].endswith("StatusIndicator")
    assert bound["attributes"]["coldDrawing:verdict"] == "SAFE"
    assert bound["attributes"]["coldDrawing:indicator"] == "green"
    assert bound["color"][1] > bound["color"][0]


def test_status_binding_offline_is_neutral_gray():
    model = panel_model({"decision": {"latest_verdict": "SAFE"}}, backend_online=False)
    bound = status_binding("/World/BugokFactory/Production/Drawing/Drawing_04", model)
    assert bound["attributes"]["coldDrawing:verdict"] == ""
    assert bound["attributes"]["coldDrawing:indicator"] == NEUTRAL_INDICATOR
    assert bound["attributes"]["coldDrawing:backendStatus"] == "OFFLINE"


def test_live_controller_uses_backend_ids():
    client = FakeLiveClient(
        {
            "asset_id": PRIMARY,
            "usd_prim": "/World/BugokFactory/Production/Drawing/Drawing_04",
            "process": {
                "features": {"reduction_ratio": 0.3},
                "state_version": "state-1",
                "source_timestamp": "2026-08-01T00:00:00Z",
                "quality": "GOOD",
            },
            "decision": {
                "latest_verdict": "SAFE",
                "evaluation_id": "eval-1",
                "snapshot_id": "snap-1",
                "decision_id": "dec-1",
                "routing_action": "ACCEPT",
                "model_version": "v0.1.1",
            },
            "fea": {"status": "IDLE"},
        }
    )
    controller = LiveViewController(client, PRIMARY, "test")
    model = controller.tick()
    assert model["decision_id"] == "dec-1"
    assert model["latest_verdict"] == "SAFE"
    assert model["backend_status"] == "ONLINE"
    assert controller.panel is None


def test_live_controller_offline_does_not_invent_verdict():
    controller = LiveViewController(FakeLiveClient(error=ConnectionError("down")), PRIMARY, "test")
    model = controller.tick()
    assert model["backend_status"] == "OFFLINE"
    assert model["latest_verdict"] is None
    assert model["indicator"] == NEUTRAL_INDICATOR
    again = controller.tick()
    assert again["backend_status"] == "OFFLINE"


def test_apply_status_to_stage_when_pxr_available():
    pxr = pytest_import_pxr()
    if pxr is None:
        assert apply_status_to_stage(None, "/World/X", panel_model({}, backend_online=False)) is False
        return
    Usd, UsdGeom = pxr
    stage = Usd.Stage.CreateInMemory()
    asset_path = "/World/BugokFactory/Production/Drawing/Drawing_04"
    stage.DefinePrim(asset_path, "Xform")
    indicator = stage.DefinePrim(asset_path + "/StatusIndicator", "Xform")
    UsdGeom.Sphere.Define(stage, indicator.GetPath().AppendChild("proxy"))
    UsdGeom.Sphere.Define(stage, indicator.GetPath().AppendChild("render"))
    model = panel_model(
        {
            "usd_prim": asset_path,
            "decision": {"latest_verdict": "UNSAFE"},
        }
    )
    assert apply_status_to_stage(stage, asset_path, model) is True
    prim = stage.GetPrimAtPath(asset_path)
    assert prim.GetAttribute("coldDrawing:verdict").Get() == "UNSAFE"
    assert prim.GetAttribute("coldDrawing:indicator").Get() == "red"


def pytest_import_pxr():
    try:
        from pxr import Usd, UsdGeom

        return Usd, UsdGeom
    except ImportError:
        return None
