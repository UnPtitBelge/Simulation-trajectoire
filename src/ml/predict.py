"""Prédiction de trajectoire par itération du modèle step-by-step.

L'état interne est (r, θ, vr, vθ). Le modèle est appelé à chaque pas
pour prédire l'état suivant. Pas de dépendance Qt.

Fonctions exportées :
  predict_trajectory    — prédiction seule (signature stable, appelée par l'UI)
  predict_with_errors   — prédiction + erreur par pas vs une trajectoire de référence
                          (pour les scripts d'analyse scientifique)
"""

import numpy as np

from ml.models import LinearStepModel, MLPStepModel


_V_STOP_DEFAULT = 2e-3  # seuil vitesse — en m/s pour le mode synth, en px/frame pour le mode réel


def predict_trajectory(
    model: "LinearStepModel | MLPStepModel",
    init_state: np.ndarray,
    n_steps: int,
    r_max: float | None = None,
    r_min: float | None = None,
    v_stop: float = _V_STOP_DEFAULT,
) -> np.ndarray:
    """Prédit n_steps états successifs depuis init_state = (r, θ, vr, vθ).

    Retourne array (≤ n_steps, 4) en coordonnées polaires (r, θ, vr, vθ).
    Conditions d'arrêt anticipé (miroir de compute_cone) :
      1. r >= r_max  — bille sortie du bord
      2. r <= r_min  — collision avec la bille centrale
      3. |v| < v_stop — bille arrêtée (frottement) ; lire depuis [synth.physics].v_stop
      4. n_steps atteint
    Le calcul est purement numpy, sans interaction Qt.
    """
    traj = np.empty((n_steps, 4))
    state = init_state.astype(float).copy()

    for i in range(n_steps):
        traj[i] = state
        state = model.predict_step(state)
        # Conditions d'arrêt vérifiées sur le nouvel état (miroir de compute_cone
        # qui teste r/speed après la mise à jour de position/vitesse).
        if r_max is not None and state[0] >= r_max:
            return traj[:i + 1]
        if r_min is not None and state[0] <= r_min:
            return traj[:i + 1]
        if np.sqrt(state[2] ** 2 + state[3] ** 2) < v_stop:
            return traj[:i + 1]

    return traj


def predict_with_errors(
    model: "LinearStepModel | MLPStepModel",
    init_state: np.ndarray,
    reference_traj: np.ndarray,
    **kwargs,
) -> tuple[np.ndarray, np.ndarray]:
    """Prédit une trajectoire et calcule l'erreur absolue par rapport à une référence.

    Paramètres
    ----------
    model          : modèle entraîné (LinearStepModel ou MLPStepModel)
    init_state     : état initial (r, θ, vr, vθ)
    reference_traj : trajectoire de référence (N, 4) — typiquement la simulation physique
    **kwargs       : forwarded to predict_trajectory (r_max, r_min, v_stop)

    Retourne
    --------
    traj   : trajectoire prédite (M, 4), M ≤ N
    errors : erreurs absolues (min(M,N), 4) = |pred - ref| sur (r, θ, vr, vθ)
             La colonne 0 (erreur sur r) est la métrique principale pour les plots.
    """
    n_steps = len(reference_traj)
    traj = predict_trajectory(model, init_state, n_steps, **kwargs)
    n = min(len(traj), n_steps)
    errors = np.abs(traj[:n] - reference_traj[:n])
    return traj, errors
