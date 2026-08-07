from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cold_drawing_twin.settings import Settings

# OpenRadioss Starter, then Engine. Each phase gets fea_job_timeout_s.
FEA_SOLVER_PHASE_COUNT = 2

# Per conversion subprocess in run_openradioss (th_to_csv / anim_to_vtk).
FEA_CONVERSION_TOOL_TIMEOUT_S = 60

# Worker budget for typical conversion after Engine (one T01 pass plus one ANIM pass).
FEA_CONVERSION_BUDGET_S = FEA_CONVERSION_TOOL_TIMEOUT_S * 2

# Mesh, decks, parse, criterion, and DB work around the solver phases.
FEA_TASK_SOFT_GRACE_S = 30

# Extra seconds after the soft limit before Celery kills the process.
FEA_TASK_HARD_GRACE_S = 30


def fea_solver_phase_timeout_s(settings: Settings) -> int:
    """Maximum runtime for one OpenRadioss phase (Starter or Engine)."""
    return int(settings.fea_job_timeout_s)


def fea_task_soft_limit_s(settings: Settings) -> int:
    """Celery soft time limit. Covers both solver phases plus conversion and orchestration."""
    return (
        FEA_SOLVER_PHASE_COUNT * fea_solver_phase_timeout_s(settings)
        + FEA_CONVERSION_BUDGET_S
        + FEA_TASK_SOFT_GRACE_S
    )


def fea_task_hard_limit_s(settings: Settings) -> int:
    """Celery hard time limit. Must stay above the soft limit."""
    return fea_task_soft_limit_s(settings) + FEA_TASK_HARD_GRACE_S
