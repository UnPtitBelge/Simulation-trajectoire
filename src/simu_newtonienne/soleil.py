from constantes import *
import numpy as np
from drap import Drap

class Soleil:
    def __init__(self, radius, mass):
        self._radius = radius
        self._mass = mass
        self._u = np.linspace(0, 2*np.pi, 40)
        self._v = np.linspace(0, np.pi, 20)

        self._X_sun = sun_radius * np.outer(np.cos(self._u), np.sin(self._v))
        self._Y_sun = sun_radius * np.outer(np.sin(self._u), np.sin(self._v))
        self._Z_sun = sun_radius * np.outer(np.ones_like(self._u), np.cos(self._v)) + Drap.h(0, 0)

    @property
    def get_radius(self):
        return self._radius
    
    @property
    def get_mass(self):
        return self._mass
    
    @property
    def get_X_sun(self):
        return self._X_sun
    
    @property
    def get_Y_sun(self):
        return self._Y_sun
    
    @property
    def get_Z_sun(self):
        return self._Z_sun