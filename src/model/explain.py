"""SHAP explainability output generation."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import shap

from src.config import PipelineConfig


def generate_shap_artifacts(model: object, X_train: pd.DataFrame, config: PipelineConfig) -> dict:
    sample = X_train.sample(n=min(200, len(X_train)), random_state=config.random_seed)
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
    top_features = mean_abs.head(10).to_dict()
    out_json = config.outputs_dir / "shap_top_features.json"
    out_json.write_text(json.dumps(top_features, indent=2))
    return top_features
