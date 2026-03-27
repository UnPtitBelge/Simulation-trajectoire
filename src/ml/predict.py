"""Prédiction de trajectoire par itération du modèle step-by-step.

L'état interne est (r, θ, vr, vθ). Le modèle est appelé à chaque pas
pour prédire l'état suivant. Pas de dépendance Qt.
"""

import numpy as np

from ml.models import LinearStepModel, MLPStepModel


def predict_trajectory(
    model: "LinearStepModel | MLPStepModel",
    init_state: np.ndarray,
    n_steps: int,
    r_max: float | None = None,
) -> np.ndarray:
    """Prédit n_steps états successifs depuis init_state = (r, θ, vr, vθ).

    Retourne array (≤ n_steps, 4) en coordonnées polaires (r, θ, vr, vθ).
    S'arrête tôt si r >= r_max (bille sortie du bord), comme compute_cone.
    Le calcul est purement numpy, sans interaction Qt.
    """
    traj = np.empty((n_steps, 4))
    state = init_state.astype(float).copy()

    for i in range(n_steps):
        traj[i] = state
        if r_max is not None and state[0] >= r_max:
            return traj[:i + 1]
        state = model.predict_step(state)

    return traj
