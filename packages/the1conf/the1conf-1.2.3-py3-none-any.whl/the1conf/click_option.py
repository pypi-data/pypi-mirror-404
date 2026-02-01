from __future__ import annotations

from typing import Any, Callable

import click

from .app_config import ConfigVarDef
from .utils import Undefined, _undef


class StringOrUndefined(click.ParamType):
    name = "string"

    def convert(self, value: Any, param: Any, ctx: Any) -> Any:
        if value is _undef:
            return value
        return click.STRING.convert(value, param, ctx)


def click_option(config_var: Any, **kwargs: Any) -> Callable[[Any], Any]:
    """Wrapper for click.option with the metadata from ConfigVarDef."""
    if not isinstance(config_var, ConfigVarDef):
        raise TypeError(f"click_option expects a ConfigVarDef, got {type(config_var)}")

    # 1. Flag name (ex: my_var -> --my-var)
    param_decls = []

    keys = []
    if config_var.value_key is None:
        keys = [config_var.name]
    elif isinstance(config_var.value_key, str):
        keys = [config_var.value_key]
    else:
        keys = config_var.value_key

    for key in keys:
        if len(key) == 1:
            param_decls.append(f"-{key}")
        else:
            param_decls.append(f"--{key.replace('_', '-').lower()}")

    # Used as destination in the dict returned by click
    param_name = keys[0]

    # 2. Documentation
    if "help" not in kwargs and config_var.help:
        kwargs["help"] = config_var.help

    # 3. Strict constraint: Always strings
    # We overwrite any passed type to ensure that resolve_vars receives a string.
    # We use a custom type to handle the `_undef` default value without converting it to string.
    kwargs["type"] = StringOrUndefined()

    # We set default to `_undef` to distinguish between "option not provided" (_undef)
    # and "option provided with no value" (which shouldn't happen with string) or None.
    # AppConfig handles `_undef` as "missing value" and will look for other sources (env, file, default).
    kwargs["default"] = _undef

    # 4. Display default without applying it
    if (
        "show_default" not in kwargs
        and config_var.default is not Undefined
        and not callable(config_var.default)
    ):
        # We must convert to string otherwise click interprets bool/int as flags (True/False)
        # which tell it "show the default" (which is None here), so it displays nothing.
        kwargs["show_default"] = str(config_var.default)

    # Note: We do NOT pass 'envvar' nor 'default'

    # We force the destination name to match the key expected by the1conf
    return click.option(*param_decls, param_name, **kwargs)
