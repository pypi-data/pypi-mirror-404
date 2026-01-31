"""UUID7 utilities for time-sortable unique identifiers."""

from uuid import UUID

from uuid_utils import uuid7 as _uuid7


def uuid7() -> UUID:
    """
    Generate a UUID version 7.

    UUID7 is time-sortable and provides better database index locality
    than UUID4. The timestamp is encoded in the first 48 bits.

    Returns:
        A new UUID7 instance.

    Example:
        >>> user_id = uuid7()
        >>> print(user_id)
        019449a0-5c80-7000-8000-000000000000
    """
    return _uuid7()


def uuid7_str() -> str:
    """
    Generate a UUID7 as a string.

    Returns:
        A new UUID7 as lowercase hyphenated string.

    Example:
        >>> user_id = uuid7_str()
        >>> print(user_id)
        '019449a0-5c80-7000-8000-000000000000'
    """
    return str(_uuid7())
