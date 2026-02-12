"""Build BI-ready marts from model outputs."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.config import PipelineConfig
from src.etl.load import DBClient


def build_marts(
    latest_predictions: pd.DataFrame, config: PipelineConfig, db: DBClient
) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_date = datetime.utcnow().date().isoformat()
    student_risk_daily = latest_predictions[
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
        student_risk_daily.groupby(["run_date", "code_module"], as_index=False)
        .agg(
            student_count=("id_student", "nunique"),
            avg_risk_score=("risk_score", "mean"),
            high_risk_rate=("high_risk_flag", "mean"),
        )
        .sort_values("high_risk_rate", ascending=False)
    )

    db.insert_df("student_risk_daily", student_risk_daily)
    db.insert_df("course_summary_daily", course_summary_daily)

    student_risk_daily.head(500).to_csv(
        config.marts_dir / "student_risk_daily_sample.csv", index=False
    )
    course_summary_daily.to_csv(config.marts_dir / "course_summary_daily_sample.csv", index=False)
    return student_risk_daily, course_summary_daily
