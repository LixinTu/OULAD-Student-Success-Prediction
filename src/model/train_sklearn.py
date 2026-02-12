"""Scikit-learn backend training."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


@dataclass
class SklearnRiskModel:
    model: LogisticRegression
    scaler: StandardScaler

    def predict_proba(self, X: pd.DataFrame):
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)


def train_sklearn(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    random_seed: int,
    demo_mode: bool = False,
):
    del demo_mode
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    model = LogisticRegression(max_iter=1000, random_state=random_seed)
    model.fit(X_train_scaled, y_train)
    params = {
        "model_type": "LogisticRegression",
        "max_iter": 1000,
        "random_seed": random_seed,
    }
    return SklearnRiskModel(model=model, scaler=scaler), params
