"""Tests for simulations/sim3d/simulate_cone.py."""
import math

import pytest

from simulations.sim3d.simulate_cone import simulate_cone
from utils.params import SimulationConeParams


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(n=500, **kwargs) -> dict:
    """Run a short simulation and return results."""
    return simulate_cone(SimulationConeParams(num_steps=n, **kwargs))


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

class TestOutputStructure:
    def test_required_keys(self):
        res = _run()
        for key in ("xs", "ys", "zs", "vxs", "vys"):
            assert key in res

    def test_lists_same_length(self):
        res = _run()
        n = len(res["xs"])
        assert n > 0
        assert all(len(res[k]) == n for k in ("ys", "zs", "vxs", "vys"))

    def test_defaults_run(self):
        res = simulate_cone()
        assert len(res["xs"]) > 0


# ---------------------------------------------------------------------------
# Initial conditions
# ---------------------------------------------------------------------------

class TestInitialConditions:
    def test_first_frame_near_initial_position(self):
        x0, y0 = 0.5, 0.0
        res = _run(x0=x0, y0=y0, v_i=0.3, theta=90.0)
        # First recorded frame is one step after t=0, so it won't be exactly (x0, y0),
        # but it should be close (within a few time-step distances).
        assert abs(res["xs"][0] - x0) < 0.05
        assert abs(res["ys"][0] - y0) < 0.05

    def test_first_frame_inside_rim(self):
        R = 0.8
        res = _run(surface_radius=R)
        r0 = math.hypot(res["xs"][0], res["ys"][0])
        assert r0 < R + 0.1  # one step can cross the rim, but not by much


# ---------------------------------------------------------------------------
# Stopping conditions
# ---------------------------------------------------------------------------

class TestStoppingConditions:
    def test_rim_exit(self):
        """Radially outward launch should exit via the rim."""
        res = _run(n=2000, x0=0.5, y0=0.0, v_i=2.0, theta=180.0,
                   friction_coef=0.0, surface_radius=0.8)
        R = 0.8
        r_last = math.hypot(res["xs"][-1], res["ys"][-1])
        assert r_last >= R - 0.05

    def test_max_steps_respected(self):
        """Loop must stop at num_steps even for stable orbits."""
        n = 50
        res = _run(n=n, friction_coef=0.0, v_i=0.3, theta=90.0)
        assert len(res["xs"]) <= n

    def test_initial_outside_rim_clamped(self):
        """x0 > R must be clamped and not crash."""
        res = _run(x0=5.0, y0=0.0, surface_radius=0.8)
        assert len(res["xs"]) > 0


# ---------------------------------------------------------------------------
# Physics invariants
# ---------------------------------------------------------------------------

class TestPhysicsInvariants:
    def test_all_z_on_surface(self):
        """Every recorded z must match the cone formula at that (x, y)."""
        from utils.math_helpers import _cone_z_scalar
        p = SimulationConeParams(num_steps=200)
        res = simulate_cone(p)
        for x, y, z in zip(res["xs"], res["ys"], res["zs"]):
            r = math.hypot(x, y)
            z_expected = _cone_z_scalar(
                r, R=p.surface_radius,
                cone_slope=p.cone_slope,
                center_radius=p.center_radius,
            )
            assert z == pytest.approx(z_expected, abs=1e-10)

    def test_friction_delays_or_blocks_particle(self):
        """Friction opposes inward motion — the friction-free case reaches centre faster.

        With theta=0 (pure radially inward launch) and friction=0, gravity
        accelerates the particle all the way to the centre.  With friction=0.5,
        the friction force (μ·g·cos α ≈ 4.9 m/s²) exceeds the gravitational
        component along the slope (g·sin α ≈ 1.0 m/s²), so the particle
        decelerates, stops before centre, and uses all num_steps.
        """
        common = dict(x0=0.5, y0=0.0, v_i=0.3, theta=0.0, n=5000)
        res_low  = _run(friction_coef=0.0,  **common)
        res_high = _run(friction_coef=0.5,  **common)
        assert len(res_low["xs"]) < len(res_high["xs"])

    def test_positions_are_finite(self):
        res = _run()
        for key in ("xs", "ys", "zs", "vxs", "vys"):
            assert all(math.isfinite(v) for v in res[key])
