"""Random codes."""

import secrets
import string
from collections.abc import Container

ALPHABET = string.ascii_uppercase + string.digits


def generate_code(length: int, taken: Container[str] = ()) -> str:
    """Random code of the given length, not in taken."""
    code = _random_code(length)
    while code in taken:
        code = _random_code(length)
    return code


def _random_code(length: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
