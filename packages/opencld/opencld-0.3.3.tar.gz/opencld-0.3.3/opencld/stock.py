from .units import ureg, Q_, format_quantity
import numpy as np

Q_   = ureg.Quantity


class Stock:
    """
    A stock (level) that can hold a scalar or a vector of values.
    """

    def __init__(self, name: str, initial_value=0.0, unit=None, dimensions=None):
        self.name = name
        self.dimensions = dimensions if dimensions is not None else []

        # --- Normalize unit ---
        if unit is None:
            self.unit = ureg.dimensionless
        elif isinstance(unit, str):
            self.unit = ureg(unit).units
        else:
            self.unit = getattr(unit, "units", unit)

        # --- Handle initial value (scalar or array) ---
        if isinstance(initial_value, Q_):
            self.initial_value = initial_value.to(self.unit)
        else:
            # Manage both scalar and arrays, coercing to float to avoid int casting issues
            self.initial_value = Q_(np.asarray(initial_value, dtype=float), self.unit)

        self.value = self.initial_value.copy()  # Ensure it's a copy
        self.inflows = []
        self.outflows = []

    def add_inflow(self, flow):
        self.inflows.append(flow)

    def add_outflow(self, flow):
        self.outflows.append(flow)

    def update(self, timestep):
        """
        Advance the stock by one timestep using vectorized operations.
        """
        # Initialize net_flow as a zero array with the correct shape and units
        net_flow_shape = self.value.shape
        net_flow_unit = self.unit / timestep.units
        net_flow = Q_(np.zeros(net_flow_shape), net_flow_unit)

        for inflow in self.inflows:
            net_flow += inflow.rate
        for outflow in self.outflows:
            net_flow -= outflow.rate

        self.value = self.value + (net_flow * timestep)

    def get_value(self):
        return format_quantity(self.value)

    def __str__(self):
        magnitude = self.value.magnitude
        # Display shape for vector quantities
        shape_str = f" (shape: {magnitude.shape})" if hasattr(magnitude, 'shape') and magnitude.shape != () else ""
        return f"{self.name}: {magnitude}{shape_str} [{self.unit}]"

    def __repr__(self):
        return (
            f"Stock(name={self.name!r}, "
            f"value={self.value.magnitude!r}, "
            f"unit={str(self.unit)!r}, "
            f"dimensions={self.dimensions!r})"
        )