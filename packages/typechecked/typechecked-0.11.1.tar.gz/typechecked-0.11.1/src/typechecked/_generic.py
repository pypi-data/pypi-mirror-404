"""Helper functions to validate user-defined generic types against type hints."""
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence, Set
from typing import Any, Protocol

from ._cache import _CACHE
from ._check_result import CheckResult
from ._constants import IS_IMMUTABLE, IS_VALID, NOT_VALID
from ._error_tags import TypeHintsErrorTag
from ._exceptions import TypeCheckError
from ._immutable import is_immutable
from ._log import log
from ._options import Options
from ._types import Never, NotRequired, ReadOnly, Required
from ._validation_state import ValidationState

__all__ = (
    "_check_generic",
)


def _check_generic(  # pylint: disable=too-many-locals,too-many-return-statements  # noqa: C901
        obj: Any,
        type_hint: Any,
        origin: Any,
        args: tuple,
        options: Options,
        parents: set[ValidationState],
        raise_on_error: bool = False,
        context: str = "") -> CheckResult:
    """
    Check user-defined generic types.

    :param Any obj: The object to check.
    :param Any type_hint: The user-defined generic type hint.
    :param Any origin: The origin of the generic type.
    :param tuple args: The type arguments for the generic.
    :param options: Validation options.
    :param set parents: Parent validation states for cycle detection.
    :param bool raise_on_error: Whether to raise on validation failure.
    :param str context: Context of the validation for error reporting.
    :return: CheckResult indicating (is_valid, is_immutable).
    """
    from ._collections_abc import (  # pylint: disable=import-outside-toplevel
        _check_collections_abc_callable,
        _check_collections_abc_collection,
        _check_collections_abc_iterable,
        _check_collections_abc_mapping,
        _check_collections_abc_sequence,
        _check_collections_abc_set,
    )

    # Check the cache first
    cached_result = _CACHE.valid_in_cache(type_hint, obj)
    if cached_result is not None:  # Only cached if Immutable
        log.debug(
            "_check_instance_of_typehint: Cache hit for object of type '%s' and type hint '%s'",
            type(obj).__name__, type_hint)
        if cached_result or not raise_on_error:
            return CheckResult(cached_result, IS_IMMUTABLE)
        raise TypeCheckError(
            f"Object of type '{type(obj).__name__}' is not an instance of type hint '{type_hint}'",
            tag=TypeHintsErrorTag.TYPE_HINT_MISMATCH)

    obj_is_immutable: bool = is_immutable(obj)

    # handler for non-runtime Protocols
    if (hasattr(type_hint, '__mro__')
            and any(base is Protocol for base in type_hint.__mro__)
            and not getattr(type_hint, '_is_runtime_protocol', False)):
        if raise_on_error:
            raise TypeCheckError(
                f'Protocol {type_hint} is not runtime checkable.',
                tag=TypeHintsErrorTag.NON_RUNTIME_CHECKABLE_PROTOCOL)
        return CheckResult(NOT_VALID, obj_is_immutable)

    if origin is None and isinstance(type_hint, type):
        if issubclass(type_hint, Mapping):
            origin = type_hint
            args = (Any, Any)
        elif issubclass(type_hint, Iterable):
            origin = type_hint
            args = (Any,)
        elif issubclass(type_hint, Callable):  # type: ignore[arg-type]
            origin = type_hint
            args = (..., Any)

    # Check instance type for generics
    if origin is None:
        valid = isinstance(obj, type_hint)
        if valid:
            if obj_is_immutable:
                _CACHE.add_cache_entry(type_hint, obj, IS_VALID, options.noncachable_types)
            return CheckResult(IS_VALID, obj_is_immutable)
        if raise_on_error:
            raise TypeCheckError(
                f'Object of type {type(obj).__name__} is not an instance of {type_hint} '
                f'(origin = {origin}, args = {args})',
                tag=TypeHintsErrorTag.VALIDATION_FAILED
            )
        return CheckResult(NOT_VALID, obj_is_immutable)

    try:
        if not isinstance(obj, origin):
            if raise_on_error:
                raise TypeCheckError(
                    f'Object of type {type(obj).__name__} is not an instance of {origin.__name__}',
                    tag=TypeHintsErrorTag.VALIDATION_FAILED
                )
            return CheckResult(NOT_VALID, obj_is_immutable)
    except TypeError as exc:
        if isinstance(exc, TypeCheckError):
            raise
        # Some origins may not be valid types for isinstance checks
        if origin in {Required, NotRequired, ReadOnly, Never}:
            raise TypeCheckError(
                f'Origin {origin} ({type_hint}) is not a valid type outside of a TypedDict context.',
                tag=TypeHintsErrorTag.VALIDATION_FAILED) from exc
        raise TypeCheckError(
            f'Origin {origin} ({type_hint}) is not a valid type for isinstance check.',
            tag=TypeHintsErrorTag.VALIDATION_FAILED) from exc

    # If no args, treat as non-parameterized generic
    try:
        if not args and isinstance(obj, type_hint):
            if obj_is_immutable:
                _CACHE.add_cache_entry(type_hint, obj, IS_VALID, options.noncachable_types)
            return CheckResult(IS_VALID, obj_is_immutable)
    except TypeError:
        pass

    # Dispatch to the appropriate container check.
    # The order (most specific to most general) is important.
    # The if..elif chain ensures that only one container check is applied
    # and that it is the most specific one available.
    result: CheckResult | None = None

    new_parents = parents.copy()
    new_parents.add(ValidationState(id(obj), type_hint, context))

    if origin:
        # Fast fail path for collections.abc
        is_collections_abc: bool
        try:
            is_collections_abc = issubclass(origin, (Iterable, Callable))  # type: ignore[arg-type]
        except TypeError:
            is_collections_abc = False

        # primary check path for all collections.abc types
        # Order of checks is important: most specific to most general
        # Each check is mutually exclusive due to the if..elif structure
        # and is designed to pick the most specific applicable check.
        if is_collections_abc:
            if issubclass(origin, Mapping):
                result = _check_collections_abc_mapping(
                    obj, type_hint, origin, args, options, new_parents, raise_on_error)
            elif issubclass(origin, Set):
                result = _check_collections_abc_set(
                    obj, type_hint, origin, args, options, new_parents, raise_on_error)
            elif issubclass(origin, Sequence):
                result = _check_collections_abc_sequence(
                    obj, type_hint, origin, args, options, new_parents, raise_on_error)
            elif issubclass(origin, Collection):
                result = _check_collections_abc_collection(
                    obj, type_hint, origin, args, options, new_parents, raise_on_error)
            elif issubclass(origin, Iterable):
                result = _check_collections_abc_iterable(
                    obj, type_hint, origin, args, options, new_parents, raise_on_error)
            elif issubclass(origin, Callable):  # type: ignore[arg-type]
                result = _check_collections_abc_callable(
                    obj, type_hint, origin, args, raise_on_error)

    if result is not None:
        if result.valid and result.immutable:
            _CACHE.add_cache_entry(type_hint, obj, result.immutable, options.noncachable_types)
        if raise_on_error and not result.valid:
            raise TypeCheckError(
                f"Object of type '{type(obj).__name__}' is not an instance of generic type hint '{type_hint}'",
                tag=TypeHintsErrorTag.TYPE_HINT_MISMATCH)
        return result

    # If we reached here, something very, very wierd is going on.
    # We will raise an error to flag this situation but this should
    # never happen under normal circumstances.
    # There used to be fallback code here, but we couldn't come up with an actual
    # example that reached that code path even with user-defined generics that
    # were manually constructed.
    log.debug(
        "_check_generic: No specific check found for object of type '%s' against generic type hint '%s'",
        type(obj).__name__, type_hint)

    raise TypeCheckError(
        f"Unable to validate object of type '{type(obj).__name__}' against "
        f"generic type hint '{type_hint}'",
        tag=TypeHintsErrorTag.UNHANDLED_GENERIC_TYPE_HINT)
