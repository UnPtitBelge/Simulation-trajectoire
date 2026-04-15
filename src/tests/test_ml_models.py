"""Tests unitaires — modèles ML (models.py)."""

import io
import pickle

import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler

from ml.models import (
    LinearStepModel,
    MLPStepModel,
    N_FEATURES,
    _clip_state,
    features_to_state,
    state_to_features,
)


# ═══════════════════════════════════════════════════════════════
# state_to_features / features_to_state
# ═══════════════════════════════════════════════════════════════

class TestStateToFeatures:

    def test_single_state_shape(self):
        state = np.array([0.25, 1.0, 0.1, 0.5])
        feat = state_to_features(state)
        assert feat.shape == (N_FEATURES,)

    def test_batch_shape(self):
        states = np.random.default_rng(0).uniform(0, 1, (50, 4))
        states[:, 0] = np.abs(states[:, 0]) + 0.05  # r > 0
        feat = state_to_features(states)
        assert feat.shape == (50, N_FEATURES)

    def test_first_feature_is_r(self):
        state = np.array([0.30, 0.5, 0.1, 0.7])
        feat = state_to_features(state)
        assert feat[0] == pytest.approx(0.30)

    def test_cos_sin_encoding(self):
        theta = np.pi / 3
        state = np.array([0.25, theta, 0.0, 0.5])
        feat = state_to_features(state)
        assert feat[1] == pytest.approx(np.cos(theta), abs=1e-10)
        assert feat[2] == pytest.approx(np.sin(theta), abs=1e-10)

    def test_centrifugal_feature(self):
        r, vtheta = 0.25, 0.6
        state = np.array([r, 0.0, 0.0, vtheta])
        feat = state_to_features(state)
        assert feat[5] == pytest.approx(vtheta ** 2 / r, abs=1e-8)

    def test_coriolis_feature(self):
        r, vr, vtheta = 0.25, 0.1, 0.6
        state = np.array([r, 0.0, vr, vtheta])
        feat = state_to_features(state)
        assert feat[6] == pytest.approx(vr * vtheta / r, abs=1e-8)

    def test_r_near_zero_no_overflow(self):
        # r très petit → r_safe = 1e-3 évite le overflow
        state = np.array([1e-6, 0.0, 0.0, 1.0])
        feat = state_to_features(state)
        assert np.all(np.isfinite(feat))


class TestFeaturesToState:

    def test_shape(self):
        feat = np.zeros(N_FEATURES)
        feat[1] = 1.0  # cos θ = 1 → θ = 0
        state = features_to_state(feat)
        assert state.shape == (4,)

    def test_round_trip_r(self):
        state = np.array([0.25, 1.2, 0.1, 0.5])
        feat = state_to_features(state)
        recovered = features_to_state(feat)
        assert recovered[0] == pytest.approx(state[0], abs=1e-6)

    def test_round_trip_theta(self):
        for theta in [-np.pi + 0.1, 0.0, np.pi / 3, np.pi - 0.1]:
            state = np.array([0.25, theta, 0.1, 0.5])
            feat = state_to_features(state)
            recovered = features_to_state(feat)
            # Normaliser dans [-π, π]
            diff = abs((recovered[1] - theta + np.pi) % (2 * np.pi) - np.pi)
            assert diff < 1e-6, f"Échec pour theta={theta:.3f}: diff={diff}"

    def test_round_trip_velocities(self):
        state = np.array([0.25, 0.8, -0.15, 0.42])
        feat = state_to_features(state)
        recovered = features_to_state(feat)
        np.testing.assert_allclose(recovered[2:], state[2:], atol=1e-6)

    def test_batch_round_trip(self):
        rng = np.random.default_rng(42)
        states = rng.uniform(-1, 1, (30, 4))
        states[:, 0] = np.abs(states[:, 0]) + 0.05
        feats = state_to_features(states)
        recovered = features_to_state(feats)
        np.testing.assert_allclose(recovered[:, 0], states[:, 0], atol=1e-6)
        np.testing.assert_allclose(recovered[:, 2:], states[:, 2:], atol=1e-6)


# ═══════════════════════════════════════════════════════════════
# _clip_state
# ═══════════════════════════════════════════════════════════════

class TestClipState:

    def test_no_clip_positive_r(self):
        state = np.array([0.25, 1.0, -0.1, 0.5])
        result = _clip_state(state)
        np.testing.assert_array_equal(result, state)

    def test_clip_negative_r(self):
        state = np.array([-0.01, 1.0, -0.5, 0.3])
        result = _clip_state(state)
        assert result[0] == 0.0

    def test_clip_negative_vr_when_r_negative(self):
        state = np.array([-0.01, 1.0, -0.5, 0.3])
        result = _clip_state(state)
        assert result[2] >= 0.0  # vr clippé à max(vr, 0)

    def test_positive_vr_unchanged_when_r_negative(self):
        state = np.array([-0.01, 1.0, 0.5, 0.3])
        result = _clip_state(state)
        assert result[2] == pytest.approx(0.5)

    def test_returns_copy(self):
        state = np.array([-0.01, 1.0, -0.5, 0.3])
        result = _clip_state(state)
        assert result is not state


# ═══════════════════════════════════════════════════════════════
# LinearStepModel
# ═══════════════════════════════════════════════════════════════

class TestLinearStepModel:

    def test_partial_fit_no_crash(self, tiny_dataset):
        X, y = tiny_dataset
        model = LinearStepModel()
        model.partial_fit(X, y)

    def test_predict_step_shape(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        next_state = fitted_linear.predict_step(state)
        assert next_state.shape == (4,)

    def test_predict_step_finite(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        next_state = fitted_linear.predict_step(state)
        assert np.all(np.isfinite(next_state))

    def test_predict_step_r_non_negative(self, fitted_linear):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        next_state = fitted_linear.predict_step(state)
        assert next_state[0] >= 0.0

    def test_not_fitted_raises(self):
        model = LinearStepModel()
        with pytest.raises(RuntimeError, match="non entraîné"):
            model.predict_step(np.array([0.25, 0.5, 0.0, 0.7]))

    def test_val_loss_returns_float(self, fitted_linear, tiny_dataset):
        X, y = tiny_dataset
        loss = fitted_linear.val_loss(X, y)
        assert isinstance(loss, float)
        assert loss >= 0.0

    def test_more_data_improves_val_loss(self, tiny_dataset):
        from tests.conftest import _make_tiny_dataset
        X_small, y_small = _make_tiny_dataset(n=20, seed=1)
        X_large, y_large = _make_tiny_dataset(n=100, seed=1)
        val_X, val_y     = _make_tiny_dataset(n=40,  seed=42)

        m_small = LinearStepModel()
        m_small.partial_fit(X_small, y_small)

        m_large = LinearStepModel()
        m_large.partial_fit(X_large, y_large)

        loss_small = m_small.val_loss(val_X, val_y)
        loss_large = m_large.val_loss(val_X, val_y)
        assert loss_large < loss_small

    def test_incremental_accumulation(self, tiny_dataset, shared_scalers):
        # XtX est commutatif : la somme 1 chunk ou 2 demi-chunks doit être identique
        # si les scalers sont partagés (même espace normalisé).
        X, y = tiny_dataset
        half = len(X) // 2
        scaler_X, scaler_y = shared_scalers

        m_full = LinearStepModel()
        m_full.inject_scalers(scaler_X, scaler_y)
        m_full.partial_fit(X, y)

        m_inc = LinearStepModel()
        m_inc.inject_scalers(scaler_X, scaler_y)
        m_inc.partial_fit(X[:half], y[:half])
        m_inc.partial_fit(X[half:], y[half:])

        # Avec les mêmes scalers, XtX doit être identique (tolérance absolue car
        # certaines entrées sont quasi-nulles → rtol non adapté)
        np.testing.assert_allclose(m_full._XtX, m_inc._XtX, atol=1e-3)

    def test_inject_scalers(self, tiny_dataset, shared_scalers):
        X, y = tiny_dataset
        scaler_X, scaler_y = shared_scalers
        model = LinearStepModel()
        model.inject_scalers(scaler_X, scaler_y)
        model.partial_fit(X, y)  # ne doit pas écraser les scalers
        state = np.array([0.25, 0.5, 0.0, 0.7])
        result = model.predict_step(state)
        assert np.all(np.isfinite(result))

    def test_pickle_round_trip(self, fitted_linear):
        buf = io.BytesIO()
        pickle.dump(fitted_linear, buf)
        buf.seek(0)
        restored = pickle.load(buf)
        state = np.array([0.25, 0.5, 0.0, 0.7])
        np.testing.assert_allclose(
            fitted_linear.predict_step(state),
            restored.predict_step(state),
            atol=1e-12,
        )

    def test_save_load_roundtrip(self, fitted_linear, tmp_path):
        path = tmp_path / "linear_model.pkl"
        fitted_linear.save(path)
        restored = LinearStepModel.load(path)
        state = np.array([0.25, 0.5, 0.0, 0.7])
        np.testing.assert_allclose(
            fitted_linear.predict_step(state),
            restored.predict_step(state),
            atol=1e-12,
        )


# ═══════════════════════════════════════════════════════════════
# MLPStepModel
# ═══════════════════════════════════════════════════════════════

class TestMLPStepModel:

    def test_partial_fit_no_crash(self, tiny_dataset):
        X, y = tiny_dataset
        model = MLPStepModel()
        model.partial_fit(X, y)

    def test_predict_step_shape(self, fitted_mlp):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        next_state = fitted_mlp.predict_step(state)
        assert next_state.shape == (4,)

    def test_predict_step_finite(self, fitted_mlp):
        state = np.array([0.25, 0.5, 0.0, 0.7])
        next_state = fitted_mlp.predict_step(state)
        assert np.all(np.isfinite(next_state))

    def test_val_loss_returns_positive_float(self, fitted_mlp, tiny_dataset):
        X, y = tiny_dataset
        loss = fitted_mlp.val_loss(X, y)
        assert isinstance(loss, float)
        assert loss >= 0.0

    def test_warm_start_multiple_chunks(self, tiny_dataset):
        from tests.conftest import _make_tiny_dataset
        X1, y1 = tiny_dataset
        X2, y2 = _make_tiny_dataset(n=80, seed=7)
        model = MLPStepModel()
        model.partial_fit(X1, y1)
        loss_before = model.val_loss(X2, y2)
        model.partial_fit(X2, y2)
        loss_after = model.val_loss(X2, y2)
        # Après 1 epoch supplémentaire sur les mêmes données, la loss doit baisser ou rester stable
        assert loss_after <= loss_before * 1.05  # tolérance 5 %

    def test_not_fitted_raises(self):
        model = MLPStepModel()
        with pytest.raises(RuntimeError, match="non entraîné"):
            model.predict_step(np.array([0.25, 0.5, 0.0, 0.7]))

    def test_pickle_round_trip(self, fitted_mlp):
        buf = io.BytesIO()
        pickle.dump(fitted_mlp, buf)
        buf.seek(0)
        restored = pickle.load(buf)
        state = np.array([0.25, 0.5, 0.0, 0.7])
        np.testing.assert_allclose(
            fitted_mlp.predict_step(state),
            restored.predict_step(state),
            atol=1e-10,
        )

    def test_inject_scalers_used(self, tiny_dataset, shared_scalers):
        X, y = tiny_dataset
        scaler_X, scaler_y = shared_scalers
        model = MLPStepModel()
        model.inject_scalers(scaler_X, scaler_y)
        assert model._scaler_fitted
        model.partial_fit(X, y)
        # Les scalers injectés ne doivent pas avoir changé (means identiques)
        np.testing.assert_allclose(model.scaler_X.mean_, scaler_X.mean_, atol=1e-10)
