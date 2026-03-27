"""Wrappers pour les modèles de prédiction de pas (step models).

Les deux modèles prédisent l'état (r, cos θ, sin θ, vr, vθ) au pas t+1
depuis l'état au pas t. L'utilisation de (cos θ, sin θ) évite les
discontinuités de θ lors de l'entraînement.

Entraînement incrémental :
  - LinearStepModel  : MultiOutputRegressor(SGDRegressor) → partial_fit()
  - MLPStepModel     : MLPRegressor(warm_start=True) → fit() batch par batch

Les scalers sont inclus dans chaque modèle (fit sur le 1er chunk).
"""

import pickle
from pathlib import Path

import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


N_FEATURES = 5  # (r, cos θ, sin θ, vr, vθ)
_R_MIN = 0.05   # rayon minimal physique (centre du cône)


def _clip_state(state: np.ndarray) -> np.ndarray:
    """Clippe r à [_R_MIN, +inf) et reflète vr si nécessaire."""
    if state[0] < _R_MIN:
        state = state.copy()
        state[0] = _R_MIN
        state[2] = max(state[2], 0.0)  # vr ≥ 0 au bord intérieur
    return state


def state_to_features(state: np.ndarray) -> np.ndarray:
    """(r, θ, vr, vθ) → (r, cos θ, sin θ, vr, vθ). Fonctionne sur batches."""
    r, theta, vr, vtheta = state[..., 0], state[..., 1], state[..., 2], state[..., 3]
    return np.stack([r, np.cos(theta), np.sin(theta), vr, vtheta], axis=-1)


def features_to_state(features: np.ndarray) -> np.ndarray:
    """(r, cos θ, sin θ, vr, vθ) → (r, θ, vr, vθ)."""
    r       = features[..., 0]
    theta   = np.arctan2(features[..., 2], features[..., 1])
    vr      = features[..., 3]
    vtheta  = features[..., 4]
    return np.stack([r, theta, vr, vtheta], axis=-1)


class LinearStepModel:
    """Régression linéaire multi-sortie via SGDRegressor (supporte partial_fit)."""

    def __init__(self):
        self.model = MultiOutputRegressor(
            SGDRegressor(loss="squared_error", max_iter=1000, tol=1e-4, random_state=0)
        )
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self._scaler_fitted = False

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Entraînement incrémental sur un chunk.  X et y sont des features brutes."""
        if not self._scaler_fitted:
            self.scaler_X.fit(X)
            self.scaler_y.fit(y)
            self._scaler_fitted = True
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(y)
        self.model.partial_fit(Xs, ys)

    def predict_step(self, state: np.ndarray) -> np.ndarray:
        """Prédit l'état (r, θ, vr, vθ) suivant depuis l'état courant."""
        feat = state_to_features(state).reshape(1, -1)
        feat_s = self.scaler_X.transform(feat)
        pred_s = self.model.predict(feat_s)
        pred = self.scaler_y.inverse_transform(pred_s)[0]
        return _clip_state(features_to_state(pred))

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "LinearStepModel":
        with open(path, "rb") as f:
            return pickle.load(f)


class MLPStepModel:
    """MLP multi-sortie via MLPRegressor (warm_start pour entraînement incrémental)."""

    def __init__(self):
        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 64),
            activation="relu",
            max_iter=10,          # peu d'epochs par batch
            warm_start=True,      # continue depuis les poids précédents
            random_state=0,
            n_iter_no_change=10,
        )
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self._scaler_fitted = False

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Entraîne sur un chunk en continuant depuis les poids existants."""
        if not self._scaler_fitted:
            self.scaler_X.fit(X)
            self.scaler_y.fit(y)
            self._scaler_fitted = True
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(y)
        self.model.fit(Xs, ys)

    def predict_step(self, state: np.ndarray) -> np.ndarray:
        feat = state_to_features(state).reshape(1, -1)
        feat_s = self.scaler_X.transform(feat)
        pred_s = self.model.predict(feat_s)
        pred = self.scaler_y.inverse_transform(pred_s)[0]
        return _clip_state(features_to_state(pred))

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "MLPStepModel":
        with open(path, "rb") as f:
            return pickle.load(f)
