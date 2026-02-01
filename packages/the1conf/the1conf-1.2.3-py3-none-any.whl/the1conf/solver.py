from __future__ import annotations

import logging
import os
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, cast
from .config_var import ConfigVarDef, Flags
from .attr_dict import AttrDict
from .utils import AppConfigException, Undefined, _undef, is_sequence, PathType
from .var_substitution import render_template, resolve_candidate_list
from pydantic import TypeAdapter, ValidationError
from pathlib import Path


class Solver:
    """Class responsible for solving configuration variables values
    according to the defined search order and applying transformations and validations."""

    _logger = logging.getLogger(__name__)
    _local_flags: Flags
    _values_map: Mapping[str, Any]
    """ The values provided directly to the AppConfig instance."""
    _conffile_values_map: Optional[Mapping[str, Any]] = None
    """ The values found in the configuration file."""
    _eval_runner: Callable[[Callable[[str, Any, Any], Any], str, Any], Any]
    """ The function that will run the evaluation of callables for default values and transformations."""
    _var_solved: AttrDict
    """ currently solved config var. Used to handle dependencies between variables and variable substitution """

    def __init__(
        self,
        *,
        flags: Flags,
        values_map: Mapping[str, Any],
        eval_runner: Callable[[Callable[[str, Any, Any], Any], str, Any], Any],
        var_solved: AttrDict,
        conffile_values_map: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._local_flags = flags
        self._values_map = values_map
        self._conffile_values_map = conffile_values_map
        self._eval_runner = eval_runner
        self._var_solved = var_solved

    def set_conffile_values_map(
        self, conffile_values_map: Optional[Mapping[str, Any]]
    ) -> None:
        """
        Set or update the configuration file values map.
        Allow to use the same solver with ou without configuration file.
        """
        self._conffile_values_map = conffile_values_map

    @classmethod
    def _find_var_in_dict(
        cls, where: Mapping[Any, Any], var_name: str
    ) -> Any | Undefined:
        """
        Search for var_name in a dictionary.
        var_name contains dict keys separated by a dot (.) ie key1.key2.key3
        The left side key key1 is search in the where directory, if it is found
        and it is a dictionary then key2 is search in it and
        all key are searched in sequence.
        Returns _undef if not found, allowing to distinguish between None (explicit null) and missing.
        """
        cur_dic: Mapping[Any, Any] = where
        for key in var_name.split("."):
            # logger = logging.getLogger(f"{cls.__module__}.{cls.__name__}")
            # logger.debug(f"searching for key: {key} in dict : {cur_val}")
            if key in cur_dic:
                cur_dic = cur_dic[key]
                # logger.debug(f"Found key: {key} = {cur_val}")
            else:
                return _undef

        return cur_dic

    def resolve_confvar(
        self, *, var_to_solve: ConfigVarDef, scopes: Optional[str | Iterable[str]]
    ) -> Any:
        """
        Assign a value to the given ConfigVarDef according to the search order:
        1. values mapping
        2. environment variables
        3. configuration file
        4. default value
        Applies transformations and validations as specified in the ConfigVarDef.
        If its a Path variable, process relative paths, create directories if needed.
        """
        val_found: Path | str | None | list[Any] | Undefined = _undef
        found = False

        cur_flags = self._local_flags.merge(inplace=False, other=var_to_solve.flags)
        assert cur_flags is not None

        # if we are resolving the variables in some specific scopes (ie parameter scope has value)
        # we check if the variable belongs to one of these scopes and if not we skip it, in this
        # case the variable is said to be "out of scope" and has no existence.
        if scopes is None and var_to_solve.scopes is not None:
            return _undef
        # if we are resolving the variable in some specific scopes (ie parameter scope has value) and the variable
        # has also some scopes defined we check if there is at least one scope in common
        if scopes is not None and var_to_solve.scopes is not None:
            test_ctx = []
            # put True in test_ctx for each scope that matches, False otherwise
            if is_sequence(scopes):
                test_ctx = [c in var_to_solve.scopes for c in scopes]
            else:
                test_ctx = [scopes in var_to_solve.scopes]

            # test if there is any True in test_ctx which means that at least one scope matches
            if not any(test_ctx):
                return _undef
        # if the variable has no scope and we are resolving in some specific scopes this means that
        # the variable is common to all scopes so we process them but only once except if the flag
        # allow_override is set to True
        if var_to_solve.scopes is None and scopes is not None:
            if not cur_flags.allow_override and var_to_solve.name in self._var_solved:
                return _undef

        #  Searching variable value in the values mapping
        if (
            self._values_map is not None
            and not cur_flags.no_value_search
            and var_to_solve.value_key is not None
        ):
            ctx = self._var_solved.to_dict()
            # First Render value_key if needed

            def value_checks(k: str) -> Any:
                """check if the key k exists in the values_map and return its value or _undef"""
                if cur_flags.click_key_conversion:
                    k = k.lower().replace("-", "_")
                return _undef if k not in self._values_map else self._values_map[k]

            value_checked = resolve_candidate_list(
                candidates=var_to_solve.value_key,
                context=ctx,
                check_exists=lambda k: value_checks(k),
            )
            # value_checked can be None meaning that the key exists in values_map with a None value which is the value to use
            if value_checked != _undef:
                # We found a key that exists in values_map and the checker has returned its value that can be None.
                val_found = value_checked
                found = True
                self._logger.debug(
                    f"{var_to_solve.name} -> Found in Values = {val_found}"
                )

        # Searching variable value in the environment variables
        if (
            not found
            and not cur_flags.no_env_search
            and var_to_solve.env_name is not None
        ):
            ctx = self._var_solved.to_dict()

            def check_env(k: str) -> Any:
                """check if the key k exists in the environment variables and return its value or _undef"""
                res = os.getenv(k)
                return _undef if res is None else res

            value_checked = resolve_candidate_list(
                candidates=var_to_solve.env_name, context=ctx, check_exists=check_env
            )
            # in env None means not found (there is no _undef in this case and the value can't be None)
            if value_checked != _undef:
                val_found = value_checked
                found = True
                self._logger.debug(f"{var_to_solve.name} -> Found in Env = {val_found}")

        #  Searching variable value in the configuration file
        if (
            not found
            and not cur_flags.no_conffile_search
            and self._conffile_values_map is not None
            and var_to_solve.file_key is not None
        ):
            ctx = self._var_solved.to_dict()

            def check_file(k: str) -> Any:
                """check if the key k exists in configuration file and return its value or _undef"""
                if self._conffile_values_map is None:
                    return False
                return self._find_var_in_dict(self._conffile_values_map, k)

            value_checked = resolve_candidate_list(
                candidates=var_to_solve.file_key, context=ctx, check_exists=check_file
            )
            # None is a valid value from config file, _undef means not found
            if value_checked != _undef:
                val_found = value_checked
                found = True
                self._logger.debug(
                    f"{var_to_solve.name} -> Found in Configuration File = {val_found}"
                )

        #  Setting variable value to the default value if defined.
        if (
            var_to_solve.name not in self._var_solved
            and not found
            and var_to_solve.default is not _undef
        ):
            if var_to_solve.default is not None and callable(var_to_solve.default):
                val_found = self._eval_runner(
                    var_to_solve.default, var_to_solve.name, None
                )
            else:
                val_found = render_template(
                    var_to_solve.default, self._var_solved.to_dict()
                )
            found = True
            self._logger.debug(
                f"{var_to_solve.name} -> Found in Default Value = {val_found}"
            )

        # Raise exception if no value was found and variable is mandatory and if we have not
        # already a value for this variable (in case of override with scopes for example)
        if (
            not found
            and var_to_solve.mandatory
            and var_to_solve.name not in self._var_solved
        ):
            raise AppConfigException(
                f"No value for var {var_to_solve.name} in scope {scopes}"
            )

        if found:
            if isinstance(val_found, Undefined):
                raise AssertionError(
                    "Internal error: val_found is _undef while found=True"
                )
            # spliting lists
            if (
                var_to_solve.split_to_list
                and val_found is not None
                and isinstance(val_found, str)
            ):
                sep: str = (
                    ","
                    if isinstance(var_to_solve.split_to_list, bool)
                    else var_to_solve.split_to_list
                )
                val_found = val_found.split(sep)

            # Transform the variable value if specified.
            if var_to_solve.transform is not None:
                if isinstance(var_to_solve.transform, str):
                    ctx = self._var_solved.to_dict()
                    ctx["value"] = val_found
                    val_transfo = render_template(var_to_solve.transform, ctx)
                else:
                    val_transfo = self._eval_runner(
                        var_to_solve.transform,
                        var_to_solve.name,
                        val_found,
                    )
                self._logger.debug(
                    f"{var_to_solve.name} -> Value Transformed: {val_found} => {val_transfo}"
                )
                val_found = val_transfo

            # Validate and cast the variable value using pydantic TypeAdapter
            if var_to_solve._type_info is not None and val_found is not None:
                try:
                    ta = TypeAdapter(var_to_solve._type_info)
                    val_found = ta.validate_python(val_found)
                except ValidationError as e:
                    raise AppConfigException(
                        f"Validation failed for var {var_to_solve.name}: {e}"
                    )

            # Make special treatment for paths
            if (
                not var_to_solve.no_dir_processing
                and var_to_solve._type_info == Path
                and val_found is not None
            ):
                new_val: list[Path] | Path | None = None
                if is_sequence(val_found):
                    # we need to consider the case where the variable is a list of Path
                    new_val = []
                    for cval in cast(Iterable, val_found):
                        res = self._process_paths(
                            value=cval, var=var_to_solve, var_solved=self._var_solved
                        )
                        new_val.append(res)
                else:
                    res = self._process_paths(
                        value=val_found, var=var_to_solve, var_solved=self._var_solved
                    )
                    new_val = res
                val_found = new_val

        elif var_to_solve.name not in self._var_solved:
            # in case of overiding and when on subsenquent call no value were found we don't want to erase a value
            # found on a previous run. This can happen when some global flags are overriden or for variable without
            # context.
            val_found = None

        return val_found

    def _process_paths(
        self, *, value: Any, var: ConfigVarDef, var_solved: AttrDict
    ) -> Path:
        """
        Run the path processing for a single Path variable.
        """
        var_value: Path
        if isinstance(value, str):
            var_value = Path(value)
        elif isinstance(value, Path):
            var_value = value
        else:
            raise Exception("not a path")

        res: Path = var_value
        # First process the can_be_relative_to case.
        if var.can_be_relative_to is not None:

            if var_value.is_absolute():
                res = var_value
            else:
                # resolving the root directory from which to be relative to.
                can_be_relative = var.can_be_relative_to
                root_dir: Path
                if (
                    isinstance(can_be_relative, str)
                    and can_be_relative in var_solved
                    and var_solved[can_be_relative] is not None
                    and var_solved[can_be_relative] != _undef
                ):
                    root_dir = Path(var_solved[can_be_relative])
                else:
                    root_dir = Path(can_be_relative)
                res = root_dir.joinpath(var_value)

        # Expanding user home and resolving dots in path
        res = res.expanduser().resolve()

        # create directory if make_dirs is not None
        if var.make_dirs:
            if var.make_dirs == PathType.Dir:
                res.mkdir(parents=True, exist_ok=True)
            else:
                res.parent.mkdir(parents=True, exist_ok=True)
        return res
