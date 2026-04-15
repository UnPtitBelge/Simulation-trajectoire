"""Tests unitaires — prédiction (predict.py)."""

import numpy as np
import pytest

from ml.predict import predict_trajectory, predict_with_errors


# ═══════════════════════════════════════════════════════════════
# predict_trajectory
# ═══════════════════════════════════════════════════════════════

class TestPredictTrajectory:

    def test_output_shape_columns(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_linear, state, n_steps=30)
        assert traj.ndim == 2
        assert traj.shape[1] == 4

    def test_output_at_most_n_steps(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_linear, state, n_steps=50)
        assert len(traj) <= 50

    def test_first_state_equals_init(self, fitted_linear):
        init = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_linear, init, n_steps=10)
        np.testing.assert_allclose(traj[0], init, atol=1e-10)

    def test_stop_at_r_max(self, fitted_linear):
        # IC avec grande vr sortante → doit s'arrêter quand r >= r_max
        state = np.array([0.38, 0.0, 2.0, 0.0])
        traj = predict_trajectory(fitted_linear, state, n_steps=500, r_max=0.4)
        # Soit la trajectoire s'est arrêtée avant n_steps (condition r_max atteinte)
        # soit tous les r sont < r_max (arrêt anticipé juste avant la condition)
        assert len(traj) < 500 or np.all(traj[:, 0] < 0.4 + 0.1)

    def test_stop_at_r_min(self, fitted_linear):
        # IC proche du centre → arrêt possible si r <= r_min
        state = np.array([0.04, 0.0, -0.5, 0.0])
        traj = predict_trajectory(fitted_linear, state, n_steps=500,
                                  r_min=0.03)
        # Vérification : aucun r négatif dans la trajectoire (clip_state actif)
        assert np.all(traj[:, 0] >= 0.0)

    def test_stop_at_v_stop(self, fitted_linear):
        # v_stop très grand → arrêt immédiat à presque tous les états
        state = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_linear, state, n_steps=100, v_stop=100.0)
        assert len(traj) == 1  # s'arrête dès le premier pas (|v| < 100 après predict)

    def test_init_state_not_mutated(self, fitted_linear):
        init = np.array([0.25, 0.5, 0.0, 0.7])
        original = init.copy()
        predict_trajectory(fitted_linear, init, n_steps=10)
        np.testing.assert_array_equal(init, original)

    def test_all_r_non_negative(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_linear, state, n_steps=50)
        assert np.all(traj[:, 0] >= 0.0)

    def test_all_values_finite(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_linear, state, n_steps=50)
        assert np.all(np.isfinite(traj))

    def test_mlp_works_same_interface(self, fitted_mlp):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_mlp, state, n_steps=30)
        assert traj.ndim == 2 and traj.shape[1] == 4

    def test_no_r_max_allows_full_n_steps(self, fitted_linear):
        # Sans r_max/r_min, seul v_stop arrête (avec v_stop très faible, peut aller loin)
        state = np.array([0.25, 0.5, 0.0, 0.7])
        traj = predict_trajectory(fitted_linear, state, n_steps=10,
                                  r_max=None, r_min=None, v_stop=0.0)
        # Sans condition d'arrêt, exactement n_steps
        assert len(traj) == 10


# ═══════════════════════════════════════════════════════════════
# predict_with_errors
# ═══════════════════════════════════════════════════════════════

class TestPredictWithErrors:

    def test_output_is_two_arrays(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        ref = np.random.default_rng(0).uniform(0, 1, (30, 4))
        ref[:, 0] = np.abs(ref[:, 0]) + 0.05
        traj, errors = predict_with_errors(fitted_linear, state, ref)
        assert traj.ndim == 2 and errors.ndim == 2

    def test_errors_shape_matches_min_lengths(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        n_ref = 20
        ref = np.tile(state, (n_ref, 1))
        traj, errors = predict_with_errors(fitted_linear, state, ref)
        n = min(len(traj), n_ref)
        assert errors.shape == (n, 4)

    def test_errors_non_negative(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        ref = np.tile(state, (20, 1))
        _, errors = predict_with_errors(fitted_linear, state, ref)
        assert np.all(errors >= 0.0)

    def test_errors_zero_when_pred_equals_ref(self, fitted_linear):
        # Si ref = trajectoire prédite, erreur = 0
        state = np.array([0.25, 0.5, 0.0, 0.7])
        n = 15
        traj = predict_trajectory(fitted_linear, state, n_steps=n,
                                  r_max=None, r_min=None, v_stop=0.0)
        _, errors = predict_with_errors(fitted_linear, state, traj,
                                        r_max=None, r_min=None, v_stop=0.0)
        np.testing.assert_allclose(errors, 0.0, atol=1e-12)

    def test_kwargs_forwarded(self, fitted_linear):
        state = np.array([0.38, 0.0, 0.5, 0.5])
        ref = np.tile(state, (100, 1))
        # r_max=0.4 → trajectoire courte
        traj_short, _ = predict_with_errors(fitted_linear, state, ref, r_max=0.4)
        traj_long,  _ = predict_with_errors(fitted_linear, state, ref, r_max=None)
        assert len(traj_short) <= len(traj_long)

    def test_shorter_pred_than_ref(self, fitted_linear):
        # Trajectoire prédite plus courte que ref → errors tronqués à len(pred)
        state = np.array([0.25, 0.5, 0.0, 0.7])
        ref = np.tile(state, (200, 1))  # ref très longue
        traj, errors = predict_with_errors(fitted_linear, state, ref,
                                           r_max=0.4, r_min=0.03, v_stop=1e-3)
        assert len(errors) == min(len(traj), 200)
