import numpy as np


class Table:
    """
    Piecewise-linear lookup with interpolation and boundary extrapolation.

    A Table approximates arbitrary nonlinear functions using discrete
    (x, y) breakpoints. Between breakpoints, linear interpolation is used.
    Outside the range, the nearest boundary value is returned.

    Parameters
    ----------
    x_values : 1-D array-like
        Breakpoint abscissae. Must be monotonically non-decreasing.
    y_values : 1-D array-like
        Ordinates corresponding to each entry of `x_values`.
    name : str, default="Table"
        Label used in print and repr outputs.

    Attributes
    ----------
    x_values : ndarray of float
        Breakpoint x-values (monotonically non-decreasing).
    y_values : ndarray of float
        Breakpoint y-values.
    name : str
        Label for this table.

    Examples
    --------
    >>> tbl = Table([0, 2, 4], [0, 10, 20], name="Linear-2x")
    >>> tbl.lookup(1)
    5.0
    >>> tbl(3)   # __call__ shorthand
    15.0
    >>> print(tbl)
    Table 'Linear-2x' (3 points, x∈[0.0…4.0])
    """

    def __init__(self, x_values, y_values, name: str = "Table"):
        if len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must have identical length.")

        if len(x_values) < 2:
            raise ValueError("Table needs at least two points for interpolation.")

        x_arr = np.asarray(x_values, dtype=float)
        y_arr = np.asarray(y_values, dtype=float)

        if np.any(np.diff(x_arr) < 0):
            raise ValueError("x_values must be monotonically increasing (or equal).")

        self.x_values = x_arr
        self.y_values = y_arr
        self.name     = name

    def lookup(self, x):
        """
        Interpolate value(s) at given x.

        Linear interpolation is used between breakpoints; for values
        outside the range, the nearest endpoint is returned.

        Parameters
        ----------
        x : float or array-like
            Abscissa value(s) where the table is evaluated.

        Returns
        -------
        float or ndarray
            Interpolated ordinate(s).
        """
        return np.interp(x, self.x_values, self.y_values)

    def __call__(self, x):
        """
        Shorthand for :meth:`lookup`.

        Parameters
        ----------
        x : float or array-like
            Input value(s).

        Returns
        -------
        float or ndarray
            Interpolated ordinate(s).
        """
        return self.lookup(x)

    def __str__(self):
        """
        Human-friendly summary.

        Returns
        -------
        str
            Example: ``"Table 'Linear-2x' (3 points, x∈[0.0…4.0])"``.
        """
        return (
            f"Table '{self.name}' "
            f"({len(self.x_values)} points, "
            f"x∈[{self.x_values[0]}…{self.x_values[-1]}])"
        )

    def __repr__(self):
        """
        Developer-oriented representation.

        Shows full arrays if short; otherwise truncates to the first 3
        and last 2 points.

        Returns
        -------
        str
            Example:
            ``"Table(name='Linear-2x', x_values=[0.0, 2.0, 4.0], y_values=[0.0, 10.0, 20.0])"``.
        """
        if len(self.x_values) <= 6:
            xs = self.x_values.tolist()
            ys = self.y_values.tolist()
        else:
            xs = [*self.x_values[:3], "...", *self.x_values[-2:]]
            ys = [*self.y_values[:3], "...", *self.y_values[-2:]]

        return (
            f"Table(name={self.name!r}, "
            f"x_values={xs}, "
            f"y_values={ys})"
        )