"""
randname - A Python library for generating realistic random names and usernames.

This library provides simple, dependency-free utilities for generating:
- Random full names (first + last) with gender support
- Usernames in various styles (simple, professional, gamer)
- Helper utilities for testing and placeholder data

Example:
    >>> import randname
    >>> randname.full_name()
    'John Smith'
    >>> randname.username(style='gamer')
    'ShadowHunter42'
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from .names import (
    first_name,
    last_name,
    full_name,
    get_available_genders,
)

from .usernames import (
    username,
    username_from_name,
    get_available_styles,
)

from .utils import (
    random_digits,
    slugify,
    capitalize_words,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Name generators
    "first_name",
    "last_name",
    "full_name",
    "get_available_genders",
    # Username generators
    "username",
    "username_from_name",
    "get_available_styles",
    # Utilities
    "random_digits",
    "slugify",
    "capitalize_words",
]
