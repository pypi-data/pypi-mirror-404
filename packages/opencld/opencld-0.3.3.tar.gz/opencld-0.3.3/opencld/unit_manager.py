import pint
from pint import UndefinedUnitError
import os


class UnitManager:
    """
    Singleton manager for units of measurement in OpenCLD.

    This class wraps a Pint UnitRegistry and adds:

    - Automatic creation of missing base units.
    - Automatic recognition of SI prefixes (kilo, milli, micro, …).
    - Convenience methods for defining, converting, and formatting units.
    - Ensures only one UnitManager instance exists across the library.

    Parameters
    ----------
    unit_definition_file : str or None, default=None
        Path to a unit definition file (see Pint). If None, a default
        registry is created with built-in definitions.

    Attributes
    ----------
    ureg : pint.UnitRegistry
        The underlying unit registry.
    Q_ : type
        Alias for constructing quantities, i.e. ``ureg.Quantity``.

    Notes
    -----
    - If an undefined unit is encountered, it is auto-registered either
      as a new base unit (``[myunit]``) or as a prefixed version of an
      existing base unit (e.g. ``km`` = 1000 * ``m``).
    - This singleton pattern means all parts of the library share the
      same registry, ensuring unit consistency.
    """

    _instance = None

    def __new__(cls, unit_definition_file=None):
        if cls._instance is None:
            cls._instance = super(UnitManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, unit_definition_file=None):
        if self._initialized:
            return

        # Custom registry with auto-registration of missing units
        class AutoUnitRegistry(pint.UnitRegistry):
            def __call__(self_inner, key):
                while True:
                    try:
                        return super(AutoUnitRegistry, self_inner).__call__(key)
                    except UndefinedUnitError as e:
                        missing_unit = e.unit_names[0]

                        # Try to parse SI prefix
                        for prefix, factor in {
                            'Y': 1e24, 'Z': 1e21, 'E': 1e18, 'P': 1e15, 'T': 1e12,
                            'G': 1e9, 'M': 1e6, 'k': 1e3, 'h': 1e2, 'da': 1e1,
                            'd': 1e-1, 'c': 1e-2, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9,
                            'p': 1e-12, 'f': 1e-15, 'a': 1e-18, 'z': 1e-21, 'y': 1e-24
                        }.items():
                            if missing_unit.startswith(prefix) and len(missing_unit) > len(prefix):
                                base = missing_unit[len(prefix):]
                                if base in self_inner:
                                    definition = f"{missing_unit} = {factor} * {base}"
                                    self_inner.define(definition)
                                    print(f"[UnitManager] Auto-registered unit '{missing_unit}' = {factor} * {base}.")
                                    break
                        else:
                            # Register as a new base unit
                            definition = f"{missing_unit} = [{missing_unit}]"
                            self_inner.define(definition)
                            print(f"[UnitManager] Auto-registered base unit '{missing_unit}' = [{missing_unit}].")

        # Instantiate the registry
        if unit_definition_file:
            self.ureg = AutoUnitRegistry(unit_definition_file)
        else:
            self.ureg = AutoUnitRegistry()

        self.Q_ = self.ureg.Quantity
        self._initialized = True

        print(f"[UnitManager] Loading units from: {unit_definition_file}")

    # ------------------------------------------------------------------
    # API methods
    # ------------------------------------------------------------------
    def define_unit(self, definition: str):
        """
        Define a new custom unit at runtime.

        Parameters
        ----------
        definition : str
            Pint-compatible unit definition, e.g. ``"widget = [widget]"``.
        """
        self.ureg.define(definition)

    def get_quantity(self, value, unit: str):
        """
        Wrap a scalar in a Quantity.

        Parameters
        ----------
        value : float
            Numeric value.
        unit : str
            Unit string.

        Returns
        -------
        pint.Quantity
            Quantity with the given value and unit.
        """
        return value * self.ureg(unit) if unit else value

    def check_compatibility(self, quantity1, quantity2):
        """
        Check whether two quantities are compatible.

        Parameters
        ----------
        quantity1, quantity2 : pint.Quantity
            Quantities to check.

        Returns
        -------
        bool
            True if they are dimensionally compatible.
        """
        return quantity1.check(quantity2)

    def to(self, quantity, target_unit: str):
        """
        Convert a quantity to another unit.

        Parameters
        ----------
        quantity : pint.Quantity
            Quantity to convert.
        target_unit : str
            Target unit.

        Returns
        -------
        pint.Quantity
            Converted quantity.
        """
        return quantity.to(target_unit)

    def format_quantity(self, quantity):
        """
        Format a Quantity as a string with magnitude and units.

        Parameters
        ----------
        quantity : pint.Quantity
            Quantity to format.

        Returns
        -------
        str
            Example: ``"12.5 meter / second"``.
        """
        return f"{quantity.magnitude} {quantity.units}" if hasattr(quantity, 'units') else str(quantity)

    def safe_define(self, definition: str):
        """
        Define a new unit, ignoring duplicates.

        Parameters
        ----------
        definition : str
            Pint-compatible definition.

        Notes
        -----
        If the unit already exists, the definition is skipped.
        """
        try:
            self.ureg.define(definition)
            print(f"[UnitManager] Defined new unit: {definition}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"[UnitManager] Unit already exists, skipping: {definition}")
            else:
                raise ValueError(f"[UnitManager] Error defining unit '{definition}': {str(e)}")

    def batch_define(self, definitions: list):
        """
        Define multiple units safely at runtime.

        Parameters
        ----------
        definitions : list of str
            Unit definitions to register.
        """
        for definition in definitions:
            self.safe_define(definition)

    def force_quantity(self, value, unit):
        """
        Ensure a value is a Quantity, wrapping if needed.

        Parameters
        ----------
        value : float or pint.Quantity
            Value to wrap.
        unit : str
            Unit to apply if ``value`` is not already a Quantity.

        Returns
        -------
        pint.Quantity
            Quantity with units.
        """
        return value if hasattr(value, 'magnitude') else self.get_quantity(value, unit)
