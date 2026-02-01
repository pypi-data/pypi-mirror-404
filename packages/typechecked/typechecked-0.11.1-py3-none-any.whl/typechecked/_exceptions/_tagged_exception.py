"""The tagged exception base class.

This module defines the TaggedException base class, which extends the built-in Exception class
and adds a mandatory tag attribute. The tag is intended to provide additional context or categorization
for the exception. The tag is be to be an instance of Enum to ensure a controlled set of possible tags.
This ensures that the tag is always valid and can be used to categorize exceptions in a consistent
and meaningful way."""
from enum import Enum
from textwrap import dedent
import re
from typing import Any, Generic, TypeVar

from ._error_tag import ErrorTag

E = TypeVar('E', bound=Exception)


class TaggedException(Exception, Generic[E]):
    """
    A generic exception that can be specialized with a base exception type
    and requires a tag during instantiation.

    This class extends the built-in Exception class and adds a mandatory tag
    attribute. The tag is intended to provide additional context or categorization
    for the exception.

    The tag must be an instance of Enum to ensure a controlled set of possible tags and
    must be the first argument provided during instantiation if passed positionally.

    It is used by other exceptions in the typechecked package to provide
    standardized error tagging for easier identification and handling of specific error conditions.
    and is used to create exceptions with specific tags for error handling and identification.
    with this base class.

    Example:

    class MyTaggedException(TaggedException[ValueError]):
    '''A tagged exception that is a specialized ValueError.'''

    raise MyTaggedException("An error occurred", tag=MyErrorTags.SOME_ERROR)


    Args:
        tag (Enum, keyword): An Enum member representing the error code.
        *args: Positional arguments to pass to the base exception's constructor.
        **kwargs: Keyword arguments to pass to the base exception's constructor.

    Attributes:
        tag_code: Enum
    """
    def __init__(self, *args: Any, tag: Enum, **kwargs: Any) -> None:
        """
        Initializes the exception with a mandatory tag.

        Args:
            *args: Positional arguments to pass to the base exception's constructor.
            tag (Enum, keyword): An Enum member representing the error code.
            **kwargs: Keyword arguments to pass to the base exception's constructor.
        """
        if not isinstance(tag, Enum):
            raise TypeError("Missing or wrong type 'tag' argument (must be Enum)")
        self.tag_code = tag
        super().__init__(*args, **kwargs)


def dedent_and_normalize_whitespace(text: str) -> str:
    """Dedent and and normalize whitespace.

    * \\n and \\t characters are removed.
    * Leading and trailing whitespace is removed.
    * Multiple consecutive whitespace characters are reduced to a single space.

    Args:
        text (str): The text to dedent and strip.

    Returns:
        str: The dedented and normalized text.
    """
    dedented_text = dedent(text)
    no_newlines_tabs = dedented_text.replace('\n', ' ').replace('\t', ' ')
    normalized_whitespace = re.sub(re.compile(r'\s+'), ' ', no_newlines_tabs)
    return normalized_whitespace.strip()


def generate_message(msg: str, tag: ErrorTag) -> str:
    """Generate an error message with the given tag.

    :param str msg: The base error message.
    :param ErrorTag tag: The error tag.
    :return str: The generated error message.
    """
    if tag.__doc__ is None:
        message = f"{msg}: {tag.value}"
    else:
        message = f"{msg}: {dedent_and_normalize_whitespace(tag.__doc__)}"
    return message.replace('\n', '')
