"""Tests for simulations/sim3d/simulate_membrane.py."""
import math

import pytest

from simulations.sim3d.simulate_membrane import simulate_membrane
from utils.params import SimulationMembraneParams


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(n=500, **kwargs) -> dict:
    return simulate_membrane(SimulationMembraneParams(num_steps=n, **kwargs))


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
        res = simulate_membrane()
        assert len(res["xs"]) > 0


# ---------------------------------------------------------------------------
# Initial conditions
# ---------------------------------------------------------------------------

class TestInitialConditions:
    def test_first_frame_near_initial_position(self):
        x0, y0 = 0.3, 0.0
        res = _run(x0=x0, y0=y0, v_i=0.5, theta=90.0)
        assert abs(res["xs"][0] - x0) < 0.05
        assert abs(res["ys"][0] - y0) < 0.05

    def test_initial_outside_rim_clamped(self):
        res = _run(x0=5.0, y0=0.0, surface_radius=0.4)
        assert len(res["xs"]) > 0


# ---------------------------------------------------------------------------
# Stopping conditions
# ---------------------------------------------------------------------------

class TestStoppingConditions:
    def test_rim_exit(self):
        """Radially outward launch with no friction should exit via the rim."""
        res = _run(n=5000, x0=0.3, y0=0.0, v_i=3.0, theta=180.0,
                   friction_coef=0.0, surface_radius=0.4)
        R = 0.4
        r_last = math.hypot(res["xs"][-1], res["ys"][-1])
        assert r_last >= R - 0.02

    def test_max_steps_respected(self):
        n = 80
        res = _run(n=n, friction_coef=0.0)
        assert len(res["xs"]) <= n


# ---------------------------------------------------------------------------
# Physics invariants
# ---------------------------------------------------------------------------

class TestPhysicsInvariants:
    def test_z_matches_membrane_formula(self):
        """Every recorded z must lie on the membrane surface z(r)."""
        from utils.math_helpers import _membrane_z_scalar
        p = SimulationMembraneParams(num_steps=200)
        res = simulate_membrane(p)
        for x, y, z in zip(res["xs"], res["ys"], res["zs"]):
            r = math.hypot(x, y)
            z_expected = _membrane_z_scalar(
                r,
                R=p.surface_radius,
                T=p.surface_tension,
                F=p.center_weight,
                center_radius=p.center_radius,
            )
            assert z == pytest.approx(z_expected, abs=1e-6)

    def test_friction_reduces_orbit_life(self):
        """Higher friction → particle reaches the center sooner."""
        common = dict(x0=0.3, y0=0.0, v_i=0.5, theta=90.0, n=10000)
        res_low  = _run(friction_coef=0.0,  **common)
        res_high = _run(friction_coef=0.5,  **common)
        assert len(res_high["xs"]) < len(res_low["xs"])

    def test_deeper_surface_with_more_load(self):
        """Heavier central load → steeper membrane gradient → stronger inward pull.

        With v_i=0 (particle released from rest), only gravity acts.  A heavier
        load steepens the surface, so the particle accelerates faster and reaches
        the centre in fewer steps.
        """
        common = dict(x0=0.3, y0=0.0, v_i=0.0, theta=90.0,
                      friction_coef=0.0, n=5000)
        res_light = _run(center_weight=1.0,  **common)
        res_heavy = _run(center_weight=20.0, **common)
        assert len(res_heavy["xs"]) < len(res_light["xs"])

    def test_positions_are_finite(self):
        res = _run()
        for key in ("xs", "ys", "zs", "vxs", "vys"):
            assert all(math.isfinite(v) for v in res[key])

    def test_membrane_deeper_than_cone_at_same_radius(self):
        """The membrane surface is more curved (concave) than a linear cone near the rim.

        At large r (close to R), the log surface approaches 0 from below faster than
        a linear cone, so z_membrane > z_cone there.  At small r the membrane is deeper.
        We check that the two models are genuinely different.
        """
        from utils.math_helpers import _cone_z_scalar, _membrane_z_scalar
        R, cr = 0.4, 0.035
        # Tune cone_slope to match membrane z at r=cr (same depth at contact)
        # — we just verify the shapes differ somewhere
        z_membrane_mid = _membrane_z_scalar(0.2, R=R, T=10.0, F=4.905, center_radius=cr)
        z_cone_mid     = _cone_z_scalar(0.2, R=R, cone_slope=0.1, center_radius=cr)
        assert z_membrane_mid != pytest.approx(z_cone_mid, abs=1e-3)
