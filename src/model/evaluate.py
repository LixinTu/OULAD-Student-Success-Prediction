"""Model evaluation utilities."""

from __future__ import annotations

import json

import numpy as np
from sklearn.metrics import auc, confusion_matrix, precision_recall_curve, roc_auc_score

from src.config import PipelineConfig


def evaluate_model(
    model: object,
    X_test,
    y_test,
    config: PipelineConfig,
    backend_hyperparams: dict,
) -> dict:
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    precision, recall, _ = precision_recall_curve(y_test, probs)
    metrics = {
        "auc": float(roc_auc_score(y_test, probs)),
        "pr_auc": float(auc(recall, precision)),
        "precision_at_0_5": float(
            np.sum((preds == 1) & (y_test == 1)) / max(np.sum(preds == 1), 1)
        ),
        "recall_at_0_5": float(np.sum((preds == 1) & (y_test == 1)) / max(np.sum(y_test == 1), 1)),
        "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
        "model_backend": config.model_backend,
        "backend_hyperparams": backend_hyperparams,
    }
    (config.outputs_dir / "metrics_latest.json").write_text(json.dumps(metrics, indent=2))
    return metrics
