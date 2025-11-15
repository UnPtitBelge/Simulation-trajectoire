import numpy as np
from constantes import depth, sigma

class Drap:
    def __init__(self, k_depth, k_sigma, sun_mass, sun_radius, mu):
        self._depth = k_depth * sun_mass
        self._sigma = k_sigma * sun_radius
        self._mu = mu

    @staticmethod
    def h(x, y) -> float:
        r2 = x**2 + y**2
        return -depth * np.exp(-r2 / (2*sigma**2))
    
    @property
    def get_depth(self):
        return self._depth
    
    @property
    def get_sigma(self):
        return self._sigma
    
    @property
    def get_mu(self):
        return self._mu
    