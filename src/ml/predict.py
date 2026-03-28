"""Prédiction de trajectoire par itération du modèle step-by-step.

L'état interne est (r, θ, vr, vθ). Le modèle est appelé à chaque pas
pour prédire l'état suivant. Pas de dépendance Qt.
"""

import numpy as np

from ml.models import LinearStepModel, MLPStepModel


_V_STOP = 2e-3  # seuil vitesse (m/s) — aligné sur g_friction×dt ≈ 0.002 m/s du simulateur


def predict_trajectory(
    model: "LinearStepModel | MLPStepModel",
    init_state: np.ndarray,
    n_steps: int,
    r_max: float | None = None,
    r_min: float | None = None,
) -> np.ndarray:
    """Prédit n_steps états successifs depuis init_state = (r, θ, vr, vθ).

    Retourne array (≤ n_steps, 4) en coordonnées polaires (r, θ, vr, vθ).
    Conditions d'arrêt anticipé (miroir de compute_cone) :
      1. r >= r_max  — bille sortie du bord
      2. r <= r_min  — collision avec la bille centrale
      3. |v| < _V_STOP — bille arrêtée (frottement)
      4. n_steps atteint
    Le calcul est purement numpy, sans interaction Qt.
    """
    traj = np.empty((n_steps, 4))
    state = init_state.astype(float).copy()

    for i in range(n_steps):
        traj[i] = state
        if r_max is not None and state[0] >= r_max:
            return traj[:i + 1]
        if r_min is not None and state[0] <= r_min:
            return traj[:i + 1]
        if np.sqrt(state[2] ** 2 + state[3] ** 2) < _V_STOP:
            return traj[:i + 1]
        state = model.predict_step(state)

    return traj
