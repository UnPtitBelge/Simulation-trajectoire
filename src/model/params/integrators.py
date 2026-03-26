"""Enums for integrator and ML model selection."""

from enum import StrEnum


class Integrator(StrEnum):
    """Numerical integration method for physics simulations."""
    EULER_SEMI_IMPLICIT = "euler_semi"
    VERLET = "verlet"
    RK4 = "rk4"


class MLModel(StrEnum):
    """Machine learning model type."""
    LINEAR = "linear"
    MLP = "mlp"
