"""Kit capture helper. Copy onto the RTX host and run with the Twin API reachable."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "yes")

ROOT = Path(os.environ.get("KIT_CAPTURE_ROOT", r"C:\Users\IDB\kit-capture"))
STAGE = ROOT / "usd" / "factory" / "bugok_factory.usda"
OUT = Path(os.environ.get("KIT_CAPTURE_DIR", str(ROOT / "out")))
EXT_FOLDER = ROOT / "extensions"
sys.path.insert(0, str(ROOT / "src"))

from omni.kit_app import KitApp  # noqa: E402

app = KitApp()
print("kit startup", flush=True)
app.startup(
    [
        "--enable",
        "omni.kit.loop-default",
        "--enable",
        "omni.kit.uiapp",
        "--enable",
        "omni.usd",
        "--enable",
        "omni.ui",
        "--enable",
        "omni.kit.viewport.window",
        "--enable",
        "omni.kit.viewport.utility",
        "--enable",
        "omni.hydra.pxr",
        "--enable",
        "omni.kit.renderer.core",
        "--ext-folder",
        str(EXT_FOLDER),
        "--enable",
        "omni.cold_drawing.operator",
        "--/app/window/width=1920",
        "--/app/window/height=1080",
        "--/app/window/title=Cold Drawing Operator Kit",
        "--/log/outputStdout=1",
    ]
)


def pump(n: int = 30) -> None:
    for _ in range(n):
        if not app.is_running():
            break
        app.update()


import omni.kit.app as kit_app  # noqa: E402
import omni.usd  # noqa: E402
from cold_drawing_twin.kit_runtime import LiveViewController, apply_kit_viewport  # noqa: E402
from omni.cold_drawing.operator.client import OperatorClient  # noqa: E402
from omni.kit.viewport.utility import (  # noqa: E402
    capture_viewport_to_file,
    frame_viewport_prims,
    get_active_viewport,
)
from pxr import Gf, UsdGeom  # noqa: E402

OUT.mkdir(parents=True, exist_ok=True)
apply_kit_viewport()
print("open stage", STAGE, flush=True)
ctx = omni.usd.get_context()
print("open_stage", ctx.open_stage(str(STAGE)), flush=True)
pump(80)
stage = ctx.get_stage()
print("stage", stage, flush=True)

client = OperatorClient(os.environ.get("TWIN_API", "http://127.0.0.1:8000"))
view = LiveViewController(client, client.asset_id, "Cold Drawing Operator")
model = view.tick()
print(
    "bound",
    model.get("decision_id"),
    model.get("headline"),
    model.get("fea_headline"),
    model.get("indicator"),
    flush=True,
)
pump(20)
vp = get_active_viewport()
print("viewport", vp, "camera", getattr(vp, "camera_path", None), flush=True)

CAMERAS = {
    "factory": "/World/Cameras/FactoryOverview",
    "line": "/World/Cameras/DrawingLine",
    "hero": "/World/Cameras/Drawing04Hero",
    "process": "/World/Cameras/Drawing04Process",
    "status": "/World/Cameras/StatusDetail",
}
FRAMES = {
    "factory": "/World/BugokFactory",
    "line": "/World/BugokFactory/Production/Drawing",
    "hero": "/World/BugokFactory/Production/Drawing/Drawing_04",
    "status": "/World/BugokFactory/Production/Drawing/Drawing_04/StatusIndicator",
}


LOOK = {
    "factory": ((22.0, -12.5, 6.35), (50.0, 16.5, 0.85)),
    "line": ((62.0, 1.5, 14.0), (40.0, 14.0, 1.1)),
    "hero": ((23.2, 4.15, 4.55), (36.8, 10.05, 1.12)),
    "hero_panel": ((23.6, 2.75, 3.85), (34.9, 9.15, 1.48)),
    "process": ((30.4, 6.05, 2.28), (34.8, 10.15, 1.08)),
    "status": ((34.8, 3.15, 4.35), (32.20, 8.00, 3.70)),
}
FOCAL = {"factory": 30.0, "line": 24.0, "hero": 26.0, "hero_panel": 24.0, "process": 32.0, "status": 32.0}


def force_landscape_window(width: int = 1920, height: int = 1080) -> None:
    try:
        import win32con
        import win32gui
        import win32api
    except Exception as exc:
        print("win32 resize unavailable", exc, flush=True)
        return
    found: list[int] = []

    def _enum(hwnd, _acc):
        title = win32gui.GetWindowText(hwnd)
        if title.startswith("Cold Drawing Operator Kit") and win32gui.IsWindowVisible(hwnd):
            found.append(hwnd)

    win32gui.EnumWindows(_enum, None)
    print("kit hwnd candidates", [(hwnd, win32gui.GetWindowRect(hwnd)) for hwnd in found], flush=True)
    if not found:
        print("no kit hwnd to resize", flush=True)
        return
    hwnd = found[0]
    best_area = 0
    for candidate in found:
        l, t, r, b = win32gui.GetWindowRect(candidate)
        area = max(0, r - l) * max(0, b - t)
        if area >= best_area:
            best_area = area
            hwnd = candidate
    tries = [(80, 60), (0, 0), (1920, 0), (3840, 0), (6000, 0), (-1920, 0), (2160, 100), (4000, 80)]
    try:
        for _handle, _hdc, rect in win32api.EnumDisplayMonitors():
            l, t, r, b = rect
            w, h = r - l, b - t
            print("monitor", l, t, r, b, "size", w, h, flush=True)
            tries.append((l + 40, t + 40))
    except Exception as exc:
        print("monitor enum failed", exc, flush=True)
    best_w = 0
    best_origin = tries[0]
    for left, top in tries:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, int(left), int(top), width, height, win32con.SWP_SHOWWINDOW)
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        print("try origin", left, top, "got", r - l, "x", b - t, flush=True)
        if r - l >= best_w:
            best_w = r - l
            best_origin = (left, top)
            if r - l >= 1600:
                break
    left, top = best_origin
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, int(left), int(top), width, height, win32con.SWP_SHOWWINDOW)
    print("resized kit window", width, height, "origin", left, top, "final_w", best_w, flush=True)


force_landscape_window()
pump(25)


def author_look_at(eye, target, *, focal: float = 24.0, up=(0.0, 0.0, 1.0)) -> None:
    if vp is None or stage is None:
        return
    cam = UsdGeom.Camera.Define(stage, "/World/CaptureCam")
    cam.CreateFocalLengthAttr(float(focal))
    cam.CreateClippingRangeAttr(Gf.Vec2f(0.05, 500.0))
    view_mat = Gf.Matrix4d()
    view_mat.SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(*up))
    xf = UsdGeom.Xformable(cam.GetPrim())
    xf.ClearXformOpOrder()
    xf.AddTransformOp().Set(view_mat.GetInverse())
    try:
        vp.camera_path = "/World/CaptureCam"
        print("look_at", eye, "->", target, "focal", focal, flush=True)
    except Exception as exc:
        print("look_at failed", exc, flush=True)


def kit_hwnd_size() -> tuple[int, int]:
    try:
        import win32gui
    except Exception:
        return (1920, 1080)
    found: list[int] = []

    def _enum(hwnd, _acc):
        title = win32gui.GetWindowText(hwnd)
        if title.startswith("Cold Drawing Operator Kit") and win32gui.IsWindowVisible(hwnd):
            found.append(hwnd)

    win32gui.EnumWindows(_enum, None)
    if not found:
        return (1920, 1080)
    best = (0, 0)
    for hwnd in found:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w, h = right - left, bottom - top
        if w * h >= best[0] * best[1]:
            best = (w, h)
    return best if best[0] >= 50 else (1920, 1080)


def set_panel_visible(visible: bool) -> None:
    panel = getattr(view, "panel", None)
    window = getattr(panel, "_window", None) if panel is not None else None
    if window is None:
        return
    try:
        window.visible = visible
        if visible:
            window.width = 400
            window.height = 680
            window.position_x = 860
            window.position_y = 8
            print("panel", window.position_x, window.width, window.height, flush=True)
    except Exception:
        pass


def dump_kit_window(path: Path) -> None:
    try:
        import ctypes

        import win32gui
        import win32ui
        from PIL import Image
    except Exception as exc:
        print("win32 unavailable", exc, flush=True)
        return
    found: list[int] = []

    def _enum(hwnd, _acc):
        title = win32gui.GetWindowText(hwnd)
        if title.startswith("Cold Drawing Operator Kit") and win32gui.IsWindowVisible(hwnd):
            found.append(hwnd)

    win32gui.EnumWindows(_enum, None)
    if not found:
        print("no kit hwnd", flush=True)
        return
    hwnd = found[0]
    best_w = 0
    for candidate in found:
        left, top, right, bottom = win32gui.GetWindowRect(candidate)
        if right - left >= best_w:
            best_w = right - left
            hwnd = candidate
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bottom - top
    if w < 50 or h < 50:
        print("kit hwnd too small", w, h, flush=True)
        return
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    save_dc.SelectObject(bitmap)
    printed = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    image = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1)
    image.save(path)
    print("window", path.name, path.stat().st_size, "PrintWindow", printed, flush=True)
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)


def capture(path: Path, camera_key: str, *, panel: bool = True, frames: int = 90) -> None:
    set_panel_visible(panel)
    if panel:
        window = getattr(getattr(view, "panel", None), "_window", None)
        if window is not None:
            try:
                window.position_x = 860
                window.position_y = 8
                window.width = 400
                window.height = 680
            except Exception:
                pass
    eye, target = LOOK[camera_key]
    author_look_at(eye, target, focal=FOCAL[camera_key])
    pump(frames)
    bound = view.tick()
    print(
        "frame",
        path.name,
        "headline",
        bound.get("headline"),
        "indicator",
        bound.get("indicator"),
        "decision_heading",
        getattr(getattr(view, "panel", None), "decision_heading", None) and view.panel.decision_heading.text,
        "decision_line",
        getattr(getattr(view, "panel", None), "decision_id", None) and view.panel.decision_id.text,
        flush=True,
    )
    pump(20)
    if path.exists():
        path.unlink()

    async def _wait():
        kit = kit_app.get_app()
        for _ in range(20):
            await kit.next_update_async()
        if vp is not None:
            helper = capture_viewport_to_file(vp, file_path=str(path))
            try:
                await helper.wait_for_result()
            except Exception as exc:
                print("wait_for_result", exc, flush=True)
        for _ in range(25):
            await kit.next_update_async()
            if path.exists() and path.stat().st_size > 2048:
                return

    task = asyncio.ensure_future(_wait())
    deadline = time.time() + 60
    while not task.done() and time.time() < deadline and app.is_running():
        app.update()
    print("capture", path.name, "exists", path.exists(), "bytes", path.stat().st_size if path.exists() else 0, flush=True)
    window_path = path.with_name(path.stem + "-window.png")
    dump_kit_window(window_path)
    publish_window_frame(window_path, path)
    if panel:
        compose_hero_panel(path, window_path, path.with_name(path.stem + "-composed.png"))


def publish_window_frame(window_path: Path, dest: Path) -> None:
    """Crop Kit chrome and publish a 1920x1080 frame from the real window."""
    try:
        from PIL import Image
    except Exception as exc:
        print("publish skipped", exc, flush=True)
        return
    if not window_path.exists():
        return
    image = Image.open(window_path).convert("RGB")
    width, height = image.size
    top = 32 if height > 400 else 0
    frame = image.crop((2, top, width - 2, height - 2))
    fw, fh = frame.size
    if fw < 16 or fh < 16:
        return
    scale = 1920 / fw
    resized = frame.resize((1920, max(1, int(fh * scale))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (1920, 1080), (18, 20, 22))
    y = (1080 - resized.size[1]) // 2
    canvas.paste(resized, (0, y))
    canvas.save(dest)
    print("published", dest.name, dest.stat().st_size, "from window", fw, fh, flush=True)


def compose_hero_panel(viewport: Path, window: Path, dest: Path) -> None:
    """Join a real viewport frame with the real omni.ui panel for 16:9 evidence."""
    try:
        from PIL import Image
    except Exception as exc:
        print("compose skipped", exc, flush=True)
        return
    if not viewport.exists() or not window.exists():
        print("compose missing inputs", viewport.exists(), window.exists(), flush=True)
        return
    vp = Image.open(viewport).convert("RGB")
    win = Image.open(window).convert("RGB")
    ww, wh = win.size
    left = min(max(0, 854), max(0, ww - 410))
    panel = win.crop((left, 32, min(ww - 4, left + 408), min(wh - 8, 32 + 980)))
    canvas = Image.new("RGB", (1600, 720), (18, 20, 22))
    vp_r = vp.resize((1180, 720), Image.Resampling.LANCZOS)
    canvas.paste(vp_r, (0, 0))
    panel_r = panel.resize((420, 720), Image.Resampling.LANCZOS)
    canvas.paste(panel_r, (1180, 0))
    canvas.save(dest)
    print("composed", dest.name, dest.stat().st_size, "panel", 420, 720, flush=True)


tag = os.environ.get("KIT_CAPTURE_TAG", "safe")
if tag in {"factory", "overview"}:
    capture(OUT / "01_factory_overview.png", "factory", panel=False)
    capture(OUT / "02_drawing4_hero.png", "hero", panel=False)
    capture(OUT / "03_drawing4_process.png", "process", panel=False)
elif tag == "safe":
    capture(OUT / "04_fast_path_safe.png", "hero_panel", panel=True)
elif tag in {"fea", "running"}:
    capture(OUT / "06_fea_running.png", "hero_panel", panel=True)
elif tag in {"inconclusive", "manual"}:
    capture(OUT / "08_manual_review.png", "hero_panel", panel=True)
else:
    capture(OUT / f"{tag}_factory.png", "factory", panel=False)
    capture(OUT / f"{tag}_hero.png", "hero_panel", panel=True)

print("shutdown", flush=True)
sys.exit(app.shutdown())
