"""2-D uniform circular motion (MCU) integrator.

Models a particle in a perfect circular orbit given analytically by::

    x(t) = R · cos(ω·t + φ₀)
    y(t) = R · sin(ω·t + φ₀)

The velocity is always tangential with constant magnitude v = ω·R::

    vx(t) = -R·ω · sin(ω·t + φ₀)
    vy(t) =  R·ω · cos(ω·t + φ₀)

The centripetal acceleration pointing toward the centre has magnitude::

    a_c = ω²·R = v²/R

This is the idealised circular orbit valid when ω = √(G·M/R³)
(Kepler's third law).  The simulation samples the analytic solution at
fixed time intervals of ``frame_ms`` milliseconds so that each returned
entry corresponds to exactly one animation frame.

Returns
-------
Dict with keys ``"xs"``, ``"ys"``, ``"vxs"``, ``"vys"``, ``"n_frames"``.
"""
from __future__ import annotations

import math

from utils.params import SimulationMCUParams


def simulate_mcu(sim_params: SimulationMCUParams | None = None) -> dict:
    """Sample the MCU trajectory and return per-frame positions.

    Args:
        sim_params: Simulation parameters.  Uses defaults if ``None``.

    Returns:
        Dict with keys ``"xs"``, ``"ys"``, ``"vxs"``, ``"vys"``,
        ``"n_frames"``.
    """
    if sim_params is None:
        sim_params = SimulationMCUParams()

    omega   = float(sim_params.omega)
    R       = float(sim_params.R)
    phi0    = math.radians(float(sim_params.initial_angle))
    dt      = sim_params.frame_ms / 1000.0   # seconds per frame

    T_orbit  = 2.0 * math.pi / omega         # orbital period [s]
    duration = float(sim_params.n_orbits) * T_orbit
    n_frames = max(1, int(duration / dt))

    xs:  list[float] = []
    ys:  list[float] = []
    vxs: list[float] = []
    vys: list[float] = []

    for i in range(n_frames):
        t    = i * dt
        angle = omega * t + phi0
        xs.append(R  * math.cos(angle))
        ys.append(R  * math.sin(angle))
        vxs.append(-R * omega * math.sin(angle))
        vys.append( R * omega * math.cos(angle))

    return {"xs": xs, "ys": ys, "vxs": vxs, "vys": vys, "n_frames": n_frames}
