"""TensorFlow backend training."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


@dataclass
class TensorFlowRiskModel:
    model: object
    scaler: StandardScaler

    def predict_proba(self, X: pd.DataFrame):
        X_scaled = self.scaler.transform(X)
        probs = self.model.predict(X_scaled, verbose=0).reshape(-1)
        return np.column_stack([1 - probs, probs])


def train_tf(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    random_seed: int,
    demo_mode: bool = False,
):
    import tensorflow as tf

    tf.random.set_seed(random_seed)
    np.random.seed(random_seed)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(X_train.shape[1],)),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
    )
    epochs = 3 if demo_mode else 40
    model.fit(X_train_scaled, y_train.values, epochs=epochs, batch_size=64, verbose=0)

    params = {
        "model_type": "KerasMLPClassifier",
        "hidden_layers": [32, 16],
        "dropout": 0.1,
        "optimizer": "Adam",
        "lr": 1e-3,
        "epochs": epochs,
        "batch_size": 64,
        "random_seed": random_seed,
    }
    return TensorFlowRiskModel(model=model, scaler=scaler), params
