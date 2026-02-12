"""Explainability output generation."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import shap
from sklearn.inspection import permutation_importance

from src.config import PipelineConfig


def _generate_shap_top_features(
    model: object, X_train: pd.DataFrame, config: PipelineConfig
) -> dict:
    sample = X_train.sample(n=min(200, len(X_train)), random_state=config.random_seed)
    if hasattr(model, "scaler") and hasattr(model, "model"):
        sample_scaled = pd.DataFrame(model.scaler.transform(sample), columns=sample.columns)
        explainer = shap.Explainer(model.model, sample_scaled)
        shap_values = explainer(sample_scaled)
    else:
        explainer = shap.Explainer(model, sample)
        shap_values = explainer(sample)

    plt.figure(figsize=(8, 5))
    shap.plots.beeswarm(shap_values, max_display=10, show=False)
    out_png = config.outputs_dir / "shap_summary.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()

    mean_abs = pd.Series(abs(shap_values.values).mean(axis=0), index=sample.columns).sort_values(
        ascending=False
    )
    return mean_abs.head(10).to_dict()


def _generate_permutation_top_features(
    model: object, X_train: pd.DataFrame, y_train: pd.Series, config: PipelineConfig
) -> dict:
    result = permutation_importance(
        model,
        X_train,
        y_train,
        n_repeats=10,
        random_state=config.random_seed,
        scoring="roc_auc",
    )
    importances = pd.Series(result.importances_mean, index=X_train.columns).sort_values(
        ascending=False
    )
    return importances.head(10).to_dict()


def generate_shap_artifacts(
    model: object,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    config: PipelineConfig,
) -> dict:
    if config.model_backend == "sklearn":
        top_features = _generate_shap_top_features(model, X_train, config)
    else:
        top_features = _generate_permutation_top_features(model, X_train, y_train, config)

    out_json = config.outputs_dir / "shap_top_features.json"
    out_json.write_text(json.dumps(top_features, indent=2))
    return top_features
