from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.inference.pinn.adapter import PinnUnavailable, ReleasedPinnAdapter
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.paths import REPO_ROOT
from cold_drawing_twin.settings import load_settings
from cold_drawing_twin.simulation.run import run_case

PRIMARY = "BG.MIEUM.DRW.04"
DEMO = ProcessFeatures(0.3, 0.2, 0.08, 0.7)


def _seed(container, features: ProcessFeatures, state_version: str = "state-0001") -> None:
    session = container.open()
    twin, _events, _evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        features,
        source_timestamp=datetime.now(timezone.utc),
        quality="GOOD",
        state_version=state_version,
    )
    session.commit()
    session.close()


def cmd_model_verify(args: argparse.Namespace) -> int:
    settings = load_settings()
    adapter = ReleasedPinnAdapter(settings.pinn_model_dir, settings.pinn_model_version)
    features = ProcessFeatures(*args.features)
    try:
        result = adapter.predict(features)
    except PinnUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "verdict": result.verdict,
                "stress_indicator": result.stress_indicator,
                "damage_indicator": result.damage_indicator,
                "physics_residual": result.physics_residual,
                "confidence": None,
                "model_version": result.model_version,
                "supported_range": result.supported_range,
            },
            indent=2,
        )
    )
    return 0


def cmd_demo_fast(_args: argparse.Namespace) -> int:
    container = build_container()
    _seed(container, DEMO)
    session = container.open()
    _twin, _events, evaluation = container.services(session)
    row = evaluation.start_operational(PRIMARY, "state-0001")
    session.commit()
    print(
        json.dumps(
            {
                "evaluation_id": row.evaluation_id,
                "snapshot_id": row.snapshot_id,
                "state": row.state,
                "routing_action": row.routing_action,
                "pinn_result": row.pinn_result,
            },
            indent=2,
        )
    )
    session.close()
    return 0 if row.state in {"FINALIZED", "MANUAL_REVIEW", "FEA_QUEUED"} else 1


def cmd_demo_fea(_args: argparse.Namespace) -> int:
    from cold_drawing_twin.domain.routing import PinnResult
    from cold_drawing_twin.inference.pinn.adapter import StaticPinnAdapter

    need = PinnResult("NEED_FEA", 0.0, 0.0, 0.0, None, "v0.1.1", True, {"decision": "NEED_FEA"})
    container = build_container(pinn=StaticPinnAdapter(need))
    _seed(container, DEMO)
    session = container.open()
    _twin, _events, evaluation = container.services(session)
    row = evaluation.start_operational(PRIMARY)
    session.commit()
    print(
        json.dumps(
            {
                "evaluation_id": row.evaluation_id,
                "state": row.state,
                "routing_action": row.routing_action,
            },
            indent=2,
        )
    )
    session.close()
    return 0


def cmd_factory_stage(_args: argparse.Namespace) -> int:
    from omniverse.scripts.generate_factory_stage import generate

    path = generate()
    print(path)
    return 0


def cmd_fetch_pinn(_args: argparse.Namespace) -> int:
    settings = load_settings()
    dest = Path(settings.pinn_model_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sibling = REPO_ROOT.parent / "ColdDrawingPinn" / "artifacts" / "hf_release" / "cold-drawing-pinn-poc-v0.1.1"
    if sibling.exists() and (sibling / "pinn.pt").exists():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(sibling, dest)
        print(f"copied PINN bundle to {dest}")
        return 0
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=settings.pinn_hf_repo,
        revision=settings.pinn_model_version,
        local_dir=dest,
    )
    print(f"downloaded PINN bundle to {dest}")
    return 0


def cmd_fea_smoke(_args: argparse.Namespace) -> int:
    result = run_case(DEMO, Path("simulation/workspaces/fea-smoke"), "fea-smoke")
    print(json.dumps(result, indent=2, default=str))
    if result["solver_status"] != "SUCCEEDED":
        print(
            "FEA smoke built geometry and decks; solver did not pass. "
            "OpenRadioss binaries and a calibrated hardening map are required for a physics solve.",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cold-drawing-twin")
    sub = parser.add_subparsers(dest="cmd", required=True)
    verify = sub.add_parser("model-verify")
    verify.add_argument("--features", type=float, nargs=4, default=[0.3, 0.2, 0.08, 0.7])
    verify.set_defaults(func=cmd_model_verify)
    sub.add_parser("demo-fast").set_defaults(func=cmd_demo_fast)
    sub.add_parser("demo-fea").set_defaults(func=cmd_demo_fea)
    sub.add_parser("factory-stage").set_defaults(func=cmd_factory_stage)
    sub.add_parser("fetch-pinn").set_defaults(func=cmd_fetch_pinn)
    sub.add_parser("fea-smoke").set_defaults(func=cmd_fea_smoke)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
