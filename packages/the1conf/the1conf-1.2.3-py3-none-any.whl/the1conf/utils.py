from __future__ import annotations

try:
    import pytest
except ImportError:
    pytest = None

import ast
import inspect
import textwrap
from typing import TypeAlias, Any
from enum import Enum, IntFlag, auto


class AppConfigException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NameSpace:
    """Marker class for configuration namespaces.
    Used to group configuration variables into nested namespaces within an AppConfig subclass.
    See AppConfig documentation for more information.
    """

    pass


class PathType(Enum):
    Dir = auto()
    File = auto()


def get_attribute_docstrings(cls: type) -> dict[str, str]:
    """
    Extracts docstrings for class attributes by parsing the source code.
    This allows using docstrings to populate ConfigVarDef.help.

    currently PEP257 is not yet implemented in python standard library so we need to parse the source code ourselves.
    This can slow down the class creation but this is done at class creation time only.
    """
    docstrings = {}
    try:
        source = inspect.getsource(cls)
        # Deduct to handle nested classes indentation
        source = textwrap.dedent(source)
    except (OSError, TypeError):
        # Source code not available (e.g. dynamic class, REPL, compiled files)
        return {}

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    # We look for the ClassDef in the parsed source.
    # Since inspect.getsource(cls) returns the class definition itself,
    # the first node in body should be the ClassDef.
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for i, item in enumerate(node.body):
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    # Check if the next node is an expression containing a string (docstring)
                    if i + 1 < len(node.body):
                        next_node = node.body[i + 1]
                        if (
                            isinstance(next_node, ast.Expr)
                            and isinstance(next_node.value, ast.Constant)
                            and isinstance(next_node.value.value, str)
                        ):
                            docstring = next_node.value.value.strip()

                            targets = []
                            if isinstance(item, ast.Assign):
                                targets = item.targets
                            elif isinstance(item, ast.AnnAssign):
                                targets = [item.target]

                            for target in targets:
                                if isinstance(target, ast.Name):
                                    docstrings[target.id] = docstring
            # We found the class def, no need to continue in top level
            break

    return docstrings


def is_sequence(obj: Any) -> bool:
    """test if obj is a sequence (list, tuple, etc...) but not a string"""
    try:
        len(obj)
        obj[0:0]
        return not isinstance(obj, str)
    except KeyError:
        return False
    except TypeError:
        return False  # TypeError: object is not iterable


class _UndefinedSentinel:
    pass


Undefined: TypeAlias = _UndefinedSentinel
_undef: Undefined = _UndefinedSentinel()


if pytest:
    pass
