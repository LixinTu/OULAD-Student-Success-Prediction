"""Main orchestration for end-to-end OULAD analytics pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone

from src.alerts.alert import generate_alert
from src.config import ensure_directories, load_config
from src.etl.extract import extract_data
from src.etl.load import get_database_client, initialize_schema, load_processed_data
from src.etl.transform import transform_data
from src.experiments.ab_simulation import run_ab_simulation
from src.features.build_features import build_time_sliced_features
from src.marts.build_marts import build_marts
from src.model.evaluate import evaluate_model
from src.model.explain import generate_shap_artifacts
from src.model.predict import predict_latest_risk
from src.model.train import train_model
from src.storage import S3Storage
from src.utils.logging import get_logger

logger = get_logger(__name__)


def write_executive_summary(metrics: dict, roi_topline: dict, demo_mode: bool) -> None:
    config = load_config(demo_mode=demo_mode)
    summary = f"""# Executive Summary

## Business Problem
Student attrition creates academic and financial risk. This pipeline operationalizes weekly risk detection and intervention planning using behavioral signals.

## Architecture
Automated ETL -> feature engineering -> time-aware ML -> explainability -> marts -> alerting -> experiment simulation -> ROI.

## Model Performance
- AUC: **{metrics['auc']:.3f}**
- PR AUC: **{metrics['pr_auc']:.3f}**
- Precision@0.5: **{metrics['precision_at_0_5']:.3f}**
- Recall@0.5: **{metrics['recall_at_0_5']:.3f}**

## Alerts Triggered
See `outputs/alerts/alert_latest.md` for threshold and spike checks.

## Experiment Outcomes
See `reports/ab_test_report.md` for uplift scenarios (3%, 5%, 8%) with CIs and z-test p-values.

## ROI Findings
Top ROI scenario: uplift={roi_topline['uplift_assumption']:.0%}, cost={roi_topline['cost_per_student']}, roi={roi_topline['roi']:.2f}.

## Production Roadmap
1. Deploy scheduler + model retraining cadence.
2. Add drift monitoring and intervention outcome feedback loop.
3. Integrate dashboards with cloud warehouse + IAM controls.

---
Generated on {datetime.utcnow().isoformat()}Z | Demo mode: {demo_mode}
"""
    (config.reports_dir / "executive_summary.md").write_text(summary)


def _build_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
            .strip()
            .lower()
        )
    except Exception:
        sha = "nogit"
    return f"{timestamp}-{sha}"


def _build_s3_uri(bucket: str, prefix: str, key: str) -> str:
    path = f"{prefix.strip('/')}/{key}".strip("/") if prefix else key
    return f"s3://{bucket}/{path}"


def _artifact_entries(config, run_id: str, storage_backend: str) -> list[dict[str, str | int]]:
    patterns = [
        "outputs/metrics_latest.json",
        "outputs/shap_top_features.json",
        "outputs/marts/*.csv",
        "outputs/alerts/*.md",
        "reports/*.md",
        "reports/*.csv",
    ]

    entries: list[dict[str, str | int]] = []
    for pattern in patterns:
        for artifact_path in sorted(config.repo_root.glob(pattern)):
            if not artifact_path.is_file():
                continue
            rel_path = artifact_path.relative_to(config.repo_root).as_posix()
            key = f"runs/{run_id}/{rel_path}"
            storage_uri = (
                _build_s3_uri(config.s3_bucket, config.s3_prefix, key)
                if storage_backend == "s3"
                else f"local://{rel_path}"
            )
            entries.append(
                {
                    "local_path": rel_path,
                    "size_bytes": artifact_path.stat().st_size,
                    "storage_uri": storage_uri,
                    "s3_key": key,
                }
            )
    return entries


def publish_artifacts_manifest(config, db_mode: str) -> None:
    run_id = _build_run_id()
    entries = _artifact_entries(config, run_id=run_id, storage_backend=config.storage_backend)

    manifest = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_backend": config.model_backend,
        "db_mode": db_mode,
        "storage_backend": config.storage_backend,
        "bucket": config.s3_bucket,
        "prefix": config.s3_prefix,
        "artifacts": entries,
    }

    manifest_path = config.outputs_dir / "artifacts_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    manifest_rel = manifest_path.relative_to(config.repo_root).as_posix()
    manifest_key = f"runs/{run_id}/{manifest_rel}"
    manifest_storage_uri = (
        _build_s3_uri(config.s3_bucket, config.s3_prefix, manifest_key)
        if config.storage_backend == "s3"
        else f"local://{manifest_rel}"
    )
    manifest["artifacts"].append(
        {
            "local_path": manifest_rel,
            "size_bytes": manifest_path.stat().st_size,
            "storage_uri": manifest_storage_uri,
            "s3_key": manifest_key,
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2))

    if config.storage_backend != "s3":
        return

    storage = S3Storage(bucket=config.s3_bucket, region=config.aws_region, prefix=config.s3_prefix)
    for item in entries:
        storage.put_file(config.repo_root / str(item["local_path"]), str(item["s3_key"]))
    storage.put_file(manifest_path, manifest_key, content_type="application/json")

    logger.info(
        json.dumps(
            {
                "event": "s3_artifacts_published",
                "run_id": run_id,
                "bucket": config.s3_bucket,
                "artifact_count": len(entries) + 1,
            }
        )
    )


def run_pipeline(demo_mode: bool) -> None:
    config = load_config(demo_mode=demo_mode)
    ensure_directories(config)

    logger.info("Starting pipeline")
    db = get_database_client(config)
    initialize_schema(config, db)

    student_info, student_assessment, assessments = extract_data(config)
    clean_df = transform_data(student_info, student_assessment, assessments)
    load_processed_data(clean_df, config, db)

    features = build_time_sliced_features(clean_df)
    model, X_train, y_train, X_test, y_test, model_metadata = train_model(features, config)
    metrics = evaluate_model(
        model,
        X_test,
        y_test,
        config,
        backend_hyperparams=model_metadata["backend_hyperparams"],
    )
    top_features = generate_shap_artifacts(model, X_train, y_train, config)

    latest_predictions = predict_latest_risk(
        model, features, config.current_week, config.high_risk_threshold
    )
    latest_predictions.to_csv(config.outputs_dir / "predictions_latest.csv", index=False)

    build_marts(latest_predictions, config, db)
    generate_alert(latest_predictions, features, config, db)
    _, _, roi_df = run_ab_simulation(latest_predictions, config, db)

    roi_topline = roi_df.sort_values("roi", ascending=False).iloc[0].to_dict()
    write_executive_summary(metrics, roi_topline, demo_mode=demo_mode)
    publish_artifacts_manifest(config, db_mode=db.driver)

    logger.info("Pipeline completed successfully")
    logger.info(
        json.dumps(
            {
                "metrics": metrics,
                "top_shap_features": top_features,
                "best_roi": roi_topline,
                "model_backend": config.model_backend,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OULAD end-to-end pipeline")
    parser.add_argument("--demo", action="store_true", help="Force demo mode with synthetic data")
    args = parser.parse_args()
    run_pipeline(demo_mode=args.demo)
