from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.inference.pinn.adapter import PinnUnavailable, ReleasedPinnAdapter
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.paths import REPO_ROOT
from cold_drawing_twin.persistence.models import DecisionRow, FeaJobRow
from cold_drawing_twin.settings import load_settings
from cold_drawing_twin.simulation.run import run_case

PRIMARY = "BG.MIEUM.DRW.04"
DEMO = ProcessFeatures(0.3, 0.2, 0.08, 0.7)
NEED_FEA = ProcessFeatures(0.55, 0.2, 0.08, 0.7)


def _seed(container, features: ProcessFeatures, state_version: str = "state-0001", quality: str = "GOOD") -> None:
    from datetime import datetime, timezone

    session = container.open()
    twin, _events, _evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        features,
        source_timestamp=datetime.now(timezone.utc),
        quality=quality,
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
    print(_format_evaluation(session, row))
    session.close()
    return 0 if row.state in {"FINALIZED", "MANUAL_REVIEW", "FEA_QUEUED"} else 1


def cmd_demo_fea(_args: argparse.Namespace) -> int:
    """NEED_FEA path through ReleasedPinnAdapter. Out-of-range input is a real NEED_FEA."""
    container = build_container()
    _seed(container, NEED_FEA, state_version="state-fea")
    session = container.open()
    _twin, _events, evaluation = container.services(session)
    row = evaluation.start_operational(PRIMARY)
    session.commit()
    print(_format_evaluation(session, row))
    session.close()
    return 0


def cmd_demo_system(_args: argparse.Namespace) -> int:
    asyncio.run(_seed_from_opcua())
    fast_code = cmd_demo_fast(_args)
    fea_code = cmd_demo_fea(_args)
    return 0 if fast_code == 0 and fea_code == 0 else 1


def cmd_seed_opcua(_args: argparse.Namespace) -> int:
    asyncio.run(_seed_from_opcua())
    return 0


async def _seed_from_opcua() -> None:
    from asyncua import Client

    from cold_drawing_twin.edge.opcua.adapter import write_twin
    from cold_drawing_twin.edge.opcua.adapter import read_process
    from cold_drawing_twin.edge.opcua.simulator import serve_drawing4

    settings = load_settings()
    container = build_container(settings)
    endpoint = "opc.tcp://127.0.0.1:4848/cold-drawing/"
    server = await serve_drawing4(DEMO, endpoint)
    async with server:
        async with Client(url=endpoint) as client:
            reading = await read_process(client)
        write_twin(container, reading)
        print(
            json.dumps(
                {
                    "asset_id": PRIMARY,
                    "quality": reading.quality,
                    "source_timestamp": None if reading.source_timestamp is None else reading.source_timestamp.isoformat(),
                    "source_timestamp_missing": reading.source_timestamp_missing,
                    "features": {
                        "reduction_ratio": reading.reduction_ratio,
                        "die_half_angle_rad": reading.die_half_angle_rad,
                        "friction_coefficient": reading.friction_coefficient,
                        "normalized_hardening_coefficient": reading.normalized_hardening_coefficient,
                    },
                },
                indent=2,
            )
        )


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
    result = run_case(DEMO, Path("simulation/workspaces/fea-smoke"), "fea-smoke", smoke=True)
    print(json.dumps(result, indent=2, default=str))
    if result["solver_status"] != "SUCCEEDED":
        print(
            "FEA smoke wrote geometry, mesh, and Radioss decks. "
            "A physics solve needs OPENRADIOSS_STARTER_BIN and OPENRADIOSS_ENGINE_BIN. "
            "See scripts/install_openradioss.sh. This is not a mocked success.",
            file=sys.stderr,
        )
        return 1
    return 0


def _format_evaluation(session, row) -> str:
    decision = (
        session.query(DecisionRow).filter(DecisionRow.evaluation_id == row.evaluation_id).order_by(DecisionRow.created_at.desc()).first()
    )
    job = session.query(FeaJobRow).filter(FeaJobRow.evaluation_id == row.evaluation_id).order_by(FeaJobRow.created_at.desc()).first()
    pinn = row.pinn_result or {}
    lineage = (decision.lineage if decision else {}) or {}
    fea = lineage.get("fea") or {}
    quality = (job.quality if job else None) or {}
    lines = [
        f"Asset: {row.asset_id}",
        f"Snapshot: {row.snapshot_id}",
        "",
        "PINN",
        f"  verdict: {pinn.get('verdict')}",
        f"  model: {pinn.get('model_version')}",
        "",
        "Routing",
        f"  action: {row.routing_action}",
        f"  policy: {(decision.routing_policy_version if decision else None) or 'routing-v1'}",
    ]
    if job is not None:
        qpass = quality.get("pass")
        qlabel = "PASS" if qpass else "FAIL"
        lines.extend(
            [
                "",
                "FEA",
                f"  solver: {job.solver}",
                f"  status: {job.status}",
                f"  quality: {qlabel}",
            ]
        )
    if decision is not None:
        lines.extend(
            [
                "",
                "Decision",
                f"  verdict: {decision.verdict}",
                f"  status: {decision.status}",
            ]
        )
        reason = None
        if isinstance(lineage.get("fea"), dict):
            reason = (lineage.get("decision") or {}).get("reason")
        if decision.verdict == "INCONCLUSIVE":
            reason = "No validated automatic FEA safety threshold configured."
        if reason:
            lines.extend(["", "Reason", f"  {reason}"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cold-drawing-twin")
    sub = parser.add_subparsers(dest="cmd", required=True)
    verify = sub.add_parser("model-verify")
    verify.add_argument("--features", type=float, nargs=4, default=[0.3, 0.2, 0.08, 0.7])
    verify.set_defaults(func=cmd_model_verify)
    sub.add_parser("demo-fast").set_defaults(func=cmd_demo_fast)
    sub.add_parser("demo-fea").set_defaults(func=cmd_demo_fea)
    sub.add_parser("demo-system").set_defaults(func=cmd_demo_system)
    sub.add_parser("seed-opcua").set_defaults(func=cmd_seed_opcua)
    sub.add_parser("factory-stage").set_defaults(func=cmd_factory_stage)
    sub.add_parser("fetch-pinn").set_defaults(func=cmd_fetch_pinn)
    sub.add_parser("fea-smoke").set_defaults(func=cmd_fea_smoke)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
