from cold_drawing_twin.domain.timeouts import (
    FEA_CONVERSION_BUDGET_S,
    FEA_SOLVER_PHASE_COUNT,
    FEA_TASK_HARD_GRACE_S,
    fea_solver_phase_timeout_s,
    fea_task_hard_limit_s,
    fea_task_soft_limit_s,
)
from cold_drawing_twin.settings import Settings
from workers.celery_app import app as celery_app
from workers import celery_app as celery_module


def _settings(phase_s: int = 10) -> Settings:
    return Settings(fea_job_timeout_s=phase_s, _env_file=None)


def test_task_soft_limit_exceeds_one_solver_phase():
    settings = _settings(10)
    phase = fea_solver_phase_timeout_s(settings)
    soft = fea_task_soft_limit_s(settings)
    assert phase == 10
    assert soft > phase


def test_task_budget_covers_starter_and_engine():
    settings = _settings(10)
    both_phases = FEA_SOLVER_PHASE_COUNT * fea_solver_phase_timeout_s(settings)
    soft = fea_task_soft_limit_s(settings)
    hard = fea_task_hard_limit_s(settings)
    assert both_phases == 20
    assert soft >= both_phases + FEA_CONVERSION_BUDGET_S
    assert hard > soft
    assert hard - soft == FEA_TASK_HARD_GRACE_S


def test_two_maxed_phases_fit_inside_celery_limits():
    settings = _settings(600)
    used = FEA_SOLVER_PHASE_COUNT * fea_solver_phase_timeout_s(settings)
    assert used <= fea_task_soft_limit_s(settings)
    assert used < fea_task_hard_limit_s(settings)


def test_celery_app_uses_two_phase_task_limits():
    settings = celery_module.settings
    phase = fea_solver_phase_timeout_s(settings)
    assert celery_app.conf.task_soft_time_limit == fea_task_soft_limit_s(settings)
    assert celery_app.conf.task_time_limit == fea_task_hard_limit_s(settings)
    assert celery_app.conf.task_soft_time_limit > phase
    assert celery_app.conf.task_soft_time_limit >= FEA_SOLVER_PHASE_COUNT * phase
    assert celery_app.conf.task_time_limit > celery_app.conf.task_soft_time_limit
