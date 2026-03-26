import numpy as np


def disk_xy(cx, cy, radius, n=64):
    angles = np.linspace(0.0, 2 * np.pi, n, endpoint=True)
    return cx + radius * np.cos(angles), cy + radius * np.sin(angles)
