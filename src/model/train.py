"""Model training module with backend-agnostic time-aware split."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.config import PipelineConfig
from src.model.train_sklearn import train_sklearn

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


def _get_backend_trainer(backend: str):
    if backend == "sklearn":
        return train_sklearn
    if backend == "pytorch":
        try:
            from src.model.train_torch import train_torch
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "MODEL_BACKEND=pytorch requires PyTorch. Install optional dependencies with: "
                "pip install -r requirements-pt.txt"
            ) from exc
        return train_torch
    if backend == "tensorflow":
        try:
            from src.model.train_tf import train_tf
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "MODEL_BACKEND=tensorflow requires TensorFlow. Install optional dependencies with: "
                "pip install -r requirements-tf.txt"
            ) from exc
        return train_tf

    raise ValueError(
        f"Unsupported MODEL_BACKEND='{backend}'. "
        "Valid options: ['pytorch', 'sklearn', 'tensorflow']"
    )


def train_model(
    features: pd.DataFrame, config: PipelineConfig
) -> tuple[object, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, dict]:
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

    trainer = _get_backend_trainer(config.model_backend)
    try:
        model, backend_params = trainer(X_train, y_train, config.random_seed, config.demo_mode)
    except ImportError as exc:
        if config.model_backend == "pytorch":
            raise ImportError(
                "PyTorch backend not available. Install with: pip install -r requirements-pt.txt"
            ) from exc
        if config.model_backend == "tensorflow":
            raise ImportError(
                "TensorFlow backend not available. Install with: pip install -r requirements-tf.txt"
            ) from exc
        raise

    if config.model_backend == "sklearn":
        joblib.dump(model, config.models_dir / "risk_model.joblib")

    metadata = {
        "model_backend": config.model_backend,
        "feature_columns": FEATURE_COLS,
        "random_seed": config.random_seed,
        "split_week": split_week,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "backend_hyperparams": backend_params,
    }
    Path(config.models_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2))
    return model, X_train, y_train, X_test, y_test, metadata
