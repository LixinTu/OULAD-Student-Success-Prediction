"""Build BI-ready marts from model outputs."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.config import PipelineConfig
from src.etl.load import DBClient


def build_marts(
    predictions: pd.DataFrame, config: PipelineConfig, db: DBClient
) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_ts = datetime.utcnow().replace(microsecond=0)
    run_date = run_ts.date().isoformat()
    student_risk_daily = predictions[
        [
            "id_student",
            "code_module",
            "week",
            "risk_score",
            "high_risk_flag",
            "weekly_score_mean",
            "cum_submissions",
        ]
    ].copy()
    student_risk_daily["run_date"] = run_date
    student_risk_daily = student_risk_daily[
        [
            "run_date",
            "id_student",
            "code_module",
            "week",
            "risk_score",
            "high_risk_flag",
            "weekly_score_mean",
            "cum_submissions",
        ]
    ]

    course_summary_daily = (
        student_risk_daily.groupby(["run_date", "week", "code_module"], as_index=False)
        .agg(
            student_count=("id_student", "nunique"),
            avg_risk_score=("risk_score", "mean"),
            high_risk_rate=("high_risk_flag", "mean"),
        )
        .sort_values(["week", "high_risk_rate"], ascending=[True, False])
    )

    db.insert_df("student_risk_daily", student_risk_daily)
    db.insert_df("course_summary_daily", course_summary_daily)

    if db.driver == "postgres":
        model_scores = student_risk_daily[
            [
                "run_date",
                "week",
                "id_student",
                "code_module",
                "risk_score",
                "high_risk_flag",
            ]
        ].copy()
        model_scores["run_date"] = run_ts.isoformat()
        model_scores["model_version"] = "v1"
        model_scores["model_backend"] = config.model_backend
        model_scores["threshold"] = config.high_risk_threshold
        model_scores["created_at"] = run_ts.isoformat()
        db.insert_df("ml.student_risk_scores", model_scores)

    student_risk_daily.head(500).to_csv(
        config.marts_dir / "student_risk_daily_sample.csv", index=False
    )
    course_summary_daily.to_csv(config.marts_dir / "course_summary_daily_sample.csv", index=False)
    return student_risk_daily, course_summary_daily
