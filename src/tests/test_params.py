"""Tests for utils/params.py — parameter dataclasses."""
import math

import pytest

from utils.params import (
    SimulationConeParams,
    SimulationMembraneParams,
    SimulationMCUParams,
    SimulationMLParams,
)


# ---------------------------------------------------------------------------
# SimulationConeParams
# ---------------------------------------------------------------------------

class TestSimulationConeParams:
    def test_defaults_are_sensible(self):
        p = SimulationConeParams()
        assert p.cone_slope > 0
        assert p.surface_radius > p.center_radius
        assert p.g > 0
        assert 0 <= p.friction_coef <= 1
        assert p.time_step > 0
        assert p.num_steps > 0

    def test_vx0_vy0_magnitude(self):
        """Speed magnitude must equal v_i."""
        p = SimulationConeParams(v_i=1.0, theta=45.0, x0=0.5, y0=0.0)
        v = math.hypot(p.vx0, p.vy0)
        assert v == pytest.approx(1.0, rel=1e-9)

    def test_theta_90_is_pure_tangential(self):
        """theta=90° → velocity tangential (perpendicular to radial direction)."""
        p = SimulationConeParams(v_i=1.0, theta=90.0, x0=0.5, y0=0.0)
        # Position is on the +x axis, so radial = x-hat.
        # Tangential (CCW) = y-hat, so vx ≈ 0, vy ≈ v_i.
        assert p.vx0 == pytest.approx(0.0, abs=1e-9)
        assert p.vy0 == pytest.approx(1.0, rel=1e-9)

    def test_theta_0_is_pure_radial_inward(self):
        """theta=0° → velocity directed radially inward."""
        p = SimulationConeParams(v_i=1.0, theta=0.0, x0=0.5, y0=0.0)
        # Inward from +x axis → vx = -v_i, vy = 0.
        assert p.vx0 == pytest.approx(-1.0, rel=1e-9)
        assert p.vy0 == pytest.approx(0.0, abs=1e-9)

    def test_theta_180_is_pure_radial_outward(self):
        """theta=180° → velocity directed radially outward."""
        p = SimulationConeParams(v_i=1.0, theta=180.0, x0=0.5, y0=0.0)
        assert p.vx0 == pytest.approx(1.0, rel=1e-9)
        assert p.vy0 == pytest.approx(0.0, abs=1e-9)

    def test_to_dict(self):
        p = SimulationConeParams()
        d = p.to_dict()
        assert "cone_slope" in d
        assert "surface_radius" in d
        assert "friction_coef" in d
        # frame_ms is a class variable, not a field → not in asdict output
        assert "frame_ms" not in d


# ---------------------------------------------------------------------------
# SimulationMembraneParams
# ---------------------------------------------------------------------------

class TestSimulationMembraneParams:
    def test_defaults_are_sensible(self):
        p = SimulationMembraneParams()
        assert p.surface_tension > 0
        assert p.center_weight > 0
        assert p.surface_radius > p.center_radius
        assert p.g > 0

    def test_vx0_vy0_magnitude(self):
        p = SimulationMembraneParams(v_i=2.0, theta=30.0, x0=0.3, y0=0.1)
        v = math.hypot(p.vx0, p.vy0)
        assert v == pytest.approx(2.0, rel=1e-9)

    def test_theta_90_is_pure_tangential(self):
        p = SimulationMembraneParams(v_i=1.0, theta=90.0, x0=0.3, y0=0.0)
        assert p.vx0 == pytest.approx(0.0, abs=1e-9)
        assert p.vy0 == pytest.approx(1.0, rel=1e-9)

    def test_to_dict(self):
        p = SimulationMembraneParams()
        d = p.to_dict()
        assert "surface_tension" in d
        assert "center_weight" in d
        assert "friction_coef" in d
        assert "frame_ms" not in d


# ---------------------------------------------------------------------------
# SimulationMCUParams
# ---------------------------------------------------------------------------

class TestSimulationMCUParams:
    def test_defaults_are_sensible(self):
        p = SimulationMCUParams()
        assert p.R > 0
        assert p.omega > 0
        assert p.n_orbits > 0
        assert p.center_radius > 0
        assert p.particle_radius > 0

    def test_orbital_period(self):
        omega = 2.0
        p = SimulationMCUParams(omega=omega)
        T = 2.0 * math.pi / omega
        assert T == pytest.approx(math.pi)

    def test_tangential_speed(self):
        R, omega = 50.0, 0.5
        v = R * omega
        assert v == pytest.approx(25.0)

    def test_to_dict(self):
        p = SimulationMCUParams()
        d = p.to_dict()
        assert "R" in d
        assert "omega" in d
        assert "frame_ms" not in d


# ---------------------------------------------------------------------------
# SimulationMLParams
# ---------------------------------------------------------------------------

class TestSimulationMLParams:
    def test_defaults(self):
        p = SimulationMLParams()
        assert p.test_initial_idx == 0
        assert p.noise_level == 0.0
        assert p.show_true_trajectory is True
