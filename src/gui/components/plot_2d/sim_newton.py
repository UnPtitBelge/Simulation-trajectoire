import numpy as np

def _disk_xy(cx, cy, radius, n=60):
    """
    Get the (x, y) coordinates of points forming a circle (disk) centered at (cx, cy) with the given radius.
    """

    ang = np.linspace(0, 2*np.pi, n, endpoint=True)
    x = cx + radius * np.cos(ang)
    y = cy + radius * np.sin(ang)
    return x, y

# v=4,7, theta=90, distance=45 => MCU almost circular
def build_newton_orbit_2d_figure(
    G=1.0,             # constante gravitationnelle
    M=1000.0,          # masse du corps central
    r0=50.0,            # position initiale
    v0=4.0,
    theta_deg=90,      # angle initial de la vitesse (0 = vers la droite, 90 = vers le haut)
    gamma=0.001,
    trail=50,      # nombre de points affichés dans la trajectoire partielle
    n_frames=2000,
    duration_ms=20
):

    mu = G * M
    r_big=6.0
    r_small=2.0

    dt = 0.02

    # ---------------------------
    # Conditions initiales
    # ---------------------------
    r = np.array([r0, 0.0], dtype=float)

    # ---------------------------
    # Vitesse initiale avec angle
    # ---------------------------
    theta = np.deg2rad(theta_deg)
    v = np.array([
        v0 * np.cos(theta),
        v0 * np.sin(theta)
    ], dtype=float)

    def accel(r_vec, v_vec):
        r = np.linalg.norm(r_vec)
        r = max(float(r), 1e-12)

        r_hat = r_vec / r # vecteur unitaire pointant vers le centre
        a_mag = mu / (r**2) # accélération gravitationnelle

        a_grav = -a_mag * r_hat
        a_drag = -gamma * v_vec # force de frottement linéaire

        return a_grav + a_drag

    xs = []
    ys = []

    # ---------------------------
    # Intégration Velocity-Verlet
    # ---------------------------
    a = accel(r, v)

    for _ in range(n_frames):
        xs.append(r[0])
        ys.append(r[1])

        if np.linalg.norm(r) <= (r_big + r_small):
            break

        r_next = r + v*dt + 0.5*a*dt**2
        v_half = v + 0.5*a*dt
        a_next = accel(r_next, v_half)
        v_next = v_half + 0.5*a_next*dt

        r, v, a = r_next, v_next, a_next

    xs = np.array(xs)
    ys = np.array(ys)

    # ---------------------------
    # Traces
    # ---------------------------


    cx0, cy0 = _disk_xy(0.0, 0.0, float(r_big), n=80)
    center_ball = {
        "type": "scatter",
        "x": cx0,
        "y": cy0,
        "mode": "lines",
        "fill": "toself",
        "name": "Centre",
        "line": {"width": 1, "color": "rgba(42, 151, 8, 1)"},
        "fillcolor": "rgba(42, 151, 8, 1)",
        "hoverinfo": "skip",
    }

    orbit_path = {
        "type": "scatter",
        "x": xs,
        "y": ys,
        "mode": "lines",
        "name": "Trajectoire",
        "visible": False,
        "marker": {"color": "rgba(18, 59, 207, 1)" },
    }

    stride = 10
    xs_anim = xs[::stride]
    ys_anim = ys[::stride]
    n_frames = len(xs_anim)
    mx0, my0 = _disk_xy(float(xs_anim[0]), float(ys_anim[0]), float(r_small), n=60)
    moving_ball = {
        "type": "scatter",
        "x": mx0,
        "y": my0,
        "mode": "lines",
        "fill": "toself",
        "name": "Bille",
        "line": {"width": 1, "color": "rgba(200, 50, 50, 1.0)"},
        "fillcolor": "rgba(200, 50, 50, 1.0)",
        "hoverinfo": "skip",
    }

    # ---------------------------
    # Frames animation
    # ---------------------------
    frames = []
    for i in range(n_frames):
        i0 = max(0, i - trail)

        # trajectoire partielle
        tx = xs_anim[i0:i+1]
        ty = ys_anim[i0:i+1]

        # disque mobile centré sur la position i
        mx, my = _disk_xy(float(xs_anim[i]), float(ys_anim[i]), float(r_small), n=60)

        frame = {
            "name": f"f{i}",
            "data": [
                {"type": "scatter", "x": tx, "y": ty},     # trace 1: orbit_path
                {"type": "scatter", "x": mx, "y": my},     # trace 2: moving_ball
            ],
            "traces": [1, 2]
        }
        frames.append(frame)

    # ---------------------------
    # Layout
    # ---------------------------
    # max_range = max(np.max(np.abs(xs)), np.max(np.abs(ys))) * 1.2

    layout = {
        "xaxis": {"range": [-r0, r0]},
        "yaxis": {"range": [-r0, r0], "scaleanchor": "x"},
        "showlegend": False,
        "updatemenus": [
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶",
                        "method": "animate",
                        "args": [None, {
                            "frame": {"duration": duration_ms, "redraw": True},
                            "fromcurrent": True
                        }]
                    },
                    {
                        "label": "⏸",
                        "method": "animate",
                        "args": [[None], {
                            "frame": {"duration": 0},
                            "mode": "immediate"
                        }]
                    },
                    {
                        "label": "◯",
                        "method": "restyle",
                        "args": [{"visible": True}, [1]],
                        "args2": [{"visible": "legendonly"}, [1]]
                    }
                ]
            }
        ]
    }

    layout["dragmode"] = "pan"
    layout["autosize"] = True

    figure = {
        "data": [center_ball, orbit_path, moving_ball],
        "layout": layout,
        "frames": frames
    }

    return figure


def plot(G=1, M=1000, r0=50.0, v0=3.0, theta_deg=85, gamma=0.005, trail=50, n_frames=10000, duration_ms=10):
    return build_newton_orbit_2d_figure(
        G=G,
        M=M,
        r0=r0,
        v0=v0,
        theta_deg=theta_deg,
        gamma=gamma,
        trail=trail,
        n_frames=n_frames,
        duration_ms=duration_ms
    )
