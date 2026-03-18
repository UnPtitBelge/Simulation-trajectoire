"""Tests for utils/math_helpers.py."""
import math

import numpy as np
import pytest

from utils.math_helpers import (
    _cone_z_scalar,
    _membrane_gradient,
    _membrane_z_scalar,
    cone_z,
    disk_xy,
    membrane_z,
)

# ---------------------------------------------------------------------------
# Cone surface
# ---------------------------------------------------------------------------

class TestConeZ:
    """Vectorised cone deformation."""

    def test_zero_at_rim(self):
        R, slope, cr = 0.8, 0.1, 0.035
        z = cone_z(np.array([R]), R=R, cone_slope=slope, center_radius=cr)
        assert z[0] == pytest.approx(0.0)

    def test_deepest_at_center_radius(self):
        R, slope, cr = 0.8, 0.1, 0.035
        r = np.array([0.0, cr / 2, cr])
        z = cone_z(r, R=R, cone_slope=slope, center_radius=cr)
        z_floor = -slope * (R - cr)
        # All values at or below the floor should be clamped to floor
        assert np.all(z >= z_floor - 1e-12)
        assert z[-1] == pytest.approx(z_floor)

    def test_increases_toward_rim(self):
        R, slope, cr = 0.8, 0.1, 0.035
        r = np.linspace(cr, R, 50)
        z = cone_z(r, R=R, cone_slope=slope, center_radius=cr)
        # z should be monotonically non-decreasing as r → R
        assert np.all(np.diff(z) >= -1e-12)

    def test_shape_preserved(self):
        r = np.zeros((4, 5))
        z = cone_z(r, R=1.0, cone_slope=0.1, center_radius=0.05)
        assert z.shape == (4, 5)

    def test_nan_outside_rim_is_callers_responsibility(self):
        # cone_z itself doesn't NaN outside R; that's done in the renderer
        R, slope, cr = 0.8, 0.1, 0.035
        z = cone_z(np.array([R + 0.1]), R=R, cone_slope=slope, center_radius=cr)
        assert np.isfinite(z[0])


class TestConeZScalar:
    """Scalar cone deformation — must match vectorised version."""

    @pytest.mark.parametrize("r", [0.035, 0.1, 0.4, 0.79, 0.8])
    def test_matches_vectorised(self, r):
        R, slope, cr = 0.8, 0.1, 0.035
        z_vec    = float(cone_z(np.array([r]), R=R, cone_slope=slope, center_radius=cr)[0])
        z_scalar = _cone_z_scalar(r, R=R, cone_slope=slope, center_radius=cr)
        assert z_scalar == pytest.approx(z_vec, abs=1e-12)

    def test_floor_clamping(self):
        R, slope, cr = 0.8, 0.1, 0.035
        z_floor  = -slope * (R - cr)
        z_origin = _cone_z_scalar(0.0, R=R, cone_slope=slope, center_radius=cr)
        assert z_origin == pytest.approx(z_floor)


# ---------------------------------------------------------------------------
# Laplace membrane surface
# ---------------------------------------------------------------------------

class TestMembraneZ:
    """Vectorised membrane deformation: z(r) = -(F/2πT)·ln(R/r)."""

    def test_zero_at_rim(self):
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        z = membrane_z(np.array([R]), R=R, T=T, F=F, center_radius=cr)
        assert z[0] == pytest.approx(0.0, abs=1e-10)

    def test_negative_inside_rim(self):
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        r = np.linspace(cr, R * 0.99, 20)
        z = membrane_z(r, R=R, T=T, F=F, center_radius=cr)
        assert np.all(z < 0)

    def test_increases_toward_rim(self):
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        r = np.linspace(cr, R, 50)
        z = membrane_z(r, R=R, T=T, F=F, center_radius=cr)
        assert np.all(np.diff(z) >= -1e-12)

    def test_singularity_clamped(self):
        # r=0 must not raise; result should equal z(center_radius)
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        z0 = membrane_z(np.array([0.0]), R=R, T=T, F=F, center_radius=cr)
        zc = membrane_z(np.array([cr]), R=R, T=T, F=F, center_radius=cr)
        assert np.isfinite(z0[0])
        assert z0[0] == pytest.approx(zc[0])

    def test_deeper_with_more_load(self):
        R, T, cr, r = 0.4, 10.0, 0.035, np.array([0.2])
        z_light = membrane_z(r, R=R, T=T, F=1.0,  center_radius=cr)
        z_heavy = membrane_z(r, R=R, T=T, F=10.0, center_radius=cr)
        assert z_heavy[0] < z_light[0]

    def test_shallower_with_higher_tension(self):
        R, F, cr, r = 0.4, 4.905, 0.035, np.array([0.2])
        z_low  = membrane_z(r, R=R, T=1.0,  F=F, center_radius=cr)
        z_high = membrane_z(r, R=R, T=50.0, F=F, center_radius=cr)
        assert z_high[0] > z_low[0]


class TestMembraneZScalar:
    """Scalar membrane deflection — must match vectorised version."""

    @pytest.mark.parametrize("r", [0.035, 0.1, 0.2, 0.39])
    def test_matches_vectorised(self, r):
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        z_vec    = float(membrane_z(np.array([r]), R=R, T=T, F=F, center_radius=cr)[0])
        z_scalar = _membrane_z_scalar(r, R=R, T=T, F=F, center_radius=cr)
        assert z_scalar == pytest.approx(z_vec, rel=1e-10)


class TestMembraneGradient:
    """Gradient of the membrane surface."""

    def test_z_matches_scalar(self):
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        x, y = 0.2, 0.1
        r = math.hypot(x, y)
        z_grad, _, _ = _membrane_gradient(x, y, R=R, T=T, F=F, center_radius=cr)
        z_ref = _membrane_z_scalar(r, R=R, T=T, F=F, center_radius=cr)
        assert z_grad == pytest.approx(z_ref, rel=1e-10)

    def test_gradient_points_inward(self):
        # ∂z/∂x should be positive for x > 0 (surface slopes up as r increases)
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        _, dz_dx, dz_dy = _membrane_gradient(0.2, 0.0, R=R, T=T, F=F, center_radius=cr)
        assert dz_dx > 0
        assert dz_dy == pytest.approx(0.0, abs=1e-12)

    def test_gradient_zero_at_origin(self):
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        _, dz_dx, dz_dy = _membrane_gradient(0.0, 0.0, R=R, T=T, F=F, center_radius=cr)
        assert dz_dx == pytest.approx(0.0, abs=1e-12)
        assert dz_dy == pytest.approx(0.0, abs=1e-12)

    def test_gradient_radial_symmetry(self):
        # |∇z| should depend only on r, not on angle
        R, T, F, cr = 0.4, 10.0, 4.905, 0.035
        r = 0.2
        for angle in [0, math.pi / 4, math.pi / 2, math.pi]:
            x, y = r * math.cos(angle), r * math.sin(angle)
            _, dx, dy = _membrane_gradient(x, y, R=R, T=T, F=F, center_radius=cr)
            mag = math.hypot(dx, dy)
            assert mag == pytest.approx(
                abs(4.905 / (2 * math.pi * 10.0) / r), rel=1e-6
            )


# ---------------------------------------------------------------------------
# 2-D geometry helper
# ---------------------------------------------------------------------------

class TestDiskXY:
    def test_shape(self):
        x, y = disk_xy(0.0, 0.0, 1.0, n=60)
        assert len(x) == 60
        assert len(y) == 60

    def test_closes(self):
        x, y = disk_xy(0.0, 0.0, 1.0, n=60)
        assert x[0] == pytest.approx(x[-1])
        assert y[0] == pytest.approx(y[-1])

    def test_radius(self):
        cx, cy, r = 3.0, -2.0, 5.0
        x, y = disk_xy(cx, cy, r, n=100)
        distances = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        assert np.allclose(distances, r)

    def test_centre_offset(self):
        # disk_xy closes the loop (first == last), so use a large n so the
        # duplicated endpoint shifts the mean by only r/n ≈ 0.001.
        x, y = disk_xy(10.0, 20.0, 1.0, n=1000)
        assert np.mean(x) == pytest.approx(10.0, abs=0.01)
        assert np.mean(y) == pytest.approx(20.0, abs=0.01)
