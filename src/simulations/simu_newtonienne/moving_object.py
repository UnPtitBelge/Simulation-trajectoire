class MovingObject:
    """
    Generic moving object for 2D motion integration.

    Attributes:
        _x, _y (float): Position components.
        _vx, _vy (float): Velocity components.
        _ax, _ay (float): Acceleration components (updated externally).
        _xs, _ys, _zs (list[float]): Position history for x, y, and surface height z.

    Methods:
        update_position(dt): Integrate position using current velocity.
        update_velocity(ax, ay, dt): Integrate velocity using provided acceleration.
        History access via `positions_history` property.
    """

    def __init__(self, x: float, y: float, vx: float, vy: float):
        self._x = float(x)
        self._y = float(y)
        self._vx = float(vx)
        self._vy = float(vy)
        self._ax = 0.0
        self._ay = 0.0
        self._xs: list[float] = []
        self._ys: list[float] = []
        self._zs: list[float] = []

    def update_position(self, dt: float) -> None:
        """Update position using current velocity."""
        self._x += self._vx * dt
        self._y += self._vy * dt

    def update_velocity(self, ax: float, ay: float, dt: float) -> None:
        """Update velocity using provided acceleration."""
        self._vx += ax * dt
        self._vy += ay * dt

    # --- Generic getters ----------------------------------------------------

    @property
    def position(self) -> tuple[float, float]:
        """Return current (x, y)."""
        return self._x, self._y

    @property
    def velocity(self) -> tuple[float, float]:
        """Return current (vx, vy)."""
        return self._vx, self._vy

    @property
    def acceleration(self) -> tuple[float, float]:
        """Return current (ax, ay)."""
        return self._ax, self._ay

    # --- Component getters and setters -------------------------------------

    @property
    def ax(self) -> float:
        return self._ax

    @ax.setter
    def ax(self, value: float) -> None:
        self._ax = float(value)

    @property
    def ay(self) -> float:
        return self._ay

    @ay.setter
    def ay(self, value: float) -> None:
        self._ay = float(value)

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def vx(self) -> float:
        return self._vx

    @property
    def vy(self) -> float:
        return self._vy

    # --- History ------------------------------------------------------------

    @property
    def positions_history(self) -> tuple[list[float], list[float], list[float]]:
        """
        Return position history lists (xs, ys, zs).

        Notes:
            zs is typically filled externally with a surface height h(x, y).
        """
        return self._xs, self._ys, self._zs
