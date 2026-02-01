"""Validator for typing.Literal type hints."""
from typing import Any, Literal

from .._check_result import CheckResult
from .._constants import IS_IMMUTABLE, IS_VALID, NOT_VALID
from .._error_tags import TypeHintsErrorTag
from .._exceptions import TypeCheckError
from .._immutable import is_immutable

__all__ = (
    "_check_typing_literal",
)


def _check_typing_literal(
        obj: Any,
        type_hint: Any,
        origin: Any,
        args: tuple,
        raise_on_error: bool = False) -> CheckResult:
    """Handle Literal types.

    :param Any obj: The object to check.
    :param Any type_hint: The type hint to check against.
    :param Any origin: The origin type of the type hint.
    :param tuple args: The type arguments of the Literal type hint.
    :param bool raise_on_error: Whether to raise an exception on validation failure.
    :return CheckResult: Tuple indicating (is_valid, is_immutable).
    :raises TypeCheckError: If raise_on_error is True and validation fails.
    """
    if origin is not Literal:  # Sanity check for bad calls
        raise TypeCheckError(
            f"Type hint '{type_hint}' is not a Literal type.",
            tag=TypeHintsErrorTag.INVALID_TYPE_HINT)

    if obj in args:
        return CheckResult(IS_VALID, IS_IMMUTABLE)

    if raise_on_error:
        raise TypeCheckError(
            f"Object of type '{type(obj)}' does not match type hint '{type_hint}'.",
            tag=TypeHintsErrorTag.VALIDATION_FAILED)
    return CheckResult(NOT_VALID, is_immutable(obj))
