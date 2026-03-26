"""Physical constants and simulation parameters."""

import math as _math

# Fundamental physical constants
GRAVITY = 9.81  # m/s²

# Small ball parameters
SMALL_BALL_RADIUS = 0.01  # meters
SMALL_BALL_MASS = 0.010  # kg

# Large ball parameters
LARGE_BALL_RADIUS = 0.03  # meters
LARGE_BALL_MASS = 1.5  # kg

# Surface parameters
SURFACE_RADIUS = 0.4  # meters
SURFACE_DEPTH = 0.09  # meters — physical depth of the 3D surface at its centre

# Cone: z(r) = -slope*(R - r)  →  depth = slope * R
CONE_DEFAULT_SLOPE = SURFACE_DEPTH / SURFACE_RADIUS  # ≈ 0.225

# Membrane: z(r) = -A·ln(R/r),  A = F/(2πT)  →  depth at r_min = A·ln(R/r_min)
MEMBRANE_R_MIN = 0.005   # metres — avoids log singularity
MEMBRANE_DEFAULT_A = SURFACE_DEPTH / _math.log(SURFACE_RADIUS / MEMBRANE_R_MIN)  # ≈ 0.0205
MEMBRANE_DEFAULT_T = 10.0  # N/m — membrane tension
MEMBRANE_DEFAULT_F = MEMBRANE_DEFAULT_A * 2 * _math.pi * MEMBRANE_DEFAULT_T  # ≈ 1.29 N

# Launch parameters
LAUNCH_R0 = 0.36  # m  — initial radial position (along x-axis)
LAUNCH_SPEED = 0.99  # m/s
LAUNCH_ANGLE = 90.0  # degrees — velocity direction (90° = tangential +y)
