from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, Optional, Any

from .config_var import configvar
from .utils import PathType


def _get_os_type() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform.startswith("darwin"):
        return "macos"
    return "unknown"


class AutoProlog:
    """
    Automatic configuration for standard paths and environment variables.
    This class defines configuration variables that will be accessible in any
    subclass of AppConfig, providing sensible defaults based directories, Os type
    and execution stage.

    Variables defined:
    - os_type: The operating system type (windows, linux, macos)
    - user_home: The user's home directory, as returned by Path.home()
      Must be used instead of '~' to ensure cross platform compatibility.
    - xdg_data_home: Base directory for user specific data files (XDG standard)
    - xdg_config_home: Base directory for user specific configuration files (XDG standard)
    - xdg_cache_home: Base directory for user specific non-essential data files (XDG standard)
    - xdg_state_home: Base directory for user specific state files (XDG standard)
    - app_data: Application Data directory on Windows
    - app_config: Application Config directory on Windows
    - app_cache: Application Cache directory on Windows
    - data_home: OS independent application data directory
    - config_home: OS independent application configuration directory
    - cache_home: OS independent application cache directory
    - exec_stage: The execution stage, default to the string "dev", no restriction on its value
        to let the user define its own stages.

    Any of this variable can be overridden by a redefinition on a subclasse of AppConfig.
    """

    os_type: Literal["windows", "linux", "macos", "unknown"] = configvar(
        default=lambda _, __, ___: _get_os_type(),
        no_search=True,
        help="The operating system type (windows, linux, macos)",
        auto_prolog=True,
    )

    exec_stage: Any = configvar(
        default=None,
        type_info=str,
        env_name=["EXEC_STAGE", "STAGE", "ENV"],
        value_key=["exec_stage", "stage", "env"],
        help="The execution stage (dev, prod, test)",
        click_key_conversion=True,
        allow_override=True,
        auto_prolog=True,
    )

    user_home: Path = configvar(
        default=lambda _, __, ___: Path.home(),
        no_search=True,
        help="The user's home directory",
        auto_prolog=True,
    )

    # XDG Standards
    xdg_data_home: Optional[Path] = configvar(
        default=lambda _, c, __: (
            c.user_home / ".local" / "share" if c.os_type != "windows" else None
        ),
        env_name="XDG_DATA_HOME",
        help="Base directory for user specific data files",
        no_value_search=True,
        no_conffile_search=True,
        auto_prolog=True,
    )

    xdg_config_home: Optional[Path] = configvar(
        default=lambda _, c, __: (
            c.user_home / ".config" if c.os_type != "windows" else None
        ),
        env_name="XDG_CONFIG_HOME",
        help="Base directory for user specific configuration files",
        no_value_search=True,
        no_conffile_search=True,
        auto_prolog=True,
    )

    xdg_cache_home: Optional[Path] = configvar(
        default=lambda _, c, __: (
            c.user_home / ".cache" if c.os_type != "windows" else None
        ),
        env_name="XDG_CACHE_HOME",
        help="Base directory for user specific non-essential data files",
        no_value_search=True,
        no_conffile_search=True,
        auto_prolog=True,
    )

    xdg_state_home: Optional[Path] = configvar(
        default=lambda _, c, __: (
            c.user_home / ".local" / "state" if c.os_type != "windows" else None
        ),
        env_name="XDG_STATE_HOME",
        help="Base directory for user specific state files",
        no_value_search=True,
        no_conffile_search=True,
        auto_prolog=True,
    )

    # Windows specific variables
    app_data: Optional[Path] = configvar(
        default=lambda _, c, __: (
            c.user_home / "AppData" if c.os_type == "windows" else None
        ),
        env_name="APP_DATA",
        help="Application Data directory on Windows",
        no_value_search=True,
        no_conffile_search=True,
        auto_prolog=True,
    )

    app_config: Optional[Path] = configvar(
        default=lambda _, c, __: c.app_data / "Config" if c.app_data else None,
        env_name="APP_CONFIG",
        help="Application Config directory on Windows",
        no_value_search=True,
        no_conffile_search=True,
        auto_prolog=True,
    )

    app_cache: Optional[Path] = configvar(
        default=lambda _, c, __: c.app_data / "Cache" if c.app_data else None,
        env_name="APP_CACHE",
        help="Application Cache directory on Windows",
        no_value_search=True,
        no_conffile_search=True,
        auto_prolog=True,
    )

    # Unified variables
    data_home: Path = configvar(
        default=lambda _, c, __: (
            c.app_data if c.os_type == "windows" else c.xdg_data_home
        ),
        click_key_conversion=True,
        help="OS independent application data directory",
        auto_prolog=True,
        allow_override=True,
    )

    config_home: Path = configvar(
        default=lambda _, c, __: (
            c.app_config if c.os_type == "windows" else c.xdg_config_home
        ),
        click_key_conversion=True,
        help="OS independent application configuration directory",
        auto_prolog=True,
        allow_override=True,
    )

    cache_home: Path = configvar(
        default=lambda _, c, __: (
            c.app_cache if c.os_type == "windows" else c.xdg_cache_home
        ),
        click_key_conversion=True,
        help="OS independent application cache directory",
        auto_prolog=True,
        allow_override=True,
    )
