from __future__ import annotations

from typing import Optional


class Flags:
    """
    Flags that control how to search for variable values in AppConfig.
    These flags can be set globally in the AppConfig object or locally when calling resolve_vars() or
    per config variables.

    Not None flag values override other values with the following precedence:
        ConfigVariableDef > resolve_vars() parameters > AppConfig global flags.
    Which means that a not None value in a ConfVarDef directive will overrride a global flag value defined in AppConfig. And also that a None value in a ConfVarDef directive
    will not override the value set in resolve_vars() parameters or an AppConfig global flags.

    Attributes:
        no_env_search (bool|None): don't search values in the environment.
        no_value_search (bool|None): don't search values in the values dict.
        no_conffile_search (bool|None): don't search values in the configuration file.
        no_search (bool|None): don't search values in any location.
        click_key_conversion (bool|None): use the variable name converted to lower case and with dashes converted to underscores as
            the key to search in values.
        allow_override (bool|None): allow overriding variable in the configuration when calling resolve_vars.
        mandatory (bool|None): raise exception when no value is found for a variable. Default is True.
    """

    _no_env_search: bool | None
    _no_value_search: bool | None
    _no_conffile_search: bool | None
    _no_search: bool | None
    _click_key_conversion: bool | None
    _allow_override: bool | None

    def __init__(
        self,
        *,
        no_env_search: Optional[bool] = None,
        no_value_search: Optional[bool] = None,
        no_conffile_search: Optional[bool] = None,
        no_search: Optional[bool] = None,
        click_key_conversion: Optional[bool] = None,
        allow_override: Optional[bool] = None,
    ) -> None:
        self._no_env_search = no_env_search
        self._no_value_search = no_value_search
        self._no_conffile_search = no_conffile_search
        self._no_search = no_search
        if self._no_search:
            self._no_env_search = True
            self._no_value_search = True
            self._no_conffile_search = True
        self._click_key_conversion = click_key_conversion
        self._allow_override = allow_override

    def merge(self, *, inplace: bool = False, other: Flags) -> Flags | None:
        """
        Merge the current flags with the given flags.
        If inplace is True then modify the current object, otherwise return a new Flags object.

        Flags given as parameters have precedence over the current object values if they are not None.
        """
        cur_no_search: Optional[bool]
        cur_no_env_search: Optional[bool]
        cur_no_value_search: Optional[bool]
        cur_no_conffile_search: Optional[bool]
        cur_click_key_conversion: Optional[bool]
        cur_allow_override: Optional[bool]

        cur_no_search = (
            other._no_search if other._no_search is not None else self._no_search
        )
        if cur_no_search:
            cur_no_env_search = True
            cur_no_value_search = True
            cur_no_conffile_search = True
        else:
            cur_no_env_search = (
                other._no_env_search
                if other._no_env_search is not None
                else self._no_env_search
            )
            cur_no_value_search = (
                other._no_value_search
                if other._no_value_search is not None
                else self._no_value_search
            )
            cur_no_conffile_search = (
                other._no_conffile_search
                if other._no_conffile_search is not None
                else self._no_conffile_search
            )
        cur_click_key_conversion = (
            other._click_key_conversion
            if other._click_key_conversion is not None
            else self._click_key_conversion
        )
        cur_allow_override = (
            other._allow_override
            if other._allow_override is not None
            else self._allow_override
        )
        if not inplace:
            return Flags(
                no_env_search=cur_no_env_search,
                no_value_search=cur_no_value_search,
                no_conffile_search=cur_no_conffile_search,
                no_search=cur_no_search,
                click_key_conversion=cur_click_key_conversion,
                allow_override=cur_allow_override,
            )
        else:
            self._no_env_search = cur_no_env_search
            self._no_value_search = cur_no_value_search
            self._no_conffile_search = cur_no_conffile_search
            self._no_search = cur_no_search
            self._click_key_conversion = cur_click_key_conversion
            self._allow_override = cur_allow_override
            return None

    @property
    def no_env_search(self) -> bool:
        return False if self._no_env_search is None else self._no_env_search

    @property
    def no_value_search(self) -> bool:
        return False if self._no_value_search is None else self._no_value_search

    @property
    def no_conffile_search(self) -> bool:
        return False if self._no_conffile_search is None else self._no_conffile_search

    @property
    def no_search(self) -> bool:
        return False if self._no_search is None else self._no_search

    @property
    def click_key_conversion(self) -> bool:
        return False if self._click_key_conversion is None else self._click_key_conversion

    @property
    def allow_override(self) -> bool:
        return False if self._allow_override is None else self._allow_override
