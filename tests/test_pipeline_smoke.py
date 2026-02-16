"""Smoke tests for demo pipeline execution."""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline import run_pipeline


@pytest.mark.parametrize("backend", ["sklearn"])
def test_demo_pipeline_smoke(monkeypatch: pytest.MonkeyPatch, backend: str) -> None:
    """Pipeline should run in demo mode and emit core text artifacts."""
    monkeypatch.setenv("MODEL_BACKEND", backend)
    run_pipeline(demo_mode=True)

    expected_outputs = [
        Path("outputs/metrics_latest.json"),
        Path("outputs/shap_top_features.json"),
        Path("outputs/artifacts_manifest.json"),
        Path("outputs/alerts/alert_latest.md"),
        Path("outputs/marts/student_risk_daily_sample.csv"),
        Path("reports/ab_test_report.md"),
        Path("reports/roi_sensitivity.csv"),
        Path("reports/executive_summary.md"),
    ]

    missing = [str(path) for path in expected_outputs if not path.exists()]
    assert not missing, f"Missing expected artifacts: {missing}"

    student_risk = pd.read_csv("outputs/marts/student_risk_daily_sample.csv")
    assert student_risk["week"].nunique() > 1
    assert pd.api.types.is_numeric_dtype(student_risk["risk_score"])
    assert student_risk["risk_score"].notna().any()

    course_summary = pd.read_csv("outputs/marts/course_summary_daily_sample.csv")
    assert "week" in course_summary.columns
    assert course_summary["week"].nunique() > 1

    manifest = json.loads(Path("outputs/artifacts_manifest.json").read_text())
    assert manifest["model_backend"] == "sklearn"
    assert manifest["db_mode"] in {"sqlite", "postgres"}
    assert manifest["artifacts"], "Expected manifest artifacts to be non-empty"


@pytest.mark.parametrize(
    "backend,module_name",
    [("pytorch", "torch"), ("tensorflow", "tensorflow")],
)
def test_optional_deep_learning_backends(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    module_name: str,
) -> None:
    pytest.importorskip(module_name)
    monkeypatch.setenv("MODEL_BACKEND", backend)
    run_pipeline(demo_mode=True)

    metrics = json.loads(Path("outputs/metrics_latest.json").read_text())
    assert metrics["model_backend"] == backend
    assert metrics["backend_hyperparams"]["epochs"] <= 3
