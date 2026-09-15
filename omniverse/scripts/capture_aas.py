"""Headless AAS Inspector capture. Display only. Requires a live Twin API."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "docs" / "evidence"
URL = os.environ.get("AAS_CAPTURE_URL", "http://127.0.0.1:8000/aas-inspector?capture=1")
NAME = os.environ.get("AAS_CAPTURE_NAME", "05_fast_path_aas.png")


def main() -> None:
    png = OUT / NAME
    png.parent.mkdir(parents=True, exist_ok=True)
    exe = None
    for binary in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        exe = shutil.which(binary)
        if exe:
            break
    if not exe:
        raise SystemExit("no chrome/chromium for AAS capture")
    subprocess.run(
        [
            exe,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1600,620",
            "--default-background-color=1c1f24",
            "--virtual-time-budget=4000",
            f"--screenshot={png}",
            URL,
        ],
        check=False,
        timeout=30,
    )
    if not png.is_file() or png.stat().st_size < 1000:
        raise SystemExit(f"AAS capture failed: {png}")
    print(png, png.stat().st_size)


if __name__ == "__main__":
    main()
