from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from cold_drawing_twin.paths import REPO_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = f"sqlite:///{REPO_ROOT / 'data' / 'runtime' / 'cold_drawing.db'}"

    celery_broker_url: str = ""
    celery_result_backend: str = "rpc://"
    fea_execution: str = "inline"

    basyx_aas_repository_url: str = "http://localhost:8081"
    basyx_enabled: bool = False

    pinn_hf_repo: str = "MongsangGa/cold-drawing-pinn-poc"
    pinn_model_version: str = "v0.1.1"
    pinn_model_dir: Path = REPO_ROOT / "models" / "cold-drawing-pinn-poc"

    openradioss_starter_bin: str = ""
    openradioss_engine_bin: str = ""
    openradioss_work_dir: Path = REPO_ROOT / "simulation" / "workspaces"
    fea_job_timeout_s: int = 600

    usd_stage_path: Path = REPO_ROOT / "usd" / "factory" / "bugok_factory.usda"
    opcua_endpoint: str = "opc.tcp://127.0.0.1:4840/cold-drawing/"

    freshness_max_age_seconds: int | None = None


def load_settings() -> Settings:
    return Settings()
