from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast,
    dataclass_transform,
    get_args,
    get_origin,
    get_type_hints,
)
import inspect
from .utils import Undefined, _undef, PathType, is_sequence
from .flags import Flags

if TYPE_CHECKING:
    from .app_config import AppConfig

_T = TypeVar("_T")


@dataclass_transform()
class ConfigVarDef(Generic[_T]):
    """
    Definition of an application configuration variable.

    Attribute of this class are called configuration directives that are used to specify the configuration of the application with the AppConfig class.

    Configuration are used indirectly by defining attributes of an AppConfig subclass with the configvar() function that creates ConfigVarDef objects:
        class MyAppConfig(AppConfig):
            my_var: int = configvar(default=1)

    The method resolve_vars() of the AppConfig class uses these configuration variable definitions to look for the values of the variables as explained in its documentation.
    Each configuration variable definition contains several directives to define how to look for the values of the variables in a dictionnarary that can be the CLI parameters,
    or a configuration file, or an environment variables or a computation defined by a python Callable.

    Two directive are not specified in the constructor of ConfigVarDef because they are inferred from the attribute name and type hint:
        - name : the name of the variable, inferred from the attribute name.
        - type_info : the type to which to cast the variable value, inferred from the attribute type hint. Must be a python builtin type or a class or a list of
            builtin types.
            Here how to get the list of python builtin types:
                print([t.__name__ for t in __builtins__.__dict__.values() if isinstance(t, type)])
            Lists are handle with a specific processing detail below in the paragraph 'Lists'.
            Complex casting can be handle with a transfom Eval Form or with a class that implements the complex type.
            Optional value are supported like Optional[int] or Union[str, None] to indicate that the variable can be None.
            When the type hint is missing the variable is considered to be of type str.

    The directives that can be specified in configvar() are:

    - help [optional]: a help string that describes the variable.
    - default [optional]: the default value, can be a value or an Eval Form (see below explanation on Eval forms) whose
        returned value will be the value of the variable if no other value has been found.
        See paragraph about None below for more information.
    - env_name [optional ]: the name of the environment variable that can contain the value. By default search for name
    - file_key [optional ]: the key to look for in the configuration file, key can be in the form a1.a2.a3 (attributes separated by dots) to indicate
        nested namespaces (see AppConfig documentation). By default search for name.
    - value_key [optional ]: the key to look for in the "Values" dict. by default search for name. None value are ignored.
        If the constructor parameter click_key_conversion flag (see below for flags) is true then the default value is the name in lowercase and with '-' replaced by '_'
    - transform : an Eval Form (see below explanation on Eval forms) that transform the value found for the variable and produce another value that will be the value
        of the variable before possible casting (like explain in type_info).
    - scopes [optional]: a list of names indicating in which scope the variable is valid. If one of the scope names passed at variable resolution to
        AppConfig.resolve_vars() matches one of the scope names of the variable or if the variable has no scope directive then the variable is
        considered for resolution.
    - split_to_list [optional ]: Indicates that the value found must be split in order to produce a list of string. The value

        of the directive is the list separator or True if the separator is a comma. Value in the string list will be casted to the type specified in type_info.
        See the paragraph below about Lists that explain how list handled.
    - can_be_relative_to [optional]: a directory path or the name of another key that resolves in a directory path.
        If type_info is a Path and the retrieved value is not an empty string nor None nor an absolute path then
        transform the value to an absolute path with the given directory as parent directory.
        See details below on how Path are processed.
    - make_dirs [optional ]: a PathType that indicates the type of Path for which directories are to be created if they do not exist yet.
            if PathType is:
                - Dir : create the hierarchy of directory necessary to contains this directory as well as the directory itself
                - File: create the parent hierarchy of directory necessary to contains this file
        See details below on how Path are processed.
    - auto_prolog [optional]: mark the variable for automatic prolog processing - which means that the variable will be resolved at an early stage, before the configuration file
        is resolved and before all other variables. If it has also the allow_override flag True then it can be processed again with all other variables in the regular resolution.


    - Flag directives:
        These directives can also be defined globally in the AppConfig object or when calling resolve_vars().Flags defined in a ConfigVarDef override
        the other values if they are defined.
        - no_dir_processing [optional ]: don't run specific Path processing for this variable.
        - no_env_search [optional ]: boolean, False by default. If true the value of the variable is not searched in the Environment.
        - no_value_search[optional ]: boolean, False by default. If true the value of the variable is not searched in the values dict.
        - no_conffile_search [optional ]: boolean, False by default. If true the value of the variable is not searched in the configuration file.
        - click_key_conversion [optional ]: boolean, False by default. If true the value of the variable is converted using Click key conversion.
        - allow_override [optional ]: boolean, False by default. If true the variable value can be overridden by another context.
        - mandatory [optional ]: boolean, True by default. If true an exception is thrown if the variable value is not found. Otherwise the variable is not set which means that accessing it
          would raise an Exception.
        - no_search [optional] : boolean, False by default. It true the value of the variable is not searched in the Environment, the values or the configuration
            file. It's equivaleut to set the directives no_env_search, no_value_search, no_conffile_search to True. In this case the value of the variable should be defined by
            the default directive.

    For backward compatibilty the special value __NO_SEARCH__ for env_name, config_key, file_key and value_key are still supported but it's recommended to use
    the no_env_search, no_value_search, no_conffile_search or no_search directives instead.

    By default throw an exception if no value are found except if mandatory is False

    Eval Forms:
    -----------

        an eval form is a callable that is evaluated to compute a value for a variable. Eval forms can be used in the default directive or the
        transform directive.

        The callable receives three parameters: the variable name, this configuration object and the current value found for the variable if one has been found
        in the case of a transform directive.

        The expression can use value already defined in this application configuration object by using the first parameter of the callable which is the AppConfig object itself,
        knowing that variables are evaluated in the order they are defined.

        In the case of a default directive the third parameter of the callable will be None.
        In the case of a transform directive the third parameter of the callable may be None if no value have been found and
        the 'mandatory' global flag is set to False, otherwise it will be the value found for the variable before transformation.

        The returned value from the evaluation of the callable will be used to set the variable value before casting to type_info.
        Note that the eventual type casting will be done after the Eval call.
        It's up to the caller to deal with the returned value.

        Note that the libraries used in Eval Forms must be imported in the module that defines the form.

        !!Warning!!: default and transform directives should be set or return a value that must be 'castable' to the type defined by type_info.
        For example if a variable is declared as a class that accept a string in its constructor then the default directive should be a string or an Eval
        Form that returns a string not the class instance.

    Path and Path list type_info variables:
    --------------------------------------

        If a variable has a type_info that is a Path or a list of Path there a dedicated processing that applies on the
        value found for them.
        This processing takes place at the end of the processing of normal variable and occurs when:
            - the type_info is a Path or a list of Path
            - a value for the variable was found
            - the directive no_dir_processing is False

        The specific processing is the following on the Path or on each of the Path in the list of Path:
            - can_be_relative_to: if this directive has a value that can be a path-like directory or the name of another key already defined
            that resolves in a path-like directory and the value found is not an absolute Path:
                - then make a Path with the can_be_relative_to directory as parent and the value found as its child.
            - make_dirs: if this directive is True , then create the necessary directories of the path if they don't exist yet.
            - Call the 'expanduser()' and 'resolve()' method on the resulting Path.

    List:
    -----

        All values found are strings that should be casted to the type specified in type_info inferred from the type hint of the variable.
        Only list of single type are supported like list[int], list[str], list[MyClass], etc.
        The value is considered as a list when split_to_list is not False and a value was found for the variable.
        In this case the temporaray string value found for the variable is split with the string 'split()' method to generate
        a list of string.
        Then all items of the list of strings are casted to the specified type_info.

    scopes:
    --------
        Every configuration variable can specify a list of scope(s) in which it is valid.
        When resolving variables it is also possible to specify for which scope(s) the resolution must be done.

        When one or several scopes are specify for the resolution then only the variable valid for these scopes will be considered for resolution
        as well as the VarDef without Scope directive. Variable defined without Scope directive are common to all scope, the one with a Scope directive
        are specific to their scopes.

        This allows to define variables that are specific to some scope and to resolve only these variables when needed.
        When the flage allow_override is False and several resolutions are done, then variables are evaluated only once even if they are valid in several
        of the requested scope(s), only the first valid scope is used.

    None value:
    ----------
        All the VarDef valid for the involved scopes will be resolved and the one for which no value have been found will be set to None if the
        flag 'mandatory' is False.

        If the flag 'mandatory' is true and one varDef for the scope has no value then an exception is raised.

        Whatever is the value of the flag 'mandatory' it is possible to set a value to None either with the 'default' directive or with
        an Eval Form or a None value in one of the search location.

    AutoProlog variables:
    --------------------
        Variables defined with the auto_prolog directive set to True are considered as AutoProlog variables. These variables are resolved at an early stage
        before all other variables and before the configuration file is processed.
        This allows to define variables that are necessary to locate the configuration file when its path depends on other variables. In this case these variables
        must be defined as AutoProlog variables.
        The default variables defined in the AutoProlog class are all AutoProlog variables and therefore are made available to be used in variable substitution for all other
        variables and for locating the configuration file.

    Note on implementation:
    -----------------------
        ConfigVarDef is a descriptor class that defines the __get__ and __set__ methods.
        This allows to define configuration variables as class attributes on AppConfig subclasses.
        The __set_name__ method is used to set the name and type_info directives based on the attribute name and type hint.
    """

    _auto_prolog: Optional[bool] = None
    _can_be_relative_to: Optional[Path | str] = None
    _scopes: Optional[Sequence[str]] = None
    _default: Any | Callable[[str, Any, Any], Any] | Undefined = _undef
    _env_name: Optional[Sequence[str]] = None
    _file_key: Optional[Sequence[str]] = None
    _help: str = ""
    _make_dirs: Optional[PathType] = None
    _mandatory: Optional[bool] = True
    _no_dir_processing: Optional[bool] = None
    _name: Optional[str] = None
    _split_to_list: Optional[bool | str] = None
    _transform: Optional[Union[Callable[[str, Any, Any], Any], str]] = None
    _type_info: Any = None
    _value_key: Optional[Sequence[str]] = None

    def __init__(
        self,
        *,
        allow_override: Optional[bool] = None,
        auto_prolog: Optional[bool] = None,
        can_be_relative_to: Optional[Path | str] = None,
        click_key_conversion: Optional[bool] = None,
        scopes: Optional[Sequence[str]] = None,
        default: Any | Callable[[str, Any, Any], Any] | Undefined = _undef,
        env_name: Optional[str | Sequence[str]] = None,
        file_key: Optional[str | Sequence[str]] = None,
        help: str = "",
        make_dirs: Optional[PathType] = None,
        mandatory: Optional[bool] = None,
        no_conffile_search: Optional[bool] = None,
        no_dir_processing: Optional[bool] = None,
        no_env_search: Optional[bool] = None,
        no_search: Optional[bool] = None,
        no_value_search: Optional[bool] = None,
        split_to_list: Optional[bool | str] = None,
        transform: Optional[Union[Callable[[str, Any, Any], Any], str]] = None,
        type_info: Any = None,
        value_key: Optional[str | Sequence[str]] = None,
    ) -> None:
        """Initialize the configuration variable definition.
        Should not be used directly but be used through the function configvar() to define a configuration variable as a class attribute
        on an AppConfig subclass like this:
            class MyCfg(AppConfig):
                my_var: int = configvar(default=1)

        """
        self.__doc__ = help
        self._auto_prolog = auto_prolog
        self._can_be_relative_to = can_be_relative_to
        self._scopes = scopes
        self._default = default
        self._env_name = (
            None
            if env_name is None
            else (
                env_name
                if is_sequence(env_name)
                else [env_name] if isinstance(env_name, str) else None
            )
        )
        self._file_key = (
            None
            if file_key is None
            else (
                file_key
                if is_sequence(file_key)
                else [file_key] if isinstance(file_key, str) else None
            )
        )
        self._help = help
        self._make_dirs = make_dirs
        self._mandatory = mandatory
        self._no_dir_processing = no_dir_processing
        self._no_search = no_search
        self._split_to_list = split_to_list
        self._transform = transform
        self._type_info = type_info
        self._value_key = (
            None
            if value_key is None
            else (
                value_key
                if is_sequence(value_key)
                else [value_key] if isinstance(value_key, str) else None
            )
        )
        self.flags = Flags(
            no_env_search=no_env_search,
            no_value_search=no_value_search,
            no_conffile_search=no_conffile_search,
            click_key_conversion=click_key_conversion,
            allow_override=allow_override,
        )

    def __set_name__(self, owner: type, name: str) -> None:
        """This method is a special python method called when a descriptor is assigned to a class attribute.
        ConfigVarDef is a descriptor class because it defines the __get__ and __set__ methods.

        The goal of this method is to:
            - set the name directive of this ConfigVarDef based on the attribute name.
            - infer the type of the attribute and set the type_info directive with it.

        Args:
            owner (type): the owning class of the attribute that is being assigned the descriptor
            name (str): the attribute name
        """

        # set name directive
        self._name = name

        # try to find a type:
        #     if we have a type hints and a type_info directive we take the type_info.
        #     This allow to define a type for the type checker that allow override with another type if the user wants to.
        #     (it is usefull for exec_stage)
        #     but still have a correct run time type , this is correct as long as the user use duck typing types
        #     that are compatible.
        try:
            hints = get_type_hints(owner, include_extras=True)
        except Exception:
            hints = getattr(owner, "__annotations__", {})

        # test if there is a type hint for this attribute
        annotated_type: dict[str, Any] | Any | dict[Any, Any] = None
        if name in hints:
            annotated_type = hints[name]
            if isinstance(annotated_type, str):
                # Why can it be a string? In Python, type hints are strings if:
                #   from __future__ import annotations is used (postponed evaluation of annotations).
                #   The user explicitly used quotes for a forward reference (e.g., var: "MyClass" where MyClass is defined later).
                for frame_info in inspect.stack():
                    # try to resolve the type with an eval to which we provide the globals and locals for its resolution.
                    # But it can happen that the type is defined in a local scope, so we need to go through all frames
                    # using the stack.
                    try:
                        resolved_type = eval(
                            annotated_type,
                            frame_info.frame.f_globals,
                            frame_info.frame.f_locals,
                        )
                        if resolved_type is not None:
                            annotated_type = resolved_type
                            break
                    except Exception:
                        continue
                else:
                    raise TypeError(
                        f"Could not resolve type hint '{annotated_type}' for configuration variable '{name}'. "
                        "Please check that the type is imported and available."
                    )

        type_info_directive: type | None = None
        if self._type_info is not None:
            type_info_directive = self._type_info

        if annotated_type is not None and type_info_directive is not None:
            # both type hint and type_info directive are defined, use type_info directive
            self._type_info = type_info_directive
        elif annotated_type is not None:
            # only type hint is defined, use it
            self._type_info = annotated_type
        elif type_info_directive is not None:
            # only type_info directive is defined, use it
            self._type_info = type_info_directive
        else:
            # no type hint nor type_info directive, default to str
            self._type_info = str

        # We still need to handle split_to_list if not set and the type selected is a list
        if self._split_to_list is None:
            try:
                origin = get_origin(self._type_info)
                args = get_args(self._type_info)

                # Check for basic list
                if origin is list or self._type_info is list:
                    self._split_to_list = True
                # Check for Optional[list] / Union[list, ...]
                elif origin is Union:
                    for arg in args:
                        arg_origin = get_origin(arg)
                        if arg_origin is list or arg is list:
                            self._split_to_list = True
                            break
            except Exception:
                pass

    def __get__(
        self, instance: Optional[AppConfig], owner: Optional[type] = None
    ) -> ConfigVarDef[_T] | _T | None:
        """
        Descriptor method that gets the value of the configuration variable from the AppConfig instance.

        The value is retrieved from the instance's __dict__ using the variable's name because we want to
        handle the case where we have dotted names for nested attributes.
        """
        if instance is None:
            return self
        name = self.name
        if name in instance.__dict__:
            return instance[name]
        return None

    def __set__(self, instance: AppConfig, value: Any) -> None:
        """
        Descriptor method that gets the value of the configuration variable from the AppConfig instance.
        The value is set in the instance's __dict__ using the variable's name because we want to
        handle the case where we have dotted names for nested attributes.
        """
        instance._set_value(self.name, value)

    @property
    def auto_prolog(self) -> Optional[bool]:
        return self._auto_prolog

    @property
    def can_be_relative_to(self) -> Optional[Path | str]:
        return self._can_be_relative_to

    @property
    def scopes(self) -> Sequence[str] | None:
        return self._scopes

    @property
    def default(self) -> Any | Callable[[str, Any, Any], Any] | Undefined:
        return self._default

    @property
    def env_name(self) -> Optional[Sequence[str]]:
        if self.flags.no_search or self.flags.no_env_search:
            return None
        else:
            return self._env_name or self.name

    @property
    def file_key(self) -> Optional[str | Sequence[str]]:
        if self.flags.no_search or self.flags.no_conffile_search:
            return None
        else:
            return self._file_key or self.name

    @property
    def help(self) -> str:
        return self._help

    @property
    def make_dirs(self) -> Optional[PathType]:
        return self._make_dirs

    @property
    def mandatory(self) -> bool:
        return True if self._mandatory is None else self._mandatory

    @property
    def no_dir_processing(self) -> bool:
        return False if self._no_dir_processing is None else self._no_dir_processing

    @property
    def name(self) -> str:
        if self._name is None:
            raise RuntimeError(
                "ConfigVarDef has no name. Declare it on an AppConfig subclass "
            )
        return self._name

    @property
    def split_to_list(self) -> bool | str:
        return False if self._split_to_list is None else self._split_to_list

    @property
    def transform(self) -> Optional[Union[Callable[[str, Any, Any], Any], str]]:
        return self._transform

    @property
    def value_key(self) -> Optional[str | Sequence[str]]:
        """Note: we can't compute the final value here because it depends on the click_key_conversion
        flag that can be set globally or in resolve_vars."""
        if self.flags.no_search or self.flags.no_value_search:
            return None
        else:
            return self._value_key or self.name


def configvar(
    *,
    allow_override: Optional[bool] = None,
    auto_prolog: Optional[bool] = None,
    can_be_relative_to: Optional[Path | str] = None,
    click_key_conversion: Optional[bool] = None,
    scopes: Optional[Sequence[str]] = None,
    default: Any | Callable[[str, Any, Any], Any] | Undefined = _undef,
    env_name: Optional[str | Sequence[str]] = None,
    file_key: Optional[str | Sequence[str]] = None,
    help: str = "",
    make_dirs: Optional[PathType] = None,
    mandatory: Optional[bool] = None,
    no_conffile_search: Optional[bool] = None,
    no_dir_processing: Optional[bool] = None,
    no_env_search: Optional[bool] = None,
    no_search: Optional[bool] = None,
    no_value_search: Optional[bool] = None,
    split_to_list: Optional[bool | str] = None,
    transform: Optional[Union[Callable[[str, Any, Any], Any], str]] = None,
    type_info: Any = None,
    value_key: Optional[str | Sequence[str]] = None,
) -> Any:
    """Create a declarative configuration variable definition.

    Use it as a class attribute on an AppConfig subclass:

        class MyCfg(AppConfig):
            my_var: int = configvar(default=1)

    The variable name defaults to the attribute name and its type is inferred from the type hint of the attribute declaration.

    This function allows to assign a ConfigVarDef objects to an attribute definitions of any type by telling the type checkers
    that the type of the assignation is Any instead of ConfigVarDef.
    Indeed ConfigVarDef is a generic class and my_var: int = ConfigVarDef(...) or my_var: ConfigVarDef[int] = ConfigVarDef(...)
    would not be accepted by type checkers. configvar() declares returning Any which deactivates type checking.

    """

    return ConfigVarDef(
        allow_override=allow_override,
        auto_prolog=auto_prolog,
        can_be_relative_to=can_be_relative_to,
        click_key_conversion=click_key_conversion,
        scopes=scopes,
        default=default,
        env_name=env_name,
        file_key=file_key,
        help=help,
        make_dirs=make_dirs,
        mandatory=mandatory,
        no_conffile_search=no_conffile_search,
        no_dir_processing=no_dir_processing,
        no_env_search=no_env_search,
        no_search=no_search,
        no_value_search=no_value_search,
        split_to_list=split_to_list,
        transform=transform,
        type_info=type_info,
        value_key=value_key,
    )
