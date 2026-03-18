"""Tests for simulations/sim2d/simulate_mcu.py."""
import math

import pytest

from simulations.sim2d.simulate_mcu import simulate_mcu
from utils.params import SimulationMCUParams


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(**kwargs) -> dict:
    return simulate_mcu(SimulationMCUParams(**kwargs))


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

class TestOutputStructure:
    def test_required_keys(self):
        res = _run()
        for key in ("xs", "ys", "vxs", "vys", "n_frames"):
            assert key in res

    def test_lists_same_length(self):
        res = _run()
        n = res["n_frames"]
        assert n > 0
        assert all(len(res[k]) == n for k in ("xs", "ys", "vxs", "vys"))

    def test_defaults_run(self):
        res = simulate_mcu()
        assert res["n_frames"] > 0


# ---------------------------------------------------------------------------
# Frame count
# ---------------------------------------------------------------------------

class TestFrameCount:
    def test_one_orbit_frame_count(self):
        """n_frames ≈ T_orbit / dt for exactly 1 orbit."""
        omega, R = 1.0, 50.0
        p = SimulationMCUParams(omega=omega, R=R, n_orbits=1.0)
        dt = p.frame_ms / 1000.0
        T  = 2.0 * math.pi / omega
        expected = int(T / dt)
        res = simulate_mcu(p)
        assert abs(res["n_frames"] - expected) <= 1

    def test_more_orbits_more_frames(self):
        res1 = _run(n_orbits=1.0)
        res3 = _run(n_orbits=3.0)
        assert res3["n_frames"] == pytest.approx(3 * res1["n_frames"], abs=1)


# ---------------------------------------------------------------------------
# Circular orbit invariants
# ---------------------------------------------------------------------------

class TestCircularOrbit:
    def test_constant_radius(self):
        """Every position must lie exactly on the circle of radius R."""
        R = 50.0
        res = _run(R=R, n_orbits=2.0)
        for x, y in zip(res["xs"], res["ys"]):
            r = math.hypot(x, y)
            assert r == pytest.approx(R, rel=1e-9)

    def test_constant_speed(self):
        """Speed |v| = ω·R must be constant throughout."""
        R, omega = 40.0, 0.8
        expected_speed = R * omega
        res = _run(R=R, omega=omega, n_orbits=1.0)
        for vx, vy in zip(res["vxs"], res["vys"]):
            v = math.hypot(vx, vy)
            assert v == pytest.approx(expected_speed, rel=1e-9)

    def test_velocity_perpendicular_to_position(self):
        """v must be perpendicular to r (tangential) at every frame."""
        res = _run(R=50.0, omega=0.5, n_orbits=1.0)
        for x, y, vx, vy in zip(res["xs"], res["ys"], res["vxs"], res["vys"]):
            dot = x * vx + y * vy
            assert dot == pytest.approx(0.0, abs=1e-6)

    def test_ccw_direction(self):
        """Default orbit should be counter-clockwise (positive cross product r × v)."""
        res = _run(initial_angle=0.0)
        x, y   = res["xs"][0],  res["ys"][0]
        vx, vy = res["vxs"][0], res["vys"][0]
        cross_z = x * vy - y * vx   # z-component of r × v
        assert cross_z > 0

    def test_initial_angle(self):
        """First frame position must match the requested initial angle."""
        for angle_deg in [0.0, 45.0, 90.0, 180.0, 270.0]:
            res = _run(R=50.0, initial_angle=angle_deg, n_orbits=0.1)
            x0, y0 = res["xs"][0], res["ys"][0]
            angle_rad = math.radians(angle_deg)
            assert x0 == pytest.approx(50.0 * math.cos(angle_rad), abs=1e-6)
            assert y0 == pytest.approx(50.0 * math.sin(angle_rad), abs=1e-6)

    def test_completes_full_orbit(self):
        """After exactly one orbit the particle should return near its start."""
        res = _run(R=50.0, omega=1.0, n_orbits=1.0, initial_angle=0.0)
        x0, y0 = res["xs"][0], res["ys"][0]
        # Last frame is one step before completing the loop, so we compare
        # first vs last and expect them to be within one frame's arc length.
        x_last, y_last = res["xs"][-1], res["ys"][-1]
        p = SimulationMCUParams(R=50.0, omega=1.0)
        arc_per_frame = 50.0 * 1.0 * (p.frame_ms / 1000.0)
        dist = math.hypot(x_last - x0, y_last - y0)
        assert dist < arc_per_frame * 2

    def test_positions_are_finite(self):
        res = _run()
        for key in ("xs", "ys", "vxs", "vys"):
            assert all(math.isfinite(v) for v in res[key])
