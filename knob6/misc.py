"""
KNOB - miscellaneous definitions
"""

from typing import Union
import inspect


def print_stack_indented(*args, **kwargs):
    """Indent a print output proportionally to stack depth"""
    indent = '    ' * (len(inspect.stack()) - 1)
    print(indent[:-1], *args, **kwargs)


# Accepted attribute value types
AttrTypes = Union[str, int, bool]


def attrs_repr(attrs: dict[str, AttrTypes]):
    """Format a (preferably compact) representation of attributes"""
    if any(not k.isidentifier() for k in attrs):
        return "{" + ", ".join(
            f"{k!r}: {v!r}" for k, v in attrs.items()
        ) + "}"
    if attrs:
        return "(" + ", ".join(
            f"{k}={v!r}" for k, v in attrs.items()
        ) + ")"
    return ""
