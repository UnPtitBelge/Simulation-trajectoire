"""Wrappers pour les modèles de prédiction de pas (step models).

Les deux modèles apprennent les résidus Δs = feat(s_{t+1}) - feat(s_t)
plutôt que l'état absolu. Avantages :
  - Les deltas sont ~100× plus petits (dt = 0.01 s), plus faciles à apprendre.
  - Les erreurs de prédiction s'accumulent moins vite sur de longues séquences.

Entraînement incrémental :
  - LinearStepModel  : Ridge via équations normales (XtX / Xty) → exact, stable
  - MLPStepModel     : MLPRegressor(warm_start=True, max_iter=1) → 1 epoch par
                       appel fit(), la boucle externe gère shuffle + early stopping

Scalers : calibrés sur un échantillon uniforme de tous les chunks via
fit_shared_scalers() dans train.py, puis injectés avec inject_scalers()
avant le premier partial_fit(). Garantit des stats de normalisation
représentatives de l'ensemble des données, indépendamment de l'ordre des chunks.
"""

import pickle
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


N_FEATURES = 9  # (r, cosθ, sinθ, vr, vθ, vθ²/r, vr·vθ/r, sinθ·vθ/r, cosθ·vθ/r)


def _clip_state(state: np.ndarray) -> np.ndarray:
    """Empêche r < 0 (non physique). La butée au r_min physique est gérée
    par predict_trajectory, pas ici — sinon _clip_state bloque la condition
    d'arrêt en maintenant r > r_min en permanence."""
    if state[0] < 0.0:
        state = state.copy()
        state[0] = 0.0
        state[2] = max(state[2], 0.0)
    return state


def state_to_features(state: np.ndarray) -> np.ndarray:
    """(r, θ, vr, vθ) → 9 features. Fonctionne sur batches.

    Les 3 features supplémentaires sont les produits croisés manquants pour la LR :

      vθ²/r     — terme centrifuge dans Δvr
      vr·vθ/r   — terme de Coriolis dans Δvθ  (= −Δvθ/dt sans friction)
      sinθ·vθ/r — couplage angulaire dans Δcosθ (= −Δcosθ/dt)
      cosθ·vθ/r — couplage angulaire dans Δsinθ (=  Δsinθ/dt)

    Sans ces produits, la LR ne peut qu'approximer ces termes à partir de features
    séparées, ce qui crée une boucle de rétroaction oscillante en prédiction récursive.

    features_to_state ignore les features 5-8 (quantités dérivées recomputées).
    """
    r, theta, vr, vtheta = state[..., 0], state[..., 1], state[..., 2], state[..., 3]
    r_safe = np.maximum(r, 1e-6)
    centrifugal   = vtheta ** 2 / r_safe
    coriolis      = vr * vtheta  / r_safe
    dcos_coeff    = np.sin(theta) * vtheta / r_safe
    dsin_coeff    = np.cos(theta) * vtheta / r_safe
    return np.stack(
        [r, np.cos(theta), np.sin(theta), vr, vtheta,
         centrifugal, coriolis, dcos_coeff, dsin_coeff],
        axis=-1,
    )


def features_to_state(features: np.ndarray) -> np.ndarray:
    """(r, cos θ, sin θ, vr, vθ) → (r, θ, vr, vθ)."""
    r       = features[..., 0]
    theta   = np.arctan2(features[..., 2], features[..., 1])
    vr      = features[..., 3]
    vtheta  = features[..., 4]
    return np.stack([r, theta, vr, vtheta], axis=-1)


class LinearStepModel:
    """Régression linéaire multi-sortie via équations normales incrémentales (Ridge).

    Accumule XtX et Xty par chunk, puis résout W = (XtX + λI)⁻¹ Xty au moment
    de la première prédiction. Avantage sur SGDRegressor : solution optimale exacte,
    pas de taux d'apprentissage décroissant, pas d'oscillations en prédiction récursive.
    """

    def __init__(self, alpha: float = 1e-3):
        self.alpha = alpha
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self._scaler_fitted = False
        # +1 pour le terme de biais
        self._XtX = np.zeros((N_FEATURES + 1, N_FEATURES + 1))
        self._Xty = np.zeros((N_FEATURES + 1, N_FEATURES))
        self._W: np.ndarray | None = None  # (N_FEATURES+1, N_FEATURES), résolu à la demande

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Accumule les statistiques suffisantes (XtX, Xty) pour un chunk."""
        residuals = y - X
        if not self._scaler_fitted:
            self.scaler_X.fit(X)
            self.scaler_y.fit(residuals)
            self._scaler_fitted = True
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(residuals)
        Xb = np.hstack([Xs, np.ones((Xs.shape[0], 1), dtype=Xs.dtype)])
        self._XtX += Xb.T @ Xb
        self._Xty += Xb.T @ ys
        self._W = None  # invalide la solution précédente

    def inject_scalers(self, scaler_X: "StandardScaler", scaler_y: "StandardScaler") -> None:
        """Injecte des scalers pré-fittés (calculés sur l'ensemble des données).
        Doit être appelé avant partial_fit() pour que la normalisation soit
        représentative de la distribution globale et non du seul premier chunk."""
        self.scaler_X = scaler_X
        self.scaler_y = scaler_y
        self._scaler_fitted = True

    def _finalize(self) -> None:
        """Résout le système normal W = (XtX + λI)⁻¹ Xty."""
        A = self._XtX.copy()
        # Régularisation sur les features uniquement (pas sur le biais)
        A[:N_FEATURES, :N_FEATURES] += self.alpha * np.eye(N_FEATURES)
        self._W = np.linalg.solve(A, self._Xty)

    def val_loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """MSE en espace normalisé — finalise W si besoin (pour reporting)."""
        if self._W is None:
            self._finalize()
        residuals = y - X
        Xs = self.scaler_X.transform(X)
        Xb = np.hstack([Xs, np.ones((Xs.shape[0], 1), dtype=Xs.dtype)])
        pred_s = Xb @ self._W
        ys = self.scaler_y.transform(residuals)
        return float(np.mean((pred_s - ys) ** 2))

    def predict_step(self, state: np.ndarray) -> np.ndarray:
        """Prédit l'état (r, θ, vr, vθ) suivant depuis l'état courant."""
        if not hasattr(self, "_XtX"):
            raise RuntimeError(
                "Modèle .pkl généré avec l'ancienne implémentation SGD — "
                "relancer scripts/train_models.py"
            )
        if not hasattr(self, "scaler_X") or not getattr(self, "_scaler_fitted", False):
            raise RuntimeError("Modèle non entraîné — appeler partial_fit() d'abord")
        if not hasattr(self, "_W") or self._W is None:
            self._finalize()
        feat = state_to_features(state).reshape(1, -1)
        feat_s = self.scaler_X.transform(feat)
        Xb = np.hstack([feat_s, [[1.0]]])
        delta_s = Xb @ self._W
        delta = self.scaler_y.inverse_transform(delta_s)[0]
        if np.isnan(delta).any() or np.isinf(delta).any():
            raise RuntimeError(f"Prédiction instable (NaN/Inf dans delta) à state={state}")
        return _clip_state(features_to_state(feat[0] + delta))

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "LinearStepModel":
        with open(path, "rb") as f:
            return pickle.load(f)


class MLPStepModel:
    """MLP multi-sortie via MLPRegressor (Adam, warm_start, 1 epoch par appel).

    Apprend les résidus Δs = s_{t+1} - s_{t} (espace features).
    Stratégie : max_iter=1 → chaque appel à partial_fit() fait exactement
    1 epoch sur le chunk courant ; la boucle d'entraînement externe gère
    le shuffle des chunks entre epochs et l'early stopping sur validation.
    """

    def __init__(self):
        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 32),   # réduit : résidus = problème plus simple
            activation="relu",
            solver="adam",                 # Adam : adaptatif par paramètre, stable sur grands datasets
            learning_rate_init=1e-3,       # lr Adam standard
            alpha=0.001,                   # L2 renforcé pour limiter la dérive
            max_iter=1,                    # 1 epoch par appel ; la boucle externe contrôle le reste
            warm_start=True,               # conserve les poids entre chunks
            random_state=0,
        )
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self._scaler_fitted = False

    def inject_scalers(self, scaler_X: StandardScaler, scaler_y: StandardScaler) -> None:
        """Injecte des scalers pré-fittés (calculés sur l'ensemble des données).
        Doit être appelé avant partial_fit() pour que la normalisation soit
        représentative de la distribution globale et non du seul premier chunk."""
        self.scaler_X = scaler_X
        self.scaler_y = scaler_y
        self._scaler_fitted = True

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Entraîne 1 epoch sur le chunk courant en continuant depuis les poids existants.
        Le modèle apprend les résidus Δ = y - X.
        ConvergenceWarning supprimé : avec max_iter=1, la non-convergence est attendue."""
        import warnings
        from sklearn.exceptions import ConvergenceWarning

        residuals = y - X
        if not self._scaler_fitted:
            self.scaler_X.fit(X)
            self.scaler_y.fit(residuals)
            self._scaler_fitted = True
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(residuals)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            self.model.fit(Xs, ys)

    def val_loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """MSE en espace normalisé — pour l'early stopping et le reporting."""
        residuals = y - X
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(residuals)
        pred = self.model.predict(Xs)
        return float(np.mean((pred - ys) ** 2))

    def predict_step(self, state: np.ndarray) -> np.ndarray:
        if not hasattr(self, "scaler_X") or not getattr(self, "_scaler_fitted", False):
            raise RuntimeError("Modèle non entraîné — appeler partial_fit() d'abord")
        feat = state_to_features(state).reshape(1, -1)
        feat_s = self.scaler_X.transform(feat)
        delta_s = self.model.predict(feat_s)
        delta = self.scaler_y.inverse_transform(delta_s)[0]
        if np.isnan(delta).any() or np.isinf(delta).any():
            raise RuntimeError(f"Prédiction instable (NaN/Inf dans delta) à state={state}")
        return _clip_state(features_to_state(feat[0] + delta))

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "MLPStepModel":
        with open(path, "rb") as f:
            return pickle.load(f)
