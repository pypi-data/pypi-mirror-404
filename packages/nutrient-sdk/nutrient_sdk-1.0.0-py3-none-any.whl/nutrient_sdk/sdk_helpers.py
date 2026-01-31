"""
SDK Helper utilities for method overload resolution and type checking.

This module provides common utilities used by generated Python wrapper classes
for the Nutrient Native SDK.
"""

from typing import Any, Optional, Type, get_type_hints
from enum import Enum


def is_sdk_class(obj: Any, expected_class_name: Optional[str] = None) -> bool:
    """
    Check if an object is an SDK class instance.

    Args:
        obj: The object to check
        expected_class_name: Optional specific class name to check for

    Returns:
        True if obj is an SDK class instance (optionally of the specified class)
    """
    if obj is None:
        return False

    if not hasattr(obj, '_handle'):
        return False

    if expected_class_name:
        return obj.__class__.__name__ == expected_class_name

    return True


def get_python_type_name(obj: Any) -> str:
    """
    Get a normalized type name for overload resolution.

    Args:
        obj: The object to get the type name for

    Returns:
        A string representing the type (e.g., 'str', 'int', 'DocumentSettings')
    """
    if obj is None:
        return 'NoneType'

    if isinstance(obj, str):
        return 'str'
    elif isinstance(obj, int):
        return 'int'
    elif isinstance(obj, float):
        return 'float'
    elif isinstance(obj, bool):
        return 'bool'
    elif isinstance(obj, bytes):
        return 'bytes'
    elif isinstance(obj, Enum):
        return obj.__class__.__name__
    elif hasattr(obj, '_handle'):
        return obj.__class__.__name__
    else:
        return type(obj).__name__


IMPLICIT_COERCIONS = {
    'float': {'int', 'bool'},
    'double': {'int', 'float', 'bool'},
    'int': {'bool'},
    'long': {'int', 'bool'},
    'str': {'Path'},
}


def match_overload_signature(args: tuple, signature: tuple) -> bool:
    """
    Check if provided arguments match a specific overload signature.

    Args:
        args: Tuple of actual argument values (None values filtered out)
        signature: Tuple of expected type names (e.g., ('str', 'DocumentSettings'))

    Returns:
        True if the arguments match the signature

    Note:
        Supports implicit type coercion based on IMPLICIT_COERCIONS map,
        following Python and C# numeric promotion conventions.
        For example, add_page(500, 800, 5) will match signature (float, float, int)
        because int can implicitly coerce to float.
    """
    actual_args = tuple(arg for arg in args if arg is not None)

    if len(actual_args) != len(signature):
        return False

    for arg, expected_type in zip(actual_args, signature):
        actual_type = get_python_type_name(arg)

        if actual_type == expected_type:
            continue

        if expected_type in IMPLICIT_COERCIONS and actual_type in IMPLICIT_COERCIONS[expected_type]:
            continue

        return False

    return True


def resolve_overload(overload_map: dict, *args) -> Optional[str]:
    """
    Resolve which overload to call based on provided arguments.

    Args:
        overload_map: Dictionary mapping signature tuples to bridge function names
                      e.g., {('str',): 'BridgeDocumentOpenString',
                             ('str', 'DocumentSettings'): 'BridgeDocumentOpenStringDocumentSettings'}
        *args: The actual arguments provided by the caller

    Returns:
        The bridge function name to call, or None if no match found
    """
    for signature, bridge_function in overload_map.items():
        if match_overload_signature(args, signature):
            return bridge_function

    return None


def format_overload_error(method_name: str, overload_map: dict, *args) -> str:
    """
    Format a helpful error message when overload resolution fails.

    Args:
        method_name: The name of the method being called
        overload_map: Dictionary of available overload signatures
        *args: The actual arguments that were provided

    Returns:
        A formatted error message
    """
    actual_types = tuple(get_python_type_name(arg) for arg in args)

    available = []
    for signature in overload_map.keys():
        available.append(f"  - {method_name}({', '.join(signature)})")

    return (
        f"No matching overload found for {method_name}({', '.join(actual_types)})\n"
        f"Available overloads:\n" + "\n".join(available)
    )


__all__ = [
    'is_sdk_class',
    'get_python_type_name',
    'match_overload_signature',
    'resolve_overload',
    'format_overload_error',
]
