"""Prediction utilities for latest student risk snapshots."""

from __future__ import annotations

import pandas as pd

from src.model.train import FEATURE_COLS


def predict_latest_risk(
    model: object, features: pd.DataFrame, current_week: int, high_risk_threshold: float
) -> pd.DataFrame:
    latest = features[features["week"] == current_week].copy()
    if latest.empty:
        latest = features.sort_values("week").groupby("id_student", as_index=False).tail(1)
    latest["risk_score"] = model.predict_proba(latest[FEATURE_COLS])[:, 1]
    latest["high_risk_flag"] = (latest["risk_score"] >= high_risk_threshold).astype(int)
    latest = latest.sort_values("risk_score", ascending=False)
    return latest
