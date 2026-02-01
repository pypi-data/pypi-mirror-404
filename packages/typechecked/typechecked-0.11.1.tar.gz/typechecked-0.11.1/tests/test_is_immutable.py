"""Tests for type hint validation functions."""
# pylint: disable=import-error,wrong-import-position,unused-import
import enum
import logging
import sys
from dataclasses import dataclass
from types import MappingProxyType

import pytest
from testspec import Assert, TestAction, TestSpec, idspec

from typechecked import Immutable, is_immutable

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
    """A frozen dataclass."""
    x: int


@dataclass(frozen=False)
class NotFrozenDataClass:
    """A non-frozen dataclass."""
    x: int


@dataclass(frozen=True)
class FrozenDataClassWithMutable:
    """Frozen dataclass with a mutable field."""
    x: list[int]


@pytest.mark.parametrize('testspec', [
    idspec('IMMUTABLE_001', TestAction(
        name='int is immutable',
        action=is_immutable, args=[1],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_002', TestAction(
        name='str is immutable',
        action=is_immutable, args=['abc'],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_003', TestAction(
        name='tuple of ints is immutable',
        action=is_immutable, args=[(1, 2, 3)],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_004', TestAction(
        name='tuple with mutable element is not immutable',
        action=is_immutable, args=[(1, [2, 3])],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_005', TestAction(
        name='frozenset is immutable',
        action=is_immutable, args=[frozenset({1, 2})],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_006', TestAction(
        name='MappingProxyType is immutable',
        action=is_immutable, args=[MappingProxyType({'a': 1})],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_007', TestAction(
        name='MappingProxyType with mutable value is not immutable',
        action=is_immutable, args=[MappingProxyType({'a': [1, 2]})],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_008', TestAction(
        name='enum is immutable',
        action=is_immutable, args=[Color.RED],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_009', TestAction(
        name='list is not immutable',
        action=is_immutable, args=[[1, 2, 3]],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_010', TestAction(
        name='dict is not immutable',
        action=is_immutable, args=[{'a': 1}],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_011', TestAction(
        name='nested immutable containers',
        action=is_immutable, args=[(frozenset({1, 2}), MappingProxyType({'a': (1, 2)}))],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_012', TestAction(
        name='nested with mutable inside',
        action=is_immutable, args=[(frozenset({1, 2}), MappingProxyType({'a': [1, 2]}))],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_013', TestAction(
        name='plain user class is not immutable',
        action=is_immutable, args=[Plain(1)],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_014', TestAction(
        name='user class inheriting Immutable is immutable',
        action=is_immutable, args=[Frozen(1)],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_015', TestAction(
        name='user class inheriting Immutable but with mutable attribute is still considered immutable',
        action=is_immutable, args=[FrozenWithMutable(1)],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_016', TestAction(
        name='frozen dataclass is immutable',
        action=is_immutable, args=[FrozenDataClass(1)],
        assertion=Assert.TRUE)),
    idspec('IMMUTABLE_017', TestAction(
        name='not frozen dataclass is not immutable',
        action=is_immutable, args=[NotFrozenDataClass(1)],
        assertion=Assert.FALSE)),
    idspec('IMMUTABLE_018', TestAction(
        name='frozen dataclass with mutable field is not immutable',
        action=is_immutable, args=[FrozenDataClassWithMutable([1, 2, 3])],
        assertion=Assert.FALSE)),
])
def test_is_immutable(testspec: TestSpec) -> None:
    """Test is_immutable for various objects."""
    testspec.run()
