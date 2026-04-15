"""Fixtures partagées pour la suite de tests unitaires."""

import numpy as np
import pytest

from ml.models import LinearStepModel, MLPStepModel, state_to_features
from sklearn.preprocessing import StandardScaler


# ── Paramètres physiques minimaux ────────────────────────────────────────────

@pytest.fixture
def phys_params():
    """Paramètres physiques minimaux pour le cône."""
    return dict(R=0.4, depth=0.09, friction=0.02, g=9.81, dt=0.01,
                n_steps=200, center_radius=0.03)


@pytest.fixture
def membrane_params():
    """Paramètres physiques minimaux pour la membrane."""
    return dict(R=0.4, k=0.035, r_min=0.03, friction=0.02, g=9.81, dt=0.01,
                n_steps=200, center_radius=0.03)


@pytest.fixture
def default_ic():
    """Condition initiale par défaut (orbite quasi-circulaire)."""
    return dict(r0=0.30, theta0=0.0, vr0=0.0, vtheta0=0.7)


# ── Helpers ML ───────────────────────────────────────────────────────────────

def _make_tiny_dataset(n: int = 200, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Génère un mini-dataset (X_features, y_features) depuis des états synthétiques."""
    from physics.cone import compute_cone
    rng = np.random.default_rng(seed)
    r0 = rng.uniform(0.05, 0.38)
    vr0 = rng.uniform(-0.3, 0.3)
    vth0 = rng.uniform(0.3, 1.2)
    traj = compute_cone(r0=r0, theta0=0.0, vr0=vr0, vtheta0=vth0,
                        R=0.4, depth=0.09, friction=0.02, g=9.81,
                        dt=0.01, n_steps=n + 10)
    if len(traj) < 2:
        # Fallback : CI garantissant une trajectoire longue
        traj = compute_cone(r0=0.25, theta0=0.0, vr0=0.0, vtheta0=0.8,
                            R=0.4, depth=0.09, friction=0.02, g=9.81,
                            dt=0.01, n_steps=n + 10)
    X = state_to_features(traj[:-1].astype(np.float32))
    y = state_to_features(traj[1:].astype(np.float32))
    return X[:n], y[:n]


@pytest.fixture
def tiny_dataset():
    """Mini-dataset (X_features, y_features) pour tester les modèles."""
    return _make_tiny_dataset(n=150)


@pytest.fixture
def fitted_linear(tiny_dataset) -> LinearStepModel:
    """LinearStepModel entraîné sur le mini-dataset."""
    X, y = tiny_dataset
    model = LinearStepModel(alpha=1e-3)
    model.partial_fit(X, y)
    return model


@pytest.fixture
def fitted_mlp(tiny_dataset) -> MLPStepModel:
    """MLPStepModel entraîné sur le mini-dataset (1 epoch)."""
    X, y = tiny_dataset
    model = MLPStepModel()
    model.partial_fit(X, y)
    return model


@pytest.fixture
def shared_scalers(tiny_dataset):
    """Scalers StandardScaler fittés sur le mini-dataset."""
    X, y = tiny_dataset
    scaler_X = StandardScaler().fit(X)
    scaler_y = StandardScaler().fit(y - X)
    return scaler_X, scaler_y
