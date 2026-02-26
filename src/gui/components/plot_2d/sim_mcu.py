import numpy as np

def build_mcu_2d_figure(
    R=2.0,
    omega=2.0,
    n_frames=200,
    duration_ms=90
):
    t = np.linspace(0, 2*np.pi, n_frames)

    xs = R * np.cos(omega * t)
    ys = R * np.sin(omega * t)

    # --- Trace balle centrale (fixe) ---
    center_ball = {
        "type": "scatter",
        "x": [0],
        "y": [0],
        "mode": "markers",
        "name": "Centre",
        "marker": {"size": 20,
                    "color": "rgba(42, 151, 8, 1)"
                   },
    }

    # --- Trace balle orbitale (position initiale) ---
    moving_ball = {
        "type": "scatter",
        "x": [xs[0]],
        "y": [ys[0]],
        "mode": "markers",
        "name": "Orbite",
        "marker": {"size": 12,
                   "color": "rgba(200, 50, 50, 1.0)"
                   },
    }

    # --- Trace cercle (orbite complète) ---
    orbit_circle = {
        "type": "scatter",
        "x": R*np.cos(np.linspace(0, 2*np.pi, 300)),
        "y": R*np.sin(np.linspace(0, 2*np.pi, 300)),
        "mode": "lines",
        "name": "Trajectoire",
        "visible": False,
        "marker": {"color": "rgba(18, 59, 207, 1)" },
    }

    # --- Frames animation ---
    frames = []
    for i in range(n_frames):
        frame = {
            "name": f"f{i}",
            "data": [
                {
                    "type": "scatter",
                    "x": [xs[i]],
                    "y": [ys[i]],
                }
            ],
            "traces": [2]  # index de la balle mobile
        }
        frames.append(frame)

    # --- Layout ---
    layout = {
        "xaxis": {"range": [-100, 100],},
        "yaxis": {"range": [-100, 100],"scaleanchor": "x"},
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

    # Pour pas avoir le zoom dégueulasse
    layout["dragmode"] = "pan"
    layout["autosize"] = True

    figure = {
        "data": [center_ball, orbit_circle, moving_ball],
        "layout": layout,
        "frames": frames
    }

    return figure

def plot(omega=2.0, R=2.0, n_frames=200, duration_ms=30):
    return build_mcu_2d_figure(omega=omega, R=R, n_frames=n_frames, duration_ms=duration_ms)
