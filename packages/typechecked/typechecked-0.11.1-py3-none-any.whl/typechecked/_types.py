"""Import typing extensions types with fallback for older Python versions.

Imports :class:`Never`, :class:`NotRequired`, :class:`Required`, and :class:`ReadOnly`
from typing_extensions for Python versions that do not have them in the standard typing module.

:raises ImportError: If typing_extensions is not installed for Python < 3.11/3.13.
"""
import sys

if sys.version_info >= (3, 11):
    from typing import Never, NotRequired, Required
else:
    try:
        from typing_extensions import Never, NotRequired, Required
    except ImportError as e:
        raise ImportError(
            "TypeChecked requires 'typing_extensions' for Python < 3.11 "
            "to support Never, Required, NotRequired, ReadOnly.") from e

if sys.version_info >= (3, 13):
    from typing import ReadOnly
else:
    try:
        from typing_extensions import ReadOnly
    except ImportError as e:
        raise ImportError(
            "TypeChecked requires 'typing_extensions' for Python < 3.13 "
            "to support ReadOnly.") from e

__all__ = (
    "Never",
    "NotRequired",
    "Required",
    "ReadOnly",
)
