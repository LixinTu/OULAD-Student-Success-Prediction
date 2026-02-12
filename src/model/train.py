"""Model training module with time-aware split."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.config import PipelineConfig

FEATURE_COLS = [
    "weekly_score_mean",
    "weekly_submissions",
    "studied_credits",
    "age_band_num",
    "imd_band_num",
    "disability_flag",
    "cum_submissions",
    "rolling_score_3w",
    "score_trend_2w",
]


def train_model(
    features: pd.DataFrame, config: PipelineConfig
) -> tuple[object, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    model_df = features.dropna(subset=FEATURE_COLS + ["target_high_risk"]).copy()

    split_week = min(config.split_week, int(model_df["week"].max()))
    train_df = model_df[model_df["week"] < split_week]
    test_df = model_df[model_df["week"] >= split_week]
    if train_df.empty or test_df.empty:
        split_week = int(model_df["week"].quantile(0.7))
        train_df = model_df[model_df["week"] < split_week]
        test_df = model_df[model_df["week"] >= split_week]

    X_train, y_train = train_df[FEATURE_COLS], train_df["target_high_risk"]
    X_test, y_test = test_df[FEATURE_COLS], test_df["target_high_risk"]

    model = LogisticRegression(max_iter=1000, random_state=config.random_seed)
    model.fit(X_train, y_train)

    joblib.dump(model, config.models_dir / "risk_model.joblib")
    metadata = {
        "model_type": "LogisticRegression",
        "feature_columns": FEATURE_COLS,
        "random_seed": config.random_seed,
        "split_week": split_week,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
    }
    Path(config.models_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2))
    return model, X_train, y_train, X_test, y_test
