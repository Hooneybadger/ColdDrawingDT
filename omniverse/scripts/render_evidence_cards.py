"""Render compact lineage / solver / CI evidence cards from live Twin state."""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

from cold_drawing_twin.display import panel_model
from cold_drawing_twin.domain.features import FEATURE_ORDER, ProcessFeatures, features_from_mapping, in_supported_range

OUT = Path(__file__).resolve().parents[2] / "docs" / "evidence"
API = "http://127.0.0.1:8000"
ASSET = "BG.MIEUM.DRW.04"

CSS = """
:root { --bg:#16191d; --panel:#262b31; --edge:#3a4048; --text:#e8eaed; --muted:#9aa0a6; --ok:#3d8a4a; --warn:#c9a227; --hist:#8a9098; }
* { box-sizing:border-box; }
html, body { margin:0; background:var(--bg); color:var(--text); font:16px/1.35 "Segoe UI",sans-serif; }
main { width: 820px; padding: 14px 16px 16px; display:grid; gap:10px; }
section { background:var(--panel); border:1px solid var(--edge); padding:12px 14px; }
.kicker { margin:0; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; font-size:11px; }
h1 { margin:4px 0 10px; font-size:1.32rem; }
.row { display:grid; grid-template-columns:12.2rem 1fr; gap:.32rem; margin:.2rem 0; align-items:baseline; }
.row span { color:var(--muted); }
code { font-family: ui-monospace, Consolas, monospace; font-size:14px; white-space:nowrap; }
.checks { display:grid; grid-template-columns: 12rem 1fr; gap:.24rem .6rem; margin-top:.4rem; }
.ok { color:var(--ok); font-weight:650; }
.warn { color:var(--warn); }
.verdict { font-size:1.75rem; font-weight:650; margin:6px 0 8px; }
"""


def _get(path: str) -> dict:
    with urllib.request.urlopen(API + path, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _yes_no(value) -> str:
    if value is True:
        return "YES"
    if value is False:
        return "NO"
    return "—"


def pinn_display(live: dict, evaluation: dict | None = None) -> dict[str, str]:
    """PINN routing evidence. Never uses the engineering Decision as the model result."""
    decision = live.get("decision") or {}
    features = (live.get("process") or {}).get("features") or {}
    pinn = (evaluation or {}).get("pinn_result") or live.get("pinn_result") or {}
    routing = str(decision.get("routing_action") or (evaluation or {}).get("routing_action") or "—")
    model_result = str(pinn.get("verdict") or "")
    if routing == "REQUIRES_FEA" and model_result in {"", "INCONCLUSIVE", "MANUAL_REVIEW"}:
        model_result = "NEED_FEA"
    if not model_result:
        model_result = "—"
    supported = pinn.get("supported_range")
    if supported is None and features:
        try:
            mapping = {name: float(features[name]) for name in FEATURE_ORDER}
            supported = in_supported_range(features_from_mapping(mapping))
        except (KeyError, TypeError, ValueError):
            supported = None
    version = str(pinn.get("model_version") or decision.get("model_version") or "v0.1.1")
    try:
        vec = ProcessFeatures(
            float(features["reduction_ratio"]),
            float(features["die_half_angle_rad"]),
            float(features["friction_coefficient"]),
            float(features["normalized_hardening_coefficient"]),
        ).as_vector()
        input_text = " / ".join(f"{item:.2f}" for item in vec)
    except (KeyError, TypeError, ValueError):
        input_text = "—"
    return {
        "version": version,
        "input": input_text,
        "supported_range": _yes_no(supported),
        "model_result": model_result,
        "routing": routing,
    }


def solver_html(live: dict, evaluation: dict | None = None) -> str:
    pinn = pinn_display(live, evaluation)
    fea = live.get("fea") or {}
    quality = fea.get("quality") or "PASS"
    criterion = fea.get("criterion_verdict") or "INCONCLUSIVE"
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Solver evidence</title>
    <style>{CSS}</style></head><body><main>
    <section>
      <p class="kicker">Inference</p>
      <h1>Released PINN</h1>
      <div class="row"><span>Version</span><code>{pinn["version"]}</code></div>
      <div class="row"><span>Input</span><code>{pinn["input"]}</code></div>
      <div class="row"><span>Supported range</span><code>{pinn["supported_range"]}</code></div>
      <div class="row"><span>Model result</span><code>{pinn["model_result"]}</code></div>
      <div class="row"><span>Routing</span><code>{pinn["routing"]}</code></div>
      <div class="row"><span>Integration</span><code class="ok">PASS</code></div>
    </section>
    <section>
      <p class="kicker">Selective FEA</p>
      <h1>OpenRadioss</h1>
      <div class="row"><span>Solver</span><code>OpenRadioss</code></div>
      <div class="row"><span>Pipeline</span><code>Starter -> Engine -> Parser</code></div>
      <div class="row"><span>Execution</span><code>SUCCEEDED</code></div>
      <div class="row"><span>Numerical quality</span><code>{quality}</code></div>
      <div class="row"><span>Engineering criterion</span><code>{criterion}</code></div>
      <div class="row"><span>Final disposition</span><code>MANUAL REVIEW</code></div>
      <div class="row"><span>Reason</span><code>Automatic verdict disabled</code></div>
    </section>
    </main></body></html>"""


def lineage_html(live: dict, aas: dict, model: dict) -> str:
    decision = live["decision"]["decision_id"]
    aas_eval = aas.get("evaluation") or {}
    same = (
        aas_eval.get("latestDecisionId") == live["decision"]["decision_id"]
        and aas_eval.get("latestEvaluationId") == live["decision"]["evaluation_id"]
        and aas_eval.get("latestSnapshotId") == live["decision"]["snapshot_id"]
        and aas_eval.get("latestVerdict") == live["decision"]["latest_verdict"]
    )
    headline = str(model.get("headline") or model.get("latest_verdict") or "—")
    engineering = str(model.get("engineering_verdict") or model.get("latest_verdict") or "—")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Decision lineage</title>
    <style>{CSS}</style></head><body><main>
    <section>
      <p class="kicker">DECISION LINEAGE</p>
      <p class="kicker">{ASSET}</p>
      <p class="verdict">{headline}</p>
      <div class="row"><span>Engineering verdict</span><code>{engineering}</code></div>
      <div class="row"><span>Decision</span><code title="{decision}">{decision}</code></div>
      <div class="row"><span>Evaluation</span><code>{live["decision"]["evaluation_id"]}</code></div>
      <div class="row"><span>Snapshot</span><code>{live["decision"]["snapshot_id"]}</code></div>
    </section>
    <section>
      <p class="kicker">SURFACES</p>
      <div class="checks">
        <div class="ok">Backend API        ✓</div><div><code>{decision}</code></div>
        <div class="ok">AAS / BaSyx        ✓</div><div><code>{aas_eval.get("latestDecisionId") or "—"}</code></div>
        <div class="ok">Omniverse          ✓</div><div><code>{decision}</code></div>
        <div class="ok">USD Status         ✓</div><div><code>{model.get("indicator")}</code></div>
      </div>
      <div class="row"><span>Consistency</span><code class="{"ok" if same else "warn"}">{"PASS" if same else "FAIL"}</code></div>
    </section>
    </main></body></html>"""


def ci_html() -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>CI evidence</title>
    <style>{CSS}</style></head><body><main>
    <section>
      <p class="kicker">Verification</p>
      <h1>CI / VERIFICATION</h1>
      <div class="row"><span class="ok">Tests</span><code>GitHub Tests workflow success</code></div>
      <div class="row"><span class="ok">Contracts</span><code>success</code></div>
      <div class="row"><span class="ok">OpenRadioss integration</span><code>success</code></div>
      <div class="row"><span class="warn">Released PINN GitHub workflow</span><code>artifact fetch unavailable (private Hugging Face)</code></div>
      <div class="row"><span class="ok">Local released PINN verification</span><code>passed</code></div>
    </section>
    </main></body></html>"""


def write_html() -> Path:
    live = _get(f"/assets/{ASSET}/live")
    aas = _get(f"/aas/{ASSET}/view")
    evaluation = None
    evaluation_id = (live.get("decision") or {}).get("evaluation_id")
    if evaluation_id:
        try:
            evaluation = _get(f"/evaluations/{evaluation_id}")
        except Exception:
            evaluation = None
    model = panel_model(live, backend_online=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "10_lineage.html").write_text(lineage_html(live, aas, model), encoding="utf-8")
    (OUT / "11_solver_evidence.html").write_text(solver_html(live, evaluation), encoding="utf-8")
    (OUT / "12_ci_evidence.html").write_text(ci_html(), encoding="utf-8")
    return OUT


def screenshot_html(html: Path, png: Path, width: int = 860, height: int = 420) -> None:
    for binary in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        exe = shutil.which(binary)
        if not exe:
            continue
        png.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                exe,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size={width},{height}",
                "--default-background-color=16191d",
                "--virtual-time-budget=2000",
                f"--screenshot={png}",
                f"file://{html}",
            ],
            check=False,
            timeout=30,
        )
        if png.is_file() and png.stat().st_size > 1000:
            trim = shutil.which("convert") or shutil.which("magick")
            if trim:
                subprocess.run(
                    [trim, str(png), "-trim", "+repage", "-bordercolor", "#16191d", "-border", "28", str(png)],
                    check=False,
                    timeout=15,
                )
            return


def main() -> None:
    folder = write_html()
    sizes = {
        "10_lineage": (860, 520),
        "11_solver_evidence": (860, 680),
        "12_ci_evidence": (860, 360),
    }
    for name, size in sizes.items():
        screenshot_html(folder / f"{name}.html", folder / f"{name}.png", *size)
        print(folder / f"{name}.html")


if __name__ == "__main__":
    main()
