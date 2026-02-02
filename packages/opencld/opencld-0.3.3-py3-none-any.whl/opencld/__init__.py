import importlib
from typing import TYPE_CHECKING, Any

# --- Version (single source) ---
try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError as _PNF
except Exception:  # pragma: no cover
    from importlib_metadata import version as _pkg_version, PackageNotFoundError as _PNF  # type: ignore

try:
    __version__ = _pkg_version("opencld")
except _PNF:
    __version__ = "0.0.0.dev0"

# --- Core, light imports ---
from .model import Model
from .stock import Stock
from .flow import Flow
from .parameter import Parameter
from .auxiliary import Auxiliary
from .table import Table

# Lowercase convenience aliases (class names remain canonical)
model = Model            # type: ignore[assignment]
stock = Stock            # type: ignore[assignment]
flow = Flow              # type: ignore[assignment]
parameter = Parameter    # type: ignore[assignment]
auxiliary = Auxiliary    # type: ignore[assignment]
table = Table            # type: ignore[assignment]

# Units helpers
from .units import ureg, Q_
from .unit_manager import UnitManager

unit_manager = UnitManager  # type: ignore[assignment]

__all__ = (
    # canonical classes
    "Model", "Stock", "Flow", "Parameter", "Auxiliary", "Table", "UnitManager",
    # lowercase aliases
    "model", "stock", "flow", "parameter", "auxiliary", "table", "unit_manager",
    # units objects
    "ureg", "Q_",
    # lazy module surface
    "plotting",
    # meta
    "__version__",
)

def __getattr__(name: str) -> Any:
    """
    Lazily loads the plotting module or its functions to avoid
    importing heavy dependencies like matplotlib and seaborn upfront.
    """
    # Case 1: The user wants the entire 'plotting' module (e.g., sd.plotting)
    if name == "plotting":
        # Use importlib to perform the import programmatically and safely
        plotting_module = importlib.import_module(".plotting", __name__)
        # Store the imported module in the package's namespace to prevent this function from being called again for 'plotting'
        globals()['plotting'] = plotting_module
        return plotting_module

    # Case 2: The user wants a specific function from plotting (e.g., sd.plot_timeseries)
    plotting_functions = {
        "Plotting",
        "plot_timeseries",
        "plot_alpha_density_lines",
        "plot_variable_facets",
        "plot_structure_graph",
        "plot_all_variables_from_csv",
    }
    if name in plotting_functions:
        # Import the module safely
        plotting_module = importlib.import_module(".plotting", __name__)
        # Store it for future calls
        globals()['plotting'] = plotting_module
        # Return the specific function the user asked for
        return getattr(plotting_module, name)

    # If the name is not found, raise the standard error
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return sorted(
        list(globals().keys())
        + [
            "plotting",
            "Plotting",
            "plot_timeseries",
            "plot_alpha_density_lines",
            "plot_variable_facets",
            "plot_structure_graph",
            "plot_all_variables_from_csv",
        ]
    )

# --- Typing only (no runtime cost) ---
if TYPE_CHECKING:  # pragma: no cover
    from .plotting import (
        Plotting,
        plot_timeseries,
        plot_alpha_density_lines,
        plot_variable_facets,
        plot_structure_graph,
        plot_all_variables_from_csv,
    )
