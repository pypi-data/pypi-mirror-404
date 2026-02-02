from .units import ureg, Q_
import numpy as np

Q_   = ureg.Quantity


class Flow:
    """
    A flow (rate) that can be a scalar or a vector.
    """

    def __init__(self, name, rate_function, source_stock=None, target_stock=None,
             unit=None, inputs=None, dimensions=None):
        self.name = name
        self.source_stock = source_stock
        self.target_stock = target_stock
        self.rate_function = rate_function
        self.dimensions = dimensions if dimensions is not None else []
        self.rate = Q_(0.0, unit or "")  # Default to scalar zero

        if inputs is None:
            self.inputs = []
        else:
            self.inputs = inputs

        # --- Unit Normalization ---
        if unit is None:
            self.unit = ureg.dimensionless
        elif isinstance(unit, str):
            self.unit = ureg(unit).units
        else:
            self.unit = getattr(unit, "units", unit)

        # Auto-wire to stocks
        if source_stock:
            source_stock.add_outflow(self)
        if target_stock:
            target_stock.add_inflow(self)

    def calculate_rate(self, system_state):
        """
        Compute and validate the flow rate (scalar or vector).
        """
        try:
            raw_rate = self.rate_function(system_state)
        except Exception as e:
            print(f"[ERROR] Flow '{self.name}': Error in rate_function: {e}. Setting to 0.")
            raw_rate = 0.0

        # Wrap into Quantity, handling numpy arrays
        if isinstance(raw_rate, Q_):
            self.rate = raw_rate
        else:
            self.rate = Q_(np.asarray(raw_rate), self.unit)
        
        # Dimensionality check
        if self.rate.dimensionality != self.unit.dimensionality:
            raise ValueError(f"[UNIT ERROR] Flow '{self.name}': Dimensionality mismatch.")

        return self.rate

    def get_rate(self):

        return f"{self.rate} [{self.unit}]"

    def __str__(self):
        magnitude = self.rate.magnitude
        shape_str = f" (shape: {magnitude.shape})" if hasattr(magnitude, 'shape') and magnitude.shape != () else ""
        return f"{self.name}: {magnitude}{shape_str} [{self.unit}]"

    def __repr__(self):
        return (
            f"Flow(name={self.name!r}, "
            f"rate={self.rate.magnitude!r}, "
            f"unit={str(self.unit)!r}, "
            f"dimensions={self.dimensions!r})"
        )