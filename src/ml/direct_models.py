"""Modèles directs CI → trajectoire complète.

Contrairement aux step models (LinearStepModel, MLPStepModel) qui apprennent
le résidu Δs pas-à-pas, ces modèles prédisent la **trajectoire entière** en
une seule inférence depuis les conditions initiales :

  Entrée : ci_to_features(état_0) = (r₀, cos θ₀, sin θ₀, vr₀, vθ₀)  — 5 scalaires
  Sortie : trajectoire aplatie (r₀, θ₀, vr₀, vθ₀, r₁, θ₁, …)         — 4 × target_len

Avantage  : pas d'accumulation d'erreur récursive — erreur bornée même sur
            de longues séquences.
Limitation : taille de sortie fixe (target_len pas) — impossible de prédire
             au-delà. Avec peu de données, Ridge surpasse MLP car le problème
             est sous-déterminé (haute dimension, peu d'exemples).

Classes exportées :
  ci_to_features      — encodage des conditions initiales (5 features)
  DirectModelBase     — ABC commun (fit, predict, save, load)
  DirectLinearModel   — Ridge (sklearn), solution exacte
  DirectMLPModel      — MLPRegressor (sklearn), avec early stopping
"""

import pickle
import warnings
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


N_CI_FEATURES = 5  # (r, cos θ, sin θ, vr, vθ)


def ci_to_features(state: np.ndarray) -> np.ndarray:
    """(r, θ, vr, vθ) → (r, cos θ, sin θ, vr, vθ) — 5 features pour les CI.

    Encode θ comme (cos θ, sin θ) pour éviter la discontinuité à ±π et
    permettre à la régression linéaire de capturer les symétries polaires.
    Fonctionne sur un état 1-D (4,) comme sur un batch (N, 4).
    """
    state = np.asarray(state, dtype=np.float32)
    if state.ndim == 1:
        r, theta, vr, vtheta = state[0], state[1], state[2], state[3]
        return np.array([r, np.cos(theta), np.sin(theta), vr, vtheta], dtype=np.float32)
    # batch (N, 4)
    r, theta, vr, vtheta = state[:, 0], state[:, 1], state[:, 2], state[:, 3]
    return np.stack(
        [r, np.cos(theta), np.sin(theta), vr, vtheta], axis=-1
    ).astype(np.float32)


class DirectModelBase(ABC):
    """Base commune aux deux modèles directs.

    Fournit :
      - fit(X_ci, Y_traj)  : entraînement complet (pas incrémental)
      - predict(ic)         : prédiction d'une trajectoire depuis un état CI
      - save(path) / load() : sérialisation pickle (même interface que StepModelBase)

    Les sous-classes implémentent _fit_model() et _predict_flat().

    Attributs publics après fit() :
      target_len    : int     — longueur de la trajectoire prédite (pas)
      context       : str     — nom du contexte d'entraînement ("1pct", …)
      n_train       : int     — nombre d'exemples d'entraînement
      mae_r_train   : float   — MAE sur r (train, en mètres ou px selon l'espace)
      scaler_X      : StandardScaler — fitté sur les CI d'entraînement
    """

    def __init__(self, context: str = "") -> None:
        self.context:     str              = context
        self.target_len:  int              = 0
        self.n_train:     int              = 0
        self.mae_r_train: float            = float("nan")
        self.scaler_X:    StandardScaler   = StandardScaler()
        self._fitted:     bool             = False

    def fit(self, X_ci: np.ndarray, Y_traj: np.ndarray) -> None:
        """Entraîne le modèle.

        Paramètres
        ----------
        X_ci   : (N, 5)         — features CI = ci_to_features(état_0) de N trajectoires
        Y_traj : (N, 4×T)       — trajectoires aplaties (r, θ, vr, vθ) × target_len
        """
        if X_ci.shape[0] == 0:
            raise ValueError("X_ci vide — aucune trajectoire d'entraînement valide.")

        self.target_len = Y_traj.shape[1] // 4
        self.n_train    = len(X_ci)

        self.scaler_X.fit(X_ci)
        X_s = self.scaler_X.transform(X_ci)

        self._fit_model(X_s, Y_traj)
        self._fitted = True

        # MAE sur r (indices 0, 4, 8, … dans Y aplati)
        Y_pred = self._predict_batch(X_s)
        r_true = Y_traj[:, 0::4]
        r_pred = Y_pred[:, 0::4]
        self.mae_r_train = float(mean_absolute_error(r_true.flatten(), r_pred.flatten()))

    @abstractmethod
    def _fit_model(self, X_s: np.ndarray, Y_traj: np.ndarray) -> None:
        """Entraîne le modèle interne sur (X normalisé, Y trajectoires)."""

    @abstractmethod
    def _predict_batch(self, X_s: np.ndarray) -> np.ndarray:
        """Prédit Y aplati pour un batch de X normalisés. Retourne (N, 4×target_len)."""

    def predict(self, ic: np.ndarray) -> np.ndarray:
        """Prédit la trajectoire depuis un état initial (r, θ, vr, vθ).

        Retourne array (target_len, 4) en (r, θ, vr, vθ).
        """
        if not self._fitted:
            raise RuntimeError("Modèle non entraîné — appeler fit() d'abord.")
        x = ci_to_features(ic).reshape(1, -1)
        x_s = self.scaler_X.transform(x)
        y_flat = self._predict_batch(x_s)[0]
        return y_flat.reshape(self.target_len, 4)

    def save(self, path: Path) -> None:
        """Sérialise le modèle en pickle (même interface que StepModelBase)."""
        with open(path, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, path: Path) -> "DirectModelBase":
        """Charge un modèle depuis un fichier pickle.

        Supporte l'ancien format dict (avant la refactorisation en classes) :
          {'model': sklearn_model, 'scaler_X': scaler, 'target_len': int,
           'context': str, 'model_type': 'Ridge'|'MLP', 'n_train': int,
           'mae_r_train': float}
        """
        with open(path, "rb") as f:
            obj = pickle.load(f)
        if isinstance(obj, DirectModelBase):
            return obj
        # Ancien format dict — reconstruction
        model_type = obj.get("model_type", "Ridge")
        instance: DirectModelBase
        if model_type == "Ridge":
            instance = DirectLinearModel(context=obj.get("context", ""))
        else:
            instance = DirectMLPModel(context=obj.get("context", ""))
        instance.target_len  = obj["target_len"]
        instance.n_train     = obj["n_train"]
        instance.mae_r_train = obj["mae_r_train"]
        instance.scaler_X    = obj["scaler_X"]
        instance._model      = obj["model"]
        instance._fitted     = True
        return instance


class DirectLinearModel(DirectModelBase):
    """Ridge direct CI → trajectoire complète.

    Résout W = (XᵀX + λI)⁻¹ Xᵀy en une passe sur l'ensemble des données.
    Avantage sur MLP avec peu de données : solution exacte, pas de sur-apprentissage
    sévère même avec une sortie de haute dimension (4 × target_len scalaires).
    """

    def __init__(self, alpha: float = 1.0, context: str = "") -> None:
        super().__init__(context)
        self.alpha  = alpha
        self._model: Ridge | None = None

    def _fit_model(self, X_s: np.ndarray, Y_traj: np.ndarray) -> None:
        self._model = Ridge(alpha=self.alpha)
        self._model.fit(X_s, Y_traj)

    def _predict_batch(self, X_s: np.ndarray) -> np.ndarray:
        return self._model.predict(X_s)


class DirectMLPModel(DirectModelBase):
    """MLP direct CI → trajectoire complète avec early stopping.

    Architecture (64, 32) — même que MLPStepModel pour comparaison équitable.
    early_stopping=True (si assez de données) évite le sur-apprentissage sévère
    inhérent à ce paradigme (haute dimension de sortie, peu d'exemples).
    """

    def __init__(
        self,
        hidden_layer_sizes: tuple = (64, 32),
        alpha: float = 0.01,
        max_iter: int = 500,
        context: str = "",
    ) -> None:
        super().__init__(context)
        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha    = alpha
        self.max_iter = max_iter
        self.n_iter_: int = 0
        self._model: MLPRegressor | None = None

    def _fit_model(self, X_s: np.ndarray, Y_traj: np.ndarray) -> None:
        use_early = len(X_s) >= 10
        self._model = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation="relu",
            solver="adam",
            learning_rate_init=1e-3,
            alpha=self.alpha,
            max_iter=self.max_iter,
            early_stopping=use_early,
            validation_fraction=0.1 if use_early else 0.0,
            n_iter_no_change=15,
            random_state=42,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            self._model.fit(X_s, Y_traj)
        self.n_iter_ = self._model.n_iter_

    def _predict_batch(self, X_s: np.ndarray) -> np.ndarray:
        return self._model.predict(X_s)
