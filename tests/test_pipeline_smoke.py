"""Smoke tests for demo pipeline execution."""

from pathlib import Path

from src.pipeline import run_pipeline


def test_demo_pipeline_smoke() -> None:
    """Pipeline should run in demo mode and emit core text artifacts."""
    run_pipeline(demo_mode=True)

    expected_outputs = [
        Path("outputs/metrics_latest.json"),
        Path("outputs/alerts/alert_latest.md"),
        Path("outputs/marts/student_risk_daily_sample.csv"),
        Path("reports/ab_test_report.md"),
        Path("reports/roi_sensitivity.csv"),
        Path("reports/executive_summary.md"),
    ]

    missing = [str(path) for path in expected_outputs if not path.exists()]
    assert not missing, f"Missing expected artifacts: {missing}"
