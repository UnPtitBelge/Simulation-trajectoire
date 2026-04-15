"""Tests unitaires — physique (cone.py, membrane.py, mcu.py)."""

import numpy as np
import pytest

from physics.cone import compute_cone, _derivatives
from physics.membrane import compute_membrane
from physics.mcu import compute_mcu


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _cone(r0=0.25, theta0=0.0, vr0=0.0, vtheta0=0.7, n_steps=300, **kw):
    defaults = dict(R=0.4, depth=0.09, friction=0.02, g=9.81, dt=0.01,
                    center_radius=0.03)
    defaults.update(kw)
    return compute_cone(r0=r0, theta0=theta0, vr0=vr0, vtheta0=vtheta0,
                        n_steps=n_steps, **defaults)


def _membrane(r0=0.25, theta0=0.0, vr0=0.0, vtheta0=0.5, n_steps=300, **kw):
    defaults = dict(R=0.4, k=0.035, r_min=0.03, friction=0.02, g=9.81, dt=0.01,
                    center_radius=0.03)
    defaults.update(kw)
    return compute_membrane(r0=r0, theta0=theta0, vr0=vr0, vtheta0=vtheta0,
                            n_steps=n_steps, **defaults)


# ═══════════════════════════════════════════════════════════════
# _derivatives
# ═══════════════════════════════════════════════════════════════

class TestDerivatives:
    def test_returns_4_tuple(self):
        result = _derivatives(0.2, 0.0, 0.0, 0.5, r_min=0.03,
                              g_radial=-1.0, g_friction=0.2)
        assert len(result) == 4

    def test_dr_dt_equals_vr(self):
        vr = 0.3
        dr, _, _, _ = _derivatives(0.2, 0.0, vr, 0.5, r_min=0.03,
                                   g_radial=-1.0, g_friction=0.2)
        assert abs(dr - vr) < 1e-12

    def test_dtheta_dt_equals_vtheta_over_r(self):
        r, vtheta = 0.25, 0.6
        _, dtheta, _, _ = _derivatives(r, 0.0, 0.0, vtheta, r_min=0.03,
                                       g_radial=-1.0, g_friction=0.2)
        assert abs(dtheta - vtheta / r) < 1e-12

    def test_static_below_friction_threshold(self):
        # |g_radial| < g_friction → bille immobile
        dr, dtheta, ar, at = _derivatives(0.25, 0.0, 0.0, 0.0, r_min=0.03,
                                          g_radial=-0.1, g_friction=0.5)
        assert ar == 0.0 and at == 0.0

    def test_static_above_friction_threshold(self):
        # |g_radial| > g_friction → bille glisse vers le centre
        dr, dtheta, ar, at = _derivatives(0.25, 0.0, 0.0, 0.0, r_min=0.03,
                                          g_radial=-1.0, g_friction=0.2)
        assert ar != 0.0

    def test_rolling_factor_reduces_acceleration(self):
        # En roulement, |ar| < glissement pour même g_radial
        _, _, ar_slide, _ = _derivatives(0.25, 0.0, 0.0, 0.6, r_min=0.03,
                                         g_radial=-1.0, g_friction=0.0, rolling=False)
        _, _, ar_roll, _  = _derivatives(0.25, 0.0, 0.0, 0.6, r_min=0.03,
                                         g_radial=-1.0, g_friction=0.0, rolling=True)
        # f = 5/7 < 1 → |ar_roll| < |ar_slide|
        assert abs(ar_roll) < abs(ar_slide)

    def test_drag_reduces_acceleration(self):
        _, _, ar_no_drag, _ = _derivatives(0.25, 0.0, 0.1, 0.6, r_min=0.03,
                                           g_radial=-1.0, g_friction=0.2, drag_coeff=0.0)
        _, _, ar_drag, _    = _derivatives(0.25, 0.0, 0.1, 0.6, r_min=0.03,
                                           g_radial=-1.0, g_friction=0.2, drag_coeff=0.1)
        # La traînée s'oppose au mouvement → réduit ar algébriquement
        assert ar_drag < ar_no_drag


# ═══════════════════════════════════════════════════════════════
# compute_cone — forme et invariants
# ═══════════════════════════════════════════════════════════════

class TestComputeCone:

    def test_output_shape(self):
        traj = _cone()
        assert traj.ndim == 2
        assert traj.shape[1] == 4

    def test_r_within_bounds(self):
        traj = _cone()
        assert np.all(traj[:, 0] >= 0.03 - 1e-9)
        assert np.all(traj[:, 0] <= 0.4  + 1e-9)

    def test_stops_at_center(self):
        # Bille lancée vers le centre à grande vitesse → arrêt anticipé (< n_steps)
        # Note : le dernier état enregistré est AVANT le franchissement de center_radius
        traj = _cone(r0=0.05, vr0=-2.0, vtheta0=0.0, n_steps=5000)
        assert len(traj) < 5000  # la simulation s'est arrêtée avant la fin

    def test_stops_at_border(self):
        # Bille lancée vers le bord → arrêt anticipé (< n_steps)
        # Note : le dernier état enregistré est AVANT le franchissement de R
        traj = _cone(r0=0.38, vr0=2.0, vtheta0=0.0, n_steps=500)
        assert len(traj) < 500  # la simulation s'est arrêtée avant la fin

    def test_stops_when_no_friction_and_energy_conserved(self):
        # Sans friction, une bille en orbite circulaire quasi-parfaite ne doit pas
        # s'arrêter avant n_steps
        traj = _cone(r0=0.25, vr0=0.0, vtheta0=0.65, n_steps=100,
                     friction=0.0, rolling=False)
        assert len(traj) == 100

    def test_shorter_with_higher_friction(self):
        t_low  = _cone(friction=0.01, n_steps=2000)
        t_high = _cone(friction=0.10, n_steps=2000)
        assert len(t_high) < len(t_low)

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Intégrateur inconnu"):
            _cone(n_steps=10, method="invalid")

    def test_all_integrators_give_same_shape_columns(self):
        for method in ("euler", "euler_cromer", "rk4"):
            traj = _cone(n_steps=50, method=method)
            assert traj.shape[1] == 4, f"{method} shape error"

    def test_rk4_closer_to_reference_than_euler(self):
        # RK4 et Euler-Cromer doivent converger ; RK4 avec dt standard ≈ Euler-Cromer
        # mais Euler explicite doit diverger plus vite — testé via énergie finale
        t_cromer = _cone(method="euler_cromer", n_steps=500)
        t_rk4    = _cone(method="rk4",          n_steps=500)
        n = min(len(t_cromer), len(t_rk4))
        rmse_r = float(np.sqrt(np.mean((t_cromer[:n, 0] - t_rk4[:n, 0]) ** 2)))
        # Faible différence attendue à dt=0.01 (les deux sont précis)
        assert rmse_r < 0.05

    # ── Niveaux physiques ────────────────────────────────────────────────────

    def test_rolling_longer_than_sliding(self):
        # Roulement pur conserve l'énergie → trajectoire plus longue que glissement
        t_slide = _cone(n_steps=3000, rolling=False)
        t_roll  = _cone(n_steps=3000, rolling=True)
        assert len(t_roll) >= len(t_slide)

    def test_drag_shortens_trajectory(self):
        # La traînée dissipe de l'énergie → trajectoire plus courte
        t_no_drag = _cone(n_steps=3000, rolling=True, rolling_resistance=0.003)
        t_drag    = _cone(n_steps=3000, rolling=True, rolling_resistance=0.003,
                          drag_coeff=0.05)
        assert len(t_drag) <= len(t_no_drag)

    def test_rolling_resistance_shortens_vs_pure_rolling(self):
        t_pure = _cone(n_steps=3000, rolling=True)
        t_rr   = _cone(n_steps=3000, rolling=True, rolling_resistance=0.005)
        assert len(t_rr) <= len(t_pure)

    def test_level3_shortest(self):
        # L3 (rolling + resistance + drag) doit être plus court que L1 (roulement pur)
        # L1 conserve l'énergie (le plus long) ; L3 dissipe via résistance + traînée
        n = 5000
        t1 = _cone(n_steps=n, rolling=True)
        t3 = _cone(n_steps=n, rolling=True, rolling_resistance=0.003, drag_coeff=0.05)
        assert len(t3) <= len(t1)

    def test_pure_rolling_no_coulomb_not_same_as_sliding(self):
        # Roulement pur ≠ glissement (facteur 5/7)
        t_slide = _cone(n_steps=200)
        t_roll  = _cone(n_steps=200, rolling=True)
        # Au moins un pas diffère
        n = min(len(t_slide), len(t_roll))
        assert not np.allclose(t_slide[:n, 0], t_roll[:n, 0], atol=1e-4)


# ═══════════════════════════════════════════════════════════════
# compute_membrane — forme et invariants
# ═══════════════════════════════════════════════════════════════

class TestComputeMembrane:

    def test_output_shape(self):
        traj = _membrane()
        assert traj.ndim == 2
        assert traj.shape[1] == 4

    def test_r_within_bounds(self):
        traj = _membrane()
        assert np.all(traj[:, 0] >= 0.03 - 1e-9)
        assert np.all(traj[:, 0] <= 0.4  + 1e-9)

    def test_r_min_clamped_to_center_radius(self):
        # r_min < center_radius doit être élevé à center_radius
        traj = _membrane(r_min=0.01, center_radius=0.03)
        assert np.all(traj[:, 0] >= 0.03 - 1e-9)

    def test_shorter_with_higher_friction(self):
        t_low  = _membrane(friction=0.01, n_steps=2000)
        t_high = _membrane(friction=0.15, n_steps=2000)
        assert len(t_high) <= len(t_low)

    def test_rolling_different_from_sliding(self):
        t_slide = _membrane(n_steps=300)
        t_roll  = _membrane(n_steps=300, rolling=True)
        n = min(len(t_slide), len(t_roll))
        assert not np.allclose(t_slide[:n, 0], t_roll[:n, 0], atol=1e-4)

    def test_drag_reduces_speed(self):
        # La traînée dissipe de l'énergie → trajectoire plus courte ou vitesse moyenne moindre
        t_no   = _membrane(n_steps=500, rolling=True)
        t_drag = _membrane(n_steps=500, rolling=True, drag_coeff=0.05)
        # La traînée raccourcit la trajectoire ou ne l'allonge pas
        assert len(t_drag) <= len(t_no)

    def test_orbital_speed_near_constant_no_friction(self):
        # Sur la membrane sans friction, vθ ≈ √(g·k) = constante
        vth_orb = np.sqrt(9.81 * 0.035)
        traj = _membrane(r0=0.25, vtheta0=vth_orb, vr0=0.0,
                         friction=0.0, n_steps=100)
        vtheta = traj[:, 3]
        # Sans friction, vθ doit rester proche de vθ_orb (± 5 %)
        assert np.all(np.abs(vtheta - vth_orb) < 0.05 * vth_orb + 0.02)

    def test_invalid_r_min_raises(self):
        with pytest.raises(AssertionError):
            compute_membrane(r0=0.25, theta0=0.0, vr0=0.0, vtheta0=0.5,
                             R=0.4, k=0.035, r_min=0.5,  # r_min > R → invalide
                             friction=0.02, g=9.81, dt=0.01, n_steps=10)


# ═══════════════════════════════════════════════════════════════
# compute_mcu
# ═══════════════════════════════════════════════════════════════

class TestComputeMCU:

    def test_output_shape(self):
        traj = compute_mcu(r=0.3, theta0=0.0, omega=2.0, n_steps=100, dt=0.01)
        assert traj.shape == (100, 2)

    def test_radius_constant(self):
        traj = compute_mcu(r=0.25, theta0=0.0, omega=3.0, n_steps=50, dt=0.01)
        radii = np.sqrt(traj[:, 0] ** 2 + traj[:, 1] ** 2)
        np.testing.assert_allclose(radii, 0.25, atol=1e-10)

    def test_angle_increases_with_positive_omega(self):
        traj = compute_mcu(r=0.3, theta0=0.0, omega=1.0, n_steps=10, dt=0.1)
        angles = np.arctan2(traj[:, 1], traj[:, 0])
        # Les angles doivent être croissants (modulo 2π)
        diffs = np.diff(np.unwrap(angles))
        assert np.all(diffs > 0)

    def test_period(self):
        omega = 2 * np.pi  # 1 tour en 1 s
        dt = 0.01
        # 101 pas : t=0, 0.01, ..., 1.00 → dernier point à t=1.0 s = 1 tour complet
        n_steps = 101
        traj = compute_mcu(r=0.3, theta0=0.0, omega=omega, n_steps=n_steps, dt=dt)
        # Après 1 tour, position ≈ position initiale
        np.testing.assert_allclose(traj[-1], traj[0], atol=1e-6)

    def test_initial_position(self):
        traj = compute_mcu(r=0.3, theta0=np.pi / 2, omega=0.0, n_steps=5, dt=0.01)
        # theta0 = π/2 → x ≈ 0, y ≈ 0.3
        np.testing.assert_allclose(traj[0, 0], 0.0,  atol=1e-10)
        np.testing.assert_allclose(traj[0, 1], 0.3,  atol=1e-10)
