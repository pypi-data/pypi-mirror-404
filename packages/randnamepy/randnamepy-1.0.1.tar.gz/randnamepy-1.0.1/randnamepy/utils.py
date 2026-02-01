"""
Utility functions for randname.

This module provides helper functions used across the library,
including string manipulation and random data generation utilities.
"""

import random
import re
from typing import Optional


def random_digits(length: int = 4) -> str:
    """
    Generate a string of random digits.
    
    Args:
        length: The number of digits to generate. Defaults to 4.
            Must be a positive integer.
    
    Returns:
        str: A string containing random digits.
    
    Raises:
        ValueError: If length is not a positive integer.
    
    Example:
        >>> random_digits(3)
        '847'
        >>> random_digits(6)
        '123456'
    """
    if length < 1:
        raise ValueError("Length must be a positive integer")
    
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def slugify(text: str, separator: str = "") -> str:
    """
    Convert a string to a URL/username-safe slug.
    
    This function:
    - Converts to lowercase
    - Removes special characters
    - Replaces spaces with the separator
    - Strips leading/trailing whitespace
    
    Args:
        text: The text to slugify.
        separator: Character to replace spaces with. Defaults to empty string.
    
    Returns:
        str: The slugified text.
    
    Example:
        >>> slugify("John Doe")
        'johndoe'
        >>> slugify("Mary Jane", separator="_")
        'mary_jane'
        >>> slugify("O'Brien")
        'obrien'
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower().strip()
    
    # Replace spaces with separator
    text = text.replace(" ", separator)
    
    # Remove non-alphanumeric characters (except separator)
    if separator:
        pattern = f"[^a-z0-9{re.escape(separator)}]"
    else:
        pattern = "[^a-z0-9]"
    text = re.sub(pattern, "", text)
    
    return text


def capitalize_words(text: str) -> str:
    """
    Capitalize the first letter of each word in a string.
    
    This is similar to str.title() but handles edge cases better,
    particularly with apostrophes and mixed case.
    
    Args:
        text: The text to capitalize.
    
    Returns:
        str: The text with each word capitalized.
    
    Example:
        >>> capitalize_words("john doe")
        'John Doe'
        >>> capitalize_words("mary jane watson")
        'Mary Jane Watson'
    """
    if not text:
        return ""
    
    return " ".join(word.capitalize() for word in text.split())


def random_choice(items: list) -> any:
    """
    Safely select a random item from a list.
    
    Args:
        items: A list of items to choose from.
    
    Returns:
        A randomly selected item from the list.
    
    Raises:
        ValueError: If the list is empty.
    
    Example:
        >>> random_choice(['apple', 'banana', 'cherry'])
        'banana'
    """
    if not items:
        raise ValueError("Cannot choose from an empty list")
    
    return random.choice(items)


def truncate(text: str, max_length: int, suffix: str = "") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: The text to truncate.
        max_length: The maximum length of the resulting string
            (including suffix).
        suffix: Optional suffix to append when truncating.
    
    Returns:
        str: The truncated text.
    
    Raises:
        ValueError: If max_length is less than the length of suffix.
    
    Example:
        >>> truncate("Hello World", 8)
        'Hello Wo'
        >>> truncate("Hello World", 8, "...")
        'Hello...'
    """
    if max_length < len(suffix):
        raise ValueError("max_length must be >= length of suffix")
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
