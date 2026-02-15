"""Central configuration for the OULAD pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    repo_root: Path
    data_raw_dir: Path
    data_processed_dir: Path
    outputs_dir: Path
    marts_dir: Path
    alerts_dir: Path
    experiments_dir: Path
    reports_dir: Path
    models_dir: Path
    db_path: Path
    database_url: str | None
    db_mode: str
    random_seed: int
    high_risk_threshold: float
    spike_threshold_pct: float
    current_week: int
    split_week: int
    top_k_at_risk: int
    value_per_pass: float
    default_intervention_cost: float
    demo_mode: bool
    model_backend: str
    storage_backend: str
    aws_region: str
    s3_bucket: str
    s3_prefix: str


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def load_config(demo_mode: bool | None = None) -> PipelineConfig:
    root = Path(__file__).resolve().parents[1]
    use_demo_mode = (
        str(os.getenv("PIPELINE_DEMO_MODE", "true")).lower() == "true"
        if demo_mode is None
        else demo_mode
    )
    database_url = os.getenv("DATABASE_URL")
    return PipelineConfig(
        repo_root=root,
        data_raw_dir=root / "data" / "raw",
        data_processed_dir=root / "data" / "processed",
        outputs_dir=root / "outputs",
        marts_dir=root / "outputs" / "marts",
        alerts_dir=root / "outputs" / "alerts",
        experiments_dir=root / "outputs" / "experiments",
        reports_dir=root / "reports",
        models_dir=root / "models",
        db_path=root / "data" / "processed" / "pipeline.db",
        database_url=database_url,
        db_mode="postgres" if database_url else "sqlite",
        random_seed=_env_int("PIPELINE_RANDOM_SEED", 42),
        high_risk_threshold=_env_float("HIGH_RISK_THRESHOLD", 0.25),
        spike_threshold_pct=_env_float("RISK_SPIKE_THRESHOLD_PCT", 0.10),
        current_week=_env_int("CURRENT_WEEK", 10),
        split_week=_env_int("SPLIT_WEEK", 7),
        top_k_at_risk=_env_int("TOP_K_AT_RISK", 50),
        value_per_pass=_env_float("VALUE_PER_PASS", 1200.0),
        default_intervention_cost=_env_float("INTERVENTION_COST", 150.0),
        demo_mode=use_demo_mode,
        model_backend=os.getenv("MODEL_BACKEND", "sklearn").strip().lower(),
        storage_backend=os.getenv("STORAGE_BACKEND", "local").strip().lower(),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        s3_bucket=os.getenv("S3_BUCKET", "").strip(),
        s3_prefix=os.getenv("S3_PREFIX", "").strip("/"),
    )


def ensure_directories(config: PipelineConfig) -> None:
    for path in [
        config.data_raw_dir,
        config.data_processed_dir,
        config.outputs_dir,
        config.marts_dir,
        config.alerts_dir,
        config.experiments_dir,
        config.reports_dir,
        config.models_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
