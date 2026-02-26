class Bille:
    """
    A class representing a ball in a 2D space, with properties for position, velocity, and acceleration.
    """

    def __init__(self, x: float, y: float, vx: float, vy: float):
        self._x = x
        self._y = y
        self._vx = vx
        self._vy = vy
        self._ax = 0.0
        self._ay = 0.0
        self._xs = []
        self._ys = []
        self._zs = []

    def update_position(self, dt: float):
        """
        Updates the position of the ball based on its current velocity and the time step.

        Args:
            dt (float): The time step for the update.
        """
        self._x += self._vx * dt
        self._y += self._vy * dt

    def update_velocity(self, ax: float, ay: float, dt: float):
        """
        Updates the velocity of the ball based on its current acceleration and the time step.

        Args:
            ax (float): The acceleration in the x direction.
            ay (float): The acceleration in the y direction.
            dt (float): The time step for the update.
        """
        self._vx += ax * dt
        self._vy += ay * dt

    @property
    def get_position(self):
        return self._x, self._y

    @property
    def get_velocity(self):
        return self._vx, self._vy

    @property
    def get_acceleration(self):
        return self._ax, self._ay

    @property
    def get_ax(self):
        return self._ax

    @get_ax.setter
    def set_ax(self, ax: float):
        self._ax = ax

    @property
    def get_ay(self):
        return self._ay

    @get_ax.setter
    def set_ay(self, ay: float):
        self._ay = ay

    @property
    def get_x(self):
        return self._x

    @property
    def get_y(self):
        return self._y

    @property
    def get_vx(self):
        return self._vx

    @property
    def get_vy(self):
        return self._vy

    @property
    def get_positions_history(self):
        return self._xs, self._ys, self._zs