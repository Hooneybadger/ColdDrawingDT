from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class GpuSample:
    index: str
    utilization_ratio: float
    memory_used_bytes: int
    memory_total_bytes: int


def read_nvidia_smi(
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[GpuSample]:
    """Read local NVIDIA devices. Empty when nvidia-smi is missing or fails."""
    try:
        completed = runner(
            [
                "nvidia-smi",
                "--query-gpu=index,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (FileNotFoundError, TimeoutError, OSError):
        return []
    if completed.returncode != 0:
        return []
    samples: list[GpuSample] = []
    for line in completed.stdout.splitlines():
        parts = [item.strip() for item in line.split(",")]
        if len(parts) != 4:
            continue
        try:
            index, util, used_mib, total_mib = parts
            samples.append(
                GpuSample(
                    index=index,
                    utilization_ratio=float(util) / 100.0,
                    memory_used_bytes=int(float(used_mib) * 1024 * 1024),
                    memory_total_bytes=int(float(total_mib) * 1024 * 1024),
                )
            )
        except ValueError:
            continue
    return samples
