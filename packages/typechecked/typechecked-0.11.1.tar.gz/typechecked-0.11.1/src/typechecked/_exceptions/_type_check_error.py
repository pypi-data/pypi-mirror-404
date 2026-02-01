"""Class for type check errors."""

from ._error_tag import ErrorTag
from ._tagged_exception import TaggedException, generate_message


class TypeCheckError(TaggedException[TypeError], TypeError):
    """Class for all TypeChecked type check errors.

    It is a specialized TypeError that includes a tag code to identify
    the specific location in the code where the error was raised.

    This tag code is primarily used for testing and debugging purposes.

    Usage:
        raise TypeCheckError("An error occurred", tag=MyErrorTags.SOME_ERROR)

    :param str msg: The error message.
    :param ErrorTag tag: The tag code.
    """
    def __init__(self, msg: str, *, tag: ErrorTag) -> None:
        """Raises a TypeCheckError with the given message and tag.

        :param str msg: The error message.
        :param ErrorTag tag: The tag code.
        """
        message = generate_message(msg, tag)
        super().__init__(message, tag=tag)
