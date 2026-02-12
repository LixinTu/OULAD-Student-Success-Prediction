"""PyTorch backend training."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


@dataclass
class TorchRiskModel:
    model: object
    scaler: StandardScaler
    torch: object

    def predict_proba(self, X: pd.DataFrame):
        X_scaled = self.scaler.transform(X).astype(np.float32)
        self.model.eval()
        with self.torch.no_grad():
            logits = self.model(self.torch.tensor(X_scaled))
            probs = self.torch.sigmoid(logits).cpu().numpy().reshape(-1)
        return np.column_stack([1 - probs, probs])


def train_torch(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    random_seed: int,
    demo_mode: bool = False,
):
    import torch
    import torch.nn as nn

    torch.manual_seed(random_seed)
    np.random.seed(random_seed)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train).astype(np.float32)
    y_train_arr = y_train.values.astype(np.float32).reshape(-1, 1)

    class MLP(nn.Module):
        def __init__(self, in_features: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(in_features, 32),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(32, 16),
                nn.ReLU(),
                nn.Linear(16, 1),
            )

        def forward(self, x):
            return self.net(x)

    model = MLP(X_train.shape[1])
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    X_tensor = torch.tensor(X_train_scaled)
    y_tensor = torch.tensor(y_train_arr)

    epochs = 3 if demo_mode else 60
    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(X_tensor)
        loss = loss_fn(logits, y_tensor)
        loss.backward()
        optimizer.step()

    params = {
        "model_type": "TorchMLPClassifier",
        "hidden_layers": [32, 16],
        "dropout": 0.1,
        "optimizer": "Adam",
        "lr": 1e-3,
        "epochs": epochs,
        "random_seed": random_seed,
    }
    return TorchRiskModel(model=model, scaler=scaler, torch=torch), params
