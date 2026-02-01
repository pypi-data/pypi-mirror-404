from __future__ import annotations

import copy

import json
import logging
import os

from collections import OrderedDict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Callable, Optional, Union, cast

from .auto_prolog import AutoProlog
import toml
import yaml
from pydantic import TypeAdapter, ValidationError

from .attr_dict import AttrDict
from .utils import is_sequence, Undefined
from .config_var import ConfigVarDef, Flags
from .solver import Solver
from .var_substitution import resolve_candidate_list
from .utils import _undef
from .app_config_meta import AppConfigMeta, ConfigVarCollector


class AppConfig(AttrDict, AutoProlog, metaclass=AppConfigMeta):
    """ "
    A class to manage application configuration. It can be passed from callable to callable.
    It can search for variable values in command line arguments, environment variables, a yaml or json configuration file
    or a default value or a computed value.

    Configuration variable are defined with a list of ConfigVarDef object which defines how to look for the variable values and/or compute them.

    The variable values are searched in these locations in the following order:
    - a dict of values usually passed from the command line arguments
    - environment variables
    - a configuration file in yaml or json format
    - a default value or a computed value
    The first match found is used as the value for the variable.

    When found the variable can be casted to a specific type and/or transformed with a callable.

    The default value can also be computed with a callable that can use already defined variables in this AppConfig object.
    One can combine a default value and a transformation callable to compute complex default values that can combine several already defined variables,
    knowing that variables are resolved in the order they are declared in the AppConfig subclass.

    See method 'resolve_vars()' and class 'ConfigVarDef' for more information.

    Variable can also be set directly like in an object attribute or in a Dict key:

    ctx = AppConfig()
    ctx["var"] = 2
    print(ct.var) # print 2

    Accessing the variables can also be done like an object attribute or a Dict key:
    ctx = AppConfig()
    ctx.var = 2
    print(ctx["var"]) # print 2

    This can be useful to mix known variable name and variable dynamically defined in a file or passed from the command line.
    def foo(ctx: AppConfig,attname:Any) -> Any:
        return ctx[attname]

    Variable can contain variable recursively, in this case they can be access with a dotted notation or with a dict like way:
    ctx = AppConfig()
    ctx["var1.var2"] = 2
    ctx["var1.var3"] = 3
    print(f"var1 = {ctx.var1}") # print a dict {"var2":2,"var3":3}

    print(ctx.var1.var2) # print 2

    Declarative Configuration:
    --------------------------
    Configuration is best defined declaratively by subclassing AppConfig:

        class MyConfig(AppConfig):
            host: str = configvar(default="localhost")
            port: int = configvar(default=8080)

    Nested Namespaces:
    ------------------
    Variables can be grouped into namespaces using nested classes inheriting from NameSpace.
    This creates a structured configuration:

        class MyConfig(AppConfig):
            # Root level variable
            debug: bool = configvar(default=False)

            # Nested namespace 'db'
            class db(NameSpace):
                host: str = configvar(default="db.local")
                port: int = configvar(default=5432)

            # Nested namespace 'api'
            class api(NameSpace):
                key: str = configvar(env_name="API_KEY")

    inst = MyConfig()
    inst.resolve_vars()
    print(inst.db.host)  # Access nested variables

    Decentralized Configuration (Mixins):
    -------------------------------------
    Configuration can be split across multiple classes (Mixins) and combined using inheritance.
    This allows different modules to define their own configuration requirements.

        class DatabaseConfig(AppConfig):
            class db(NameSpace):
                host: str = configvar(default="localhost")

        class ApiConfig(AppConfig):
            class api(NameSpace):
                timeout: int = configvar(default=30)

        # Combine into the final application config
        class App(DatabaseConfig, ApiConfig):
            pass

    If multiple mixins define the same namespace (e.g. `class db(NameSpace)`), their variables are merged.
    """

    _logger = logging.getLogger(__name__)
    _global_flags: Flags
    _config_var_defs: OrderedDict[str, ConfigVarDef]
    """ The list of ConfigVarDef defined in this AppConfig class and its parent classes as an ordered dictionary. 
        This attribute is created at class creation time by the __init_subclass__ method.
    """
    _autoprolog_var_names: list[str]
    """ The list of the names of ConfigVarDef defined in AutoProlog.
        This attribute is created at class creation time by the __init_subclass__ method.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Call when a subclass inherits from AppConfig.

        Create the _config_var_defs attribute that contains the list of ConfigVarDef
        defined in this subclass as well as the ones defined in parent classes.

        This method also handle namespaces defined with nested classes inheriting from NameSpace.
        1. It first collects the _config_var_defs from parent classes to handle mixins, when a variable is found in a parent class with the same name as a variable in a child class,
            the child class variable takes precedence, thus we remove the parent class variable from the collected list before adding the child class variable.
        2. Then it inspects the class __dict__ to find ConfigVarDef defined in this class (and nested classes) and add them to the collected list.
            Collecting ConfigVarDef in this class is done by the collect_vars() class method which is called recursively on nested NameSpace classes
            and which is also search for docstrings to attach them as help to the ConfigVarDef if help is not already defined.
        3. Finally it sets the _config_var_defs attribute on the class.

        """
        # First call super to handle any parent class logic
        super().__init_subclass__(**kwargs)

        with ConfigVarCollector() as collector:
            # try to look if there is already a _config_var_defs attribute in one of the parent classes.

            for base in reversed(cls.__mro__[1:-1]):
                # __mro__ contain:
                #    1. The class of the object (class of cls here, which is this class)
                #    2. The hierarchy of the parent classes in the MRO order which goes from left to right at each level and from the level
                #       closest to the object to one deeper in the tree.
                #    3. The Object class which is the latest class in the inheritance tree.
                # Here we skip the first element which is the class of the object itself (cls) and the last which is Object class and we traverse
                # it in reverse order.

                collector.collect_in_config_var_defs(base)

            # Now inspect the class __dict__ to find ConfigVarDef defined in this class (and nested classes) and add them to the collected list.
            # note that collect_config_vars is defined in the metaclass.
            collector.collect_on_class(cls)
            cls._config_var_defs = collector.get_collected_vars()
            cls._autoprolog_var_names = collector.get_auto_prolog_var_names()

    def __init__(
        self,
        *,
        no_env_search: Optional[bool] = None,
        no_key_search: Optional[bool] = None,
        no_conffile_search: Optional[bool] = None,
        no_search: Optional[bool] = None,
        allow_override: Optional[bool] = None,
        click_key_conversion: Optional[bool] = None,
    ):
        """Init the config.

        Arguments are called 'global flags', they specify the behavior of the variable resolution globaly. They can be overiden
        when the resolve method is call. (this method can be call several time and thus on each call some flags can be changed) or
        per variable when defining the ConfigVarDef object.

        Global Flags:
            no_env_search (bool, optional): don't search values in the environment. Defaults to False.
            no_key_search (bool, optional): don't search values in the value dictionary. Defaults to False.
            no_conffile_search (bool, optional): don't search values in the configuration file. Defaults to False.
            no_search (bool, optional): don't search values in any location. Defaults to False.
            allow_override (bool, optional): allow overriding variable in the configuration when calling resolve_vars.
                it happens either when resolve_vars() is call several times or the variable was set before its call.
            click_key_conversion (bool, optional): use the variable name converted to lower case and with dashes converted to underscores as
            the key to search in values. Defaults to False.
        """
        self._global_flags = Flags(
            no_env_search=no_env_search,
            no_value_search=no_key_search,
            no_conffile_search=no_conffile_search,
            no_search=no_search,
            click_key_conversion=click_key_conversion,
            allow_override=allow_override,
        )

        self._logger.debug("init AppConfig")

    def clone(self) -> AppConfig:
        """cloning the AppConfig object"""
        clone = AppConfig()
        clone.__dict__ = self.__dict__.copy()
        return clone

    def _set_value(self, name: str, value: Any) -> None:
        """Set a value.

        Use an AttrDict implementation to handle dotted keys and not trigger recursion loops
        if called from a descriptor.
        """
        self[name] = value

    def _get_eval_runner(
        self,
    ) -> Callable[[Callable[[str, Any, Any], Any], str, Any], Any]:
        """
        Call a Callable found in a Eval Form.
        """
        this = self

        def runner(
            callable: Callable[[str, Any, Any], Any], var_name: str, var_val: Any
        ) -> Any:
            return callable(var_name, this, var_val)

        return runner

    def _resolve_conffile_path(
        self, candidates: Optional[str | Path | Iterable[str | Path]]
    ) -> Path | None:
        if candidates is None:
            return None

        # Normalize candidates to list of str for resolve_candidate_list
        candidates_str_list: list[str] = []
        if isinstance(candidates, (str, Path)):
            candidates_str_list = [str(candidates)]
        elif is_sequence(candidates):
            candidates_str_list = [str(c) for c in cast(Sequence[Any], candidates)]

        # Define existence check
        def file_exists(p: str) -> Any:
            path_obj = Path(p)
            if path_obj.is_file():
                return path_obj
            else:
                return _undef

        # Build context for Jinja with current values resolved
        context = self.to_dict()

        # Resolve using current self as context (for jinja variables)
        resolved_path = resolve_candidate_list(
            candidates=candidates_str_list, context=context, check_exists=file_exists
        )

        return resolved_path

    def resolve_vars(
        self,
        *,
        scopes: Optional[str | Iterable[str]] = None,
        values: Mapping[str, Any] = {},
        no_env_search: Optional[bool] = None,
        no_value_search: Optional[bool] = None,
        no_conffile_search: Optional[bool] = None,
        no_search: Optional[bool] = None,
        conffile_path: Optional[Path | str | Sequence[str | Path]] = None,
        allow_override: Optional[bool] = None,
        click_key_conversion: Optional[bool] = None,
    ) -> None:
        """
        Resolve the configuration variables defined in this AppConfig object.
        The variable values are searched in these locations in the following order:
        - a dict of values usually passed from the command line arguments
        - environment variables
        - a configuration file in yaml or json format
        - a default value or a computed value
        The first match found is used as the value for the variable.
        When found the variable can be casted to a specific type and/or transformed with a callable.
        The default value can also be computed with a callable that can use already defined variables in this AppConfig object.
        One can combine a default value and a transformation callable to compute complex default values that can combine several already defined variables,
        knowing that variables are resolved in the order they are declared in the AppConfig subclass.
        """

        self._logger.info(
            f"Starting variable resolution, conf file = {str(conffile_path)}  "
        )

        # Compute flags that can be override locally.
        resolve_flags = Flags(
            no_env_search=no_env_search,
            no_value_search=no_value_search,
            no_conffile_search=no_conffile_search,
            no_search=no_search,
            click_key_conversion=click_key_conversion,
            allow_override=allow_override,
        )
        local_flags = self._global_flags.merge(inplace=False, other=resolve_flags)
        assert local_flags is not None

        # building the Solver who is in charge of resolving configuration variables
        solver = Solver(
            eval_runner=self._get_eval_runner(),
            flags=local_flags,
            values_map=values,
            var_solved=self,
        )

        # Special case for auto_prolog variable: we need to try to solve them
        # before any other variable and before resolving the configuration file path because
        # it can depends on one of them, the one that can be ovveriden are resolved at each run
        for var_name in self._autoprolog_var_names:
            vardef = self._config_var_defs.get(var_name)
            if vardef is None:
                continue
            if self.has_value(var_name) and not (
                local_flags.allow_override or vardef.flags.allow_override
            ):
                continue
            # call solver to try to find a value for the configuration variable
            value_found = solver.resolve_confvar(var_to_solve=vardef, scopes=scopes)
            if value_found != _undef:
                self._set_value(var_name, value_found)

        # Read configuration file if requiered
        conf_file_vars = None
        if not local_flags.no_conffile_search and conffile_path is not None:
            # Resolve conffile_path if it's dynamic
            cur_conffile_path = self._resolve_conffile_path(conffile_path)

            if cur_conffile_path is not None and cur_conffile_path.is_file():
                with cur_conffile_path.open("r") as f:
                    if cur_conffile_path.suffix.lower() == ".json":
                        self._logger.debug(f"Parsing json file {cur_conffile_path}")
                        conf_file_vars = json.load(f)
                    elif cur_conffile_path.suffix.lower() == ".toml":
                        self._logger.debug(f"Parsing toml file {cur_conffile_path}")
                        conf_file_vars = toml.load(f)
                    else:
                        self._logger.debug(
                            f"Parsing file {cur_conffile_path} with suffix {cur_conffile_path.suffix.lower()}"
                        )
                        conf_file_vars = yaml.safe_load(f)
                    # updating the solver with the values found in the configuration file
                    solver.set_conffile_values_map(conf_file_vars)
            else:
                self._logger.info(f"configuration file {cur_conffile_path} not found.")

        # Read the var definitions one by one in their definition order
        for var_name, var_def in self._config_var_defs.items():

            # Check if variable is manually set on the instance or resolved in a previous pass
            has_value = self.has_value(var_name)

            # compute the current flags for this variable by merging local flags with variable flags
            cur_flags = local_flags.merge(inplace=False, other=var_def.flags)
            assert cur_flags is not None

            # if the variable is already defined and override is not allowed then
            # we skip it (First valid scope wins).
            if not cur_flags.allow_override and has_value:
                continue

            # call solver to try to find a value for the configuration variable
            value_found = solver.resolve_confvar(var_to_solve=var_def, scopes=scopes)
            if value_found != _undef:
                self._logger.info(
                    f"Variable '{var_name}' resolved to: {str(value_found)}"
                )
                # add the found value to the AppConfig object through the AttrDict implementation.
                self._set_value(var_name, value_found)
            else:
                self._logger.debug(f"Variable '{var_def.name}' could not be resolved.")

    def _serialize_var_defs(
        self, vardef_to_serialize: Iterable[ConfigVarDef], for_file: bool = False
    ) -> dict[str, Any]:
        """
        Serialize the given variable definitions to a dictionary.
        We know that values came from strings and that they are either alone or in a list.
        Thus we can just use str() to serialize them.
        To detect list we need to look at the split_to_list attribute of the ConfigVarDef and call str() on
        each element of the list, then join them with the separator used to create the list.
        If for_file is True we serialize only variables that have no_conffile_search set to False and
        used file_key as the key in the dict, otherwise the key is the variable name.
        """
        # we are going to take advantage of the AttrDict to accept dotted keys in order to create nested dicts.
        dumper = AttrDict()
        for var in vardef_to_serialize:
            if for_file and not var.flags.no_conffile_search:
                key = var.file_key
            elif not for_file:
                key = var.name
            else:
                continue

            sep = var.split_to_list if isinstance(var.split_to_list, str) else ","
            if var.split_to_list:
                val_list = [str(v) for v in self[var.name]]
                val = sep.join(val_list)
            else:
                val = str(self[var.name])

            dumper[key] = val

        return cast(dict[str, Any], dumper.to_dict())

    def store_conf_infile(
        self,
        file: Union[Path, str],
        *,
        namespaces: Sequence[str] = [],
        scopes: Sequence[str] = [],
        type: str = "yaml",
    ) -> None:
        """
        Store the current configuration in a file by merging the variables in the file with the one in this Appconfig object.
        The method writes the variables in a file.
        The variables to write must be in one of the specified namespaces and have one of the specified scopes.

        Args:
            file (Path | str ): The path to the file where to write the configuration.
            namespaces (Sequence[str], optional): A list of namespaces dotted names to filter the variables to write. Defaults to [].
            scopes (Sequence[str], optional): A list of scopes to filter the variables to write. Defaults to [].
            type (str, optional): The type of the file to write. Can be "yaml", "json" or "toml". Defaults to "yaml".
        """

        def get_vars_to_dump() -> Iterable[ConfigVarDef]:
            """
            loop over variable definitions to select the variables to dump. we use a separate function
            in ordre to return a generator to avoid double list traversal
            """
            for var in self._config_var_defs.values():

                # check namespaces filter if any
                if namespaces:
                    # if the variable is not in one of the requested namespaces skip it
                    if not any(var.name.startswith(prefix) for prefix in namespaces):
                        continue

                # check scope filter if any
                if scopes:
                    # if the variable is specific to some scopes check if one of them is in the requested scopes
                    if var.scopes is not None:
                        if not any(ctx in var.scopes for ctx in scopes):
                            continue

                # check if the variable should be in the file
                # redondant because file_key is None only if no_conffile_search is True, but useful for type checker that knwos that file_key is not None.
                if var.flags.no_conffile_search or var.file_key is None:
                    continue

                yield var

        if type not in ["json", "yaml", "toml"]:
            raise ValueError(
                f"Unknown type {type}. Supported types are 'json', 'toml' and 'yaml'."
            )
        data: dict[str, Any] = {}

        data = self._serialize_var_defs(get_vars_to_dump())
        if isinstance(file, str):
            file = Path(file)

        # if possible we need to read the file in order to inject our data into it and
        # not remove data in the file that we don't have in configuration.
        if file.exists() and os.access(file, os.R_OK):
            # file exists and is readable, we open it in read mode to load existing data
            with file.open("r", encoding="utf-8") as f:
                if type == "json":
                    existing_data = json.load(f)
                elif type == "yaml":
                    existing_data = yaml.safe_load(f)
                else:
                    existing_data = toml.load(f)
            # merge existing data with new data
            existing_data.update(data)
            data = existing_data
        if not file.parent.exists():
            file.parent.mkdir(parents=True, exist_ok=True)

        with file.open("w", encoding="utf-8") as f:
            if type == "json":
                json.dump(data, f, indent=4)
            elif type == "yaml":
                yaml.safe_dump(data, f)
            else:
                toml.dump(data, f)

    def serialize(self) -> dict[str, Any]:
        """Serialize the AppConfig to a dictionary."""
        return self._serialize_var_defs(self._config_var_defs.values())

    def __repr__(self) -> str:
        return str(self.to_dict())

    def __str__(self) -> str:
        return json.dumps(self.serialize(), indent=2, sort_keys=True, default=str)
