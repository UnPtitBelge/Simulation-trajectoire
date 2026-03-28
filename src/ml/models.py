"""Wrappers pour les modèles de prédiction de pas (step models).

Les deux modèles apprennent les résidus Δs = s_{t+1} - s_{t} (en espace
features) plutôt que l'état absolu. Avantages :
  - Les deltas sont ~100× plus petits (dt = 0.01 s), plus faciles à apprendre.
  - La relation Δr ≈ dt·vr est quasi-linéaire → SGD la capture parfaitement.
  - Les erreurs de prédiction s'accumulent moins vite sur de longues séquences.

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
        """Entraînement incrémental sur un chunk. X et y sont des features brutes.
        Le modèle apprend les résidus Δ = y - X."""
        residuals = y - X
        if not self._scaler_fitted:
            self.scaler_X.fit(X)
            self.scaler_y.fit(residuals)
            self._scaler_fitted = True
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(residuals)
        self.model.partial_fit(Xs, ys)

    def predict_step(self, state: np.ndarray) -> np.ndarray:
        """Prédit l'état (r, θ, vr, vθ) suivant depuis l'état courant."""
        feat = state_to_features(state).reshape(1, -1)
        feat_s = self.scaler_X.transform(feat)
        delta_s = self.model.predict(feat_s)
        delta = self.scaler_y.inverse_transform(delta_s)[0]
        return _clip_state(features_to_state(feat[0] + delta))

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "LinearStepModel":
        with open(path, "rb") as f:
            return pickle.load(f)


class MLPStepModel:
    """MLP multi-sortie via MLPRegressor (warm_start pour entraînement incrémental).

    Apprend les résidus Δs = s_{t+1} - s_{t} (espace features).
    Stratégie : 100 epochs par chunk, early stopping (patience=10),
    LR adaptatif, régularisation L2 renforcée (alpha=0.001).
    """

    def __init__(self):
        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 32),   # réduit : résidus = problème plus simple
            activation="relu",
            alpha=0.001,                   # L2 renforcé pour limiter la dérive
            max_iter=100,                  # convergence réelle par chunk
            warm_start=True,               # conserve les poids entre chunks
            random_state=0,
            n_iter_no_change=10,           # patience early stopping (< max_iter)
            learning_rate="adaptive",      # réduit le LR sur plateau
        )
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self._scaler_fitted = False

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Entraîne sur un chunk en continuant depuis les poids existants.
        Le modèle apprend les résidus Δ = y - X."""
        residuals = y - X
        if not self._scaler_fitted:
            self.scaler_X.fit(X)
            self.scaler_y.fit(residuals)
            self._scaler_fitted = True
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(residuals)
        self.model.fit(Xs, ys)

    def predict_step(self, state: np.ndarray) -> np.ndarray:
        feat = state_to_features(state).reshape(1, -1)
        feat_s = self.scaler_X.transform(feat)
        delta_s = self.model.predict(feat_s)
        delta = self.scaler_y.inverse_transform(delta_s)[0]
        return _clip_state(features_to_state(feat[0] + delta))

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "MLPStepModel":
        with open(path, "rb") as f:
            return pickle.load(f)
