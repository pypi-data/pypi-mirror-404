import os
# Use a relative import since unit_manager is in the same package
from .unit_manager import UnitManager


def get_unit_file_path(filename=None):
    """
    Locate the unit definition file.
    """
    default_file = os.path.join(os.getcwd(), "units.txt")
    if os.path.isfile(default_file):
        return default_file
    return os.path.join(os.path.dirname(__file__), "my_units.txt")


def load_units(filename=None):
    """
    Initialize a UnitManager from the given unit file.
    """
    path = get_unit_file_path(filename)
    return UnitManager(path)



# Default UnitManager instance, created on import.
# This object is kept for internal consistency.
_manager = load_units()


# These two lines make ureg and Q_ directly importable from this module.
ureg = _manager.ureg
Q_ = _manager.Q_
get_quantity = _manager.get_quantity
format_quantity = _manager.format_quantity