from .units import ureg, Q_
import numpy as np

Q_ = ureg.Quantity


class Parameter:
    """
    A parameter that can hold a scalar or a vector of constant values.
    """
    def __init__(self, name: str, value=1.0, unit=None, description=None, dimensions=None):
        self.name = name
        self.description = description
        self.dimensions = dimensions if dimensions is not None else []

        # --- Unit Normalization ---
        if unit is None:
            self.unit = ureg.dimensionless
        elif isinstance(unit, str):
            self.unit = ureg(unit).units
        else:
            self.unit = getattr(unit, "units", unit)

        # --- Handle value (scalar or array) ---
        if isinstance(value, Q_):
            self.value = value.to(self.unit)
        else:
            self.value = Q_(np.asarray(value), self.unit)

    def get_value(self):
        return self.value

    def format_value(self):
        return f"{self.value.magnitude:g} [{self.unit}]"

    def __str__(self):
        magnitude = self.value.magnitude
        shape_str = f" (shape: {magnitude.shape})" if hasattr(magnitude, 'shape') and magnitude.shape != () else ""
        return f"{self.name}: {magnitude}{shape_str} [{self.unit}]"

    def __repr__(self):
        return (
            f"Parameter(name={self.name!r}, "
            f"value={self.value.magnitude!r}, "
            f"unit={str(self.unit)!r}, "
            f"dimensions={self.dimensions!r})"
        )