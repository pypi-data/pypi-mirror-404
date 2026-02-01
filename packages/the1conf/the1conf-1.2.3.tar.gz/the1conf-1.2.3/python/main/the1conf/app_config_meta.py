from __future__ import annotations

import copy
from collections import OrderedDict
from inspect import getsource
from typing import Any, Iterable, cast
from .config_var import ConfigVarDef
from .utils import get_attribute_docstrings, NameSpace


class ConfigVarCollector:
    """
    Collector class to gather ConfigVarDef from AppConfig classes and their nested NameSpace classes.

    This class helps in aggregating configuration variables from various sources during the class creation process.
    It supports two main collection strategies:
    1. Parsing the class definition directly (useful for mixins or the root class).
    2. Inheriting already collected variables from a parent `AppConfig` class (optimization).

    This class can be used as a context manager to ensure proper resource management.
    """

    _collected_vars: OrderedDict[str, ConfigVarDef]
    _auto_prolog_var_names: list[str]

    def __enter__(self):
        """Return self to be used in the with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources on exit"""
        self.close()

    def __init__(self) -> None:
        """Create a new ConfigVarCollector instance."""
        self._collected_vars = OrderedDict()
        self._auto_prolog_var_names = []

    def close(self) -> None:
        """
        Clean up resources if needed.
        """
        self._collected_vars.clear()
        self._auto_prolog_var_names.clear()

    def _collect_config_vars(
        self, owner: type, prefix: str = ""
    ) -> Iterable[ConfigVarDef]:
        """
        Traverses ConfigVarDef defined in the owner class and its nested NameSpace classes.
        Search for ConfigVarDef in the owner class __dict__ and yield them.
        Attach the docstrings as help if help is not already defined and a docstring exists
        for the attribute.
        change its name by adding the namespace it is defined in as a prefix.
        """
        # extract docstrings from the class source code
        docstrings = get_attribute_docstrings(owner)

        # Inspect the class __dict__ to find ConfigVarDef defined in this class
        for attr_name, value in owner.__dict__.items():
            if isinstance(value, ConfigVarDef):
                # Clone to update name with prefix
                new_var = value

                # If help is missing, try to use the docstring
                if not new_var.help and attr_name in docstrings:
                    new_var._help = docstrings[attr_name]

                if prefix:
                    # We need to access _name directly because we don't want to trigger the
                    # descriptor __get__ method
                    original_name = getattr(value, "_name", attr_name)
                    new_var._name = f"{prefix}{original_name}"

                yield new_var

            elif (
                isinstance(value, type)
                and issubclass(value, NameSpace)
                and value is not NameSpace
            ):
                # Recurse into nested NameSpace classes
                yield from self._collect_config_vars(
                    value, prefix=f"{prefix}{attr_name}."
                )

    def collect_on_class(self, owner: type) -> None:
        """
        Collect configuration variables by inspecting the class `__dict__` and its nested `NameSpace`s.

        This method is used when the class does not have a `_config_var_defs` attribute yet,
        typically for mixins (like AutoProlog) or during the initialization of the root `AppConfig` class.

        It performs a deep scan:
        - Iterates over the class attributes to find `ConfigVarDef` instances.
        - Extracts docstrings to use as help text if needed.
        - Recurses into nested `NameSpace` classes to collect variables defined within them.

        Any variable found overrides an existing variable with the same name in the collection.
        """
        for vardef in self._collect_config_vars(owner):
            attr_name = getattr(vardef, "_name", None)
            if attr_name:
                if attr_name in self._collected_vars:
                    # Override previous definition
                    self._collected_vars.pop(attr_name)
                self._collected_vars[attr_name] = vardef
                if attr_name and vardef.auto_prolog:
                    if attr_name in self._auto_prolog_var_names:
                        # in this case we need to move the var_name to the end of the list to preserve the order
                        self._auto_prolog_var_names.remove(attr_name)
                    self._auto_prolog_var_names.append(attr_name)

    def collect_in_config_var_defs(self, owner: type) -> None:
        """
        Collect configuration variables from the `_config_var_defs` attribute of the owner class.

        This method is used during inheritance when the parent class (`owner`) is already a subclass
        of `AppConfig`. Since the parent has already computed its configuration variables (stored in
        `_config_var_defs`), we can simply copy them instead of re-scanning the class.

        This is much faster than `collect_on_class` and preserves the resolution order established
        in the parent class.

        Any variable found overrides an existing variable with the same name in the collection.
        """
        base_config_var_defs = getattr(owner, "_config_var_defs", None)
        if not base_config_var_defs:
            return

        assert isinstance(base_config_var_defs, OrderedDict)

        for var_name, var_def in cast(
            OrderedDict[str, ConfigVarDef], base_config_var_defs
        ).items():
            # base_config_var_defs is the _config_var_defs dict. Loops on each of its elements and store them in the collected list
            # For each one read its name. If the variable name is already in the collected list, it means that it has been
            # defined in a parent class of the current inspected base class. So we remove the old definition and add the new one.
            if var_name:
                if var_name in self._collected_vars:
                    # Override previous definition
                    self._collected_vars.pop(var_name)
                self._collected_vars[var_name] = var_def
                if var_name and var_def.auto_prolog:
                    if var_name in self._auto_prolog_var_names:
                        # in this case we need to move the var_name to the end of the list to preserve the order
                        self._auto_prolog_var_names.remove(var_name)
                    self._auto_prolog_var_names.append(var_name)

    def get_collected_vars(self) -> OrderedDict[str, ConfigVarDef]:
        """
        Get the collected configuration variables.
        """
        return self._collected_vars.copy()

    def get_auto_prolog_var_names(self) -> list[str]:
        """
        Get only the collected configuration variables that have auto_prolog enabled.
        """
        return self._auto_prolog_var_names.copy()


class AppConfigMeta(type):
    """
    Metaclass for AppConfig to handle initialization of the root class itself,
    specifically to collect configuration variables from mixins that are not AppConfig subclasses.
    """

    def __init__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> None:
        """
        Initialize the class object.

        This method is part of the Python metaclass protocol. It is invoked after the class object `cls`
        has been created (usually via `type.__new__`). It effectively acts as a constructor for the class
        object itself.

        Args:
            name (str): The name of the class being created.
            bases (tuple[type, ...]): A tuple containing the base classes of the class being created.
            attrs (dict[str, Any]): A dictionary containing the class namespace (attributes and methods)
                                  populated during the execution of the class body.
                                  Keys are the names of the attributes (strings) and values are the
                                  attribute values (methods, class variables, properties, etc.).
        """
        super().__init__(name, bases, attrs)

        # Only perform root initialization for the AppConfig class itself.
        # Subclasses use the standard __init_subclass__ mechanism.
        if name == "AppConfig":
            with ConfigVarCollector() as collector:
                for base in reversed(cls.__mro__[1:-1]):
                    # For the root class initialization we want to scan all parents.
                    # We want to include variables from mixins like AutoProlog.
                    # Since AppConfig is the root for this mechanism, its parents don't have _config_var_defs.
                    # In the mro list AppConfig is always at index 0, so we can skip it safely and the last item is always object which we can also skip.

                    collector.collect_on_class(base)
                # Add own vars
                collector.collect_on_class(cls)

                cls._config_var_defs = collector.get_collected_vars()
                cls._autoprolog_var_names = collector.get_auto_prolog_var_names()
