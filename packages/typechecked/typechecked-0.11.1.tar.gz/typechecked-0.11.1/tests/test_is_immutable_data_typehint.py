"""Tests for type hint validation functions."""
# pylint: disable=import-error,wrong-import-position,unused-import
import enum
import logging
import sys
from dataclasses import dataclass
from types import MappingProxyType
from typing import Annotated

import pytest
from testspec import Assert, TestAction, TestSpec, idspec

from typechecked import Immutable, is_immutable_data_typehint

if sys.version_info >= (3, 11):
    from typing import Never, NotRequired, Required  # noqa: F401
else:
    try:
        from typing_extensions import Never, NotRequired, Required  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "TypeChecked requires 'typing_extensions' for Python < 3.11 "
            "to support ReadOnly, Never, NotRequired, and Required.") from e

if sys.version_info >= (3, 13):
    from typing import ReadOnly  # noqa: F401
else:
    try:
        from typing_extensions import ReadOnly  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "TypeChecked requires 'typing_extensions' for Python < 3.13 "
            "to support ReadOnly.") from e

log = logging.getLogger(__name__)


class Color(enum.Enum):
    """Sample enum for testing immutability."""
    RED = 1
    GREEN = 2


class Plain:
    """A plain user-defined class (mutable by default)."""
    def __init__(self, x):
        self.x = x


class Frozen(Immutable):
    """A user-defined class inheriting from Immutable."""
    def __init__(self, x):
        self._x = x


class FrozenWithMutable(Immutable):
    """A user-defined class inheriting from Immutable but containing a mutable attribute."""
    def __init__(self, x):
        self._x = x
        self.lst = []


@dataclass(frozen=True)
class FrozenDataClass:
    """Frozen dataclass for testing immutability."""
    x: int


@dataclass(frozen=False)
class NotFrozenDataClass:
    """Non-frozen dataclass for testing immutability."""
    x: int


@dataclass(frozen=True)
class FrozenDataClassWithMutable:
    """Frozen dataclass containing a mutable attribute."""
    x: list[int]


@pytest.mark.parametrize('testspec', [
    idspec('IMMUTABLE_TYPEHINT_001', TestAction(
        name='int type hint is immutable',
        action=is_immutable_data_typehint, args=[int],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_002', TestAction(
        name='str type hint is immutable',
        action=is_immutable_data_typehint, args=[str],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_003', TestAction(
        name='tuple[int, ...] type hint is immutable',
        action=is_immutable_data_typehint, args=[tuple[int, ...]],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_004', TestAction(
        name='tuple[str, int] type hint is immutable',
        action=is_immutable_data_typehint, args=[tuple[str, int]],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_005', TestAction(
        name='tuple[list[int], ...] type hint is not immutable',
        action=is_immutable_data_typehint, args=[tuple[list[int], ...]],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_TYPEHINT_006', TestAction(
        name='frozenset[int] type hint is immutable',
        action=is_immutable_data_typehint, args=[frozenset[int]],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_007', TestAction(
        name='frozenset[list[int]] type hint is not immutable',
        action=is_immutable_data_typehint, args=[frozenset[list[int]]],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_TYPEHINT_008', TestAction(
        name='MappingProxyType[str, int] type hint is immutable',
        action=is_immutable_data_typehint, args=[MappingProxyType[str, int]],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_009', TestAction(
        name='MappingProxyType[str, list[int]] type hint is not immutable',
        action=is_immutable_data_typehint, args=[MappingProxyType[str, list[int]]],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_TYPEHINT_010', TestAction(
        name='Annotated[int, ...] type hint is immutable',
        action=is_immutable_data_typehint, args=[Annotated[int, 'meta']],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_011', TestAction(
        name='Annotated[list[int], ...] type hint is not immutable',
        action=is_immutable_data_typehint, args=[Annotated[list[int], 'meta']],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_TYPEHINT_012', TestAction(
        name='list[int] type hint is not immutable',
        action=is_immutable_data_typehint, args=[list[int]],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_TYPEHINT_013', TestAction(
        name='dict[str, int] type hint is not immutable',
        action=is_immutable_data_typehint, args=[dict[str, int]],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_TYPEHINT_014', TestAction(
        name='range type hint is immutable',
        action=is_immutable_data_typehint, args=[range],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_TYPEHINT_015', TestAction(
        name='Enum type hint is immutable',
        action=is_immutable_data_typehint, args=[enum.Enum],
        assertion=Assert.TRUE)),
])
def test_is_immutable_data_typehint(testspec: TestSpec) -> None:
    """Test is_immutable_data_typehint for various type hints."""
    testspec.run()
