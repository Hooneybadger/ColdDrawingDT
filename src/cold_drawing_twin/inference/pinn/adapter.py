from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol

from cold_drawing_twin.config_files import pinn_contract
from cold_drawing_twin.domain.features import ProcessFeatures, in_supported_range
from cold_drawing_twin.domain.routing import PinnResult
from cold_drawing_twin.domain.types import PinnVerdict


class PinnUnavailable(RuntimeError):
    """Released PINN files are missing or the process failed."""


class PinnAdapter(Protocol):
    def predict(self, features: ProcessFeatures) -> PinnResult:
        ...


def map_released_payload(payload: dict[str, Any], *, contract_version: str) -> PinnResult:
    verdict = str(payload.get("decision") or payload.get("verdict") or "")
    if verdict not in {item.value for item in PinnVerdict}:
        raise PinnUnavailable(f"PINN returned unknown decision {verdict!r}")
    stress = payload.get("normalized_stress", payload.get("stress_indicator"))
    damage = payload.get("illustrative_damage", payload.get("damage_indicator"))
    residual = payload.get("physics_residual_max", payload.get("physics_residual"))
    return PinnResult(
        verdict=verdict,
        stress_indicator=None if stress is None else float(stress),
        damage_indicator=None if damage is None else float(damage),
        physics_residual=None if residual is None else float(residual),
        confidence=None,
        model_version=contract_version,
        supported_range=bool(payload.get("supported_range", False)),
        raw=payload,
    )


class ReleasedPinnAdapter:
    """Call the Hugging Face bundle. Do not reimplement model math."""

    def __init__(self, model_dir: Path, contract_version: str | None = None) -> None:
        self.model_dir = Path(model_dir).resolve()
        self.contract_version = contract_version or str(pinn_contract()["model"]["release"])

    def predict(self, features: ProcessFeatures) -> PinnResult:
        if not in_supported_range(features):
            return PinnResult(
                verdict=PinnVerdict.NEED_FEA,
                stress_indicator=None,
                damage_indicator=None,
                physics_residual=None,
                confidence=None,
                model_version=self.contract_version,
                supported_range=False,
                raw={"reason_codes": ["OUTSIDE_MODEL_DOMAIN"], "decision": "NEED_FEA"},
            )
        entry = self.model_dir / "predict.py"
        weights = self.model_dir / "pinn.pt"
        if not entry.exists() or not weights.exists():
            raise PinnUnavailable(f"PINN bundle missing under {self.model_dir}")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.model_dir) + os.pathsep + env.get("PYTHONPATH", "")
        command = [
            sys.executable,
            str(entry),
            "--features",
            *[str(value) for value in features.as_vector()],
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=self.model_dir,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PinnUnavailable(str(exc)) from exc
        if completed.returncode != 0:
            raise PinnUnavailable(completed.stderr.strip() or "PINN process failed")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise PinnUnavailable("PINN stdout is not JSON") from exc
        return map_released_payload(payload, contract_version=self.contract_version)


class StaticPinnAdapter:
    """Test double. Production code uses ReleasedPinnAdapter."""

    def __init__(self, result: PinnResult) -> None:
        self.result = result

    def predict(self, features: ProcessFeatures) -> PinnResult:
        return self.result
