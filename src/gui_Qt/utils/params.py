from dataclasses import asdict, dataclass
from math import cos, radians, sin, sqrt
from typing import Dict


@dataclass
class Simulation3dParams:
    """Physics, initial-condition, and surface-geometry parameters for the 3D sim.

    The surface is a cone of constant slope alpha = arctan(cone_slope).
    The particle starts at (x0, y0) on the cone with speed v_i directed at
    angle theta (degrees) relative to the radial direction.
    Velocity components vx0/vy0 are derived properties.

    frame_ms is declared without a type annotation so dataclasses.fields()
    skips it and it does not appear as a UI control.

    Surface geometry
    ----------------
    The cone profile is:
        z(r) = -cone_slope * (R - r)
    which gives z = 0 at the rim (r = R) and z = -cone_slope*R at the centre.
    cone_slope = dz/dr = z_max / R  [dimensionless] is the constant radial slope.

    Gravitational acceleration along the surface (constant everywhere):
        a_grav = g * sin(arctan(cone_slope))  ≈  g * cone_slope  (small angles)
    directed radially toward the centre.

    Attributes:
        cone_slope:      Constant radial slope of the cone dz/dr [dimensionless].
                         Positive value — surface descends toward the centre.
        surface_radius:  Cone rim radius R [m]. Outer stopping boundary.
        center_radius:   Central sphere radius [m]. Inner stopping boundary.
        time_step:       Euler integration step dt [s].
        num_steps:       Maximum integration steps per simulation.
        g:               Gravitational acceleration [m/s²].
        particle_radius: Moving particle radius [m]. Visual size and z-offset.
        particle_mass:   Particle mass m [kg].
                         Note: in the current model (Coulomb friction + gravity only),
                         m cancels out in both accelerations:
                           a_grav = (m·g·sin α) / m = g·sin α
                           a_fric = (μ_c·m·g·cos α) / m = μ_c·g·cos α
                         The field is kept explicit so that any future force
                         independent of mass (e.g. wind, magnetic) can be added
                         without a model change.
        x0:              Initial x-coordinate [m].
        y0:              Initial y-coordinate [m].
        v_i:             Initial speed [m/s].
        theta:           Launch angle [°]. 0 = radially inward, 90 = CCW tangential.
        friction_coef:   Coulomb kinetic friction coefficient μ_c [dimensionless].
                         Friction force magnitude = μ_c · m · g · cos(α).
    """

    frame_ms = 10

    cone_slope: float = 0.10
    surface_radius: float = 0.80
    center_radius: float = 0.035

    time_step: float = 0.010
    num_steps: int = 20000

    g: float = 9.810

    particle_radius: float = 0.01
    particle_mass: float = 0.01

    x0: float = 0.8
    y0: float = 0.00

    v_i: float = 0.5
    theta: float = 85.0

    friction_coef: float = 0.01

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def vx0(self) -> float:
        """Initial x-velocity component [m/s].

        Convention: r̂ points **inward** (toward the centre) and t̂ points
        **CCW tangentially**. theta=0 is a purely inward radial launch;
        theta=90 is a purely CCW tangential launch.
        """
        r = sqrt(self.x0 * self.x0 + self.y0 * self.y0)
        if r > 1e-12:
            rx = -self.x0 / r
            tx = -self.y0 / r
        else:
            rx, tx = -1.0, 0.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * rx + sin(th) * tx)

    @property
    def vy0(self) -> float:
        """Initial y-velocity component [m/s].

        Convention: r̂ points **inward** (toward the centre) and t̂ points
        **CCW tangentially**. theta=0 is a purely inward radial launch;
        theta=90 is a purely CCW tangential launch.
        """
        r = sqrt(self.x0 * self.x0 + self.y0 * self.y0)
        if r > 1e-12:
            ry = -self.y0 / r
            ty = self.x0 / r
        else:
            ry, ty = 0.0, 1.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * ry + sin(th) * ty)


@dataclass
class Simulation2dParams:
    """Physics and initial-condition parameters for the 2D orbital simulation.

    Attributes:
        G:              Gravitational constant [m³ kg⁻¹ s⁻²].
        M:              Central body mass [kg].
        r0:             Initial orbital radius [m].
        v0:             Initial speed [m/s].
        theta_deg:      Launch angle relative to positive x-axis [°].
        gamma:          Linear drag coefficient [s⁻¹].
        trail:          Number of past positions kept for the trail overlay.
        center_radius:  Central body radius [m].
        particle_radius: Moving particle radius [m].
        frame_ms:       Animation frame interval [ms].
        dt:             Velocity-Verlet integration time step [s].
    """

    G: float = 1
    M: float = 1000.0

    r0: float = 50.0
    v0: float = 3.0
    theta_deg: float = 90.0

    gamma: float = 0.001

    trail: int = 50
    center_radius: float = 6.0
    particle_radius: float = 2.0

    frame_ms: int = 10
    dt: float = 0.02


@dataclass
class SimulationMLParams:
    """Configuration for the machine-learning trajectory demo.

    Attributes:
        test_initial_idx: Index of the training sample to display (0–2).
        noise_level:      Gaussian noise std added to predicted points.
        marker_size:      Animated position marker diameter [px].
        show_true_trajectory: Toggle to show/hide the true trajectory.
    """

    # No type annotation — hidden from the auto-generated UI controls.
    frame_ms = 30

    test_initial_idx: int = 0
    noise_level: float = 0.0
    marker_size: int = 10
    show_true_trajectory: bool = True
