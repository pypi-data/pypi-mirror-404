from .units import ureg, Q_
import numpy as np

Q_ = ureg.Quantity


class Auxiliary:
    """
    An auxiliary variable that can hold a scalar or a vector of values.
    """

    def __init__(self, name, calculation_function, unit=None, inputs=None, dimensions=None):
        self.name = name
        self.calculation_function = calculation_function
        self.dimensions = dimensions if dimensions is not None else []
        self.value = None  # Will become a Quantity upon calculation
        self.inputs = inputs if inputs is not None else []

        # --- Unit Normalization ---
        if unit is None:
            self.unit = ureg.dimensionless
        elif isinstance(unit, str):
            self.unit = ureg(unit).units
        else:
            self.unit = getattr(unit, "units", unit)

    def calculate_value(self, system_state):
        """
        Compute and validate the auxiliary value (scalar or vector).
        """
        try:
            raw_value = self.calculation_function(system_state)
        except Exception as e:
            print(f"[ERROR] Auxiliary '{self.name}': Error in calculation_function: {e}. Setting to 0.")
            raw_value = 0.0
        
        # Wrap into Quantity, handling numpy arrays
        if isinstance(raw_value, Q_):
            self.value = raw_value
        else:
            self.value = Q_(np.asarray(raw_value), self.unit)

        # Handle NaNs for array/scalar values without triggering ambiguous truth checks
        try:
            magnitude_arr = np.asarray(self.value.magnitude)
            if magnitude_arr.dtype.kind in {"f", "c"} and np.isnan(magnitude_arr).any():
                # Replace NaNs with 0.0 (or choose a policy appropriate for your domain)
                cleaned = np.nan_to_num(magnitude_arr, nan=0.0)
                self.value = Q_(cleaned, self.unit)
        except Exception:
            # If any issue occurs during NaN handling, proceed without modification
            pass

        # Dimensionality check
        if self.value.dimensionality != self.unit.dimensionality:
            raise ValueError(f"[UNIT ERROR] Auxiliary '{self.name}': Dimensionality mismatch.")

        return self.value

    def get_value(self):
        """
        Return the current value.

        Returns
        -------
        pint.Quantity or None
            The latest computed value, or None if not yet calculated.
        """
        return self.value

    def __str__(self):
        if self.value is None:
            return f"{self.name}: None (not calculated)"
        magnitude = self.value.magnitude
        shape_str = f" (shape: {magnitude.shape})" if hasattr(magnitude, 'shape') and magnitude.shape != () else ""
        return f"{self.name}: {magnitude}{shape_str} [{self.unit}]"

    def __repr__(self):
        return (
            f"Auxiliary(name={self.name!r}, "
            f"value={self.value.magnitude if self.value is not None else None!r}, "
            f"unit={str(self.unit)!r}, "
            f"dimensions={self.dimensions!r})"
        )

