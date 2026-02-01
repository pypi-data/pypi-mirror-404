from __future__ import annotations

import jinja2
from typing import Any, Callable, Mapping, Optional, Sequence, Union, cast
from .utils import is_sequence, _undef

RenderContext = Mapping[str, Any]


def render_template(value: Union[str, Any], context: RenderContext) -> Any:
    """
    Render a string as a jinja2 template using the provided context.
    If value is not a string, return it as is.
    """
    if isinstance(value, str):
        return jinja2.Template(value).render(context)
    return value


def resolve_candidate_list(
    *,
    candidates: Optional[Union[str, Sequence[str]]],
    context: RenderContext,
    check_exists: Optional[Callable[[str], Any]] = None,
) -> Optional[Any]:
    """
    Resolve a list of candidate strings (which can be Jinja2 templates) to find the first valid one.

    Args:
        candidates: A single string or a list of strings (potentially templates).
        context: The context used for rendering templates.
        check_exists: An optional predicate to validate the rendered string.
                      returns _undef if not valid, or the value to return if valid.
    Returns:
        The first successfully resolved and validated candidate string or the first not None value return by check_exists, or None if no match is found.
    """
    if candidates is None:
        return None

    candidates_list: list[str] = []
    if isinstance(candidates, str):
        candidates_list = [candidates]
    elif is_sequence(candidates):
        candidates_list = cast(list[str], candidates)

    for raw_candidate in candidates_list:
        rendered = render_template(raw_candidate, context)
        if rendered is None:
            continue

        if isinstance(rendered, str):
            if check_exists is not None:
                res = check_exists(rendered)
                if res != _undef:
                    return res
            else:
                return rendered

    return _undef
