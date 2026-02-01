"""
Username generation module for randname.

This module provides functions for generating usernames in various styles,
either randomly or based on provided names.
"""

import random
from typing import Literal, Optional

from .names import first_name, last_name
from .utils import random_digits, slugify

# Type alias for username styles
UsernameStyle = Literal["simple", "professional", "gamer"]

# Gamer-style prefixes and suffixes
GAMER_PREFIXES = [
    "Shadow", "Dark", "Night", "Storm", "Fire",
    "Ice", "Thunder", "Frost", "Blaze", "Steel",
    "Iron", "Cyber", "Neo", "Phantom", "Ghost",
    "Ninja", "Elite", "Pro", "Ultra", "Mega",
    "Super", "Hyper", "Turbo", "Alpha", "Omega",
]

GAMER_SUFFIXES = [
    "Hunter", "Slayer", "Master", "Warrior", "Knight",
    "Dragon", "Wolf", "Tiger", "Phoenix", "Hawk",
    "Viper", "Blade", "Strike", "Force", "Guard",
    "Sniper", "Gamer", "Player", "Legend", "King",
    "Lord", "Boss", "Chief", "Ace", "Star",
]

# Professional title additions
PROFESSIONAL_SEPARATORS = [".", "_", ""]


def get_available_styles() -> list[str]:
    """
    Get a list of all available username styles.
    
    Returns:
        list[str]: Available style options: ['simple', 'professional', 'gamer']
    
    Example:
        >>> get_available_styles()
        ['simple', 'professional', 'gamer']
    """
    return ["simple", "professional", "gamer"]


def _generate_simple_username(fname: str, lname: str, add_numbers: bool = True) -> str:
    """
    Generate a simple username from first and last name.
    
    Formats: firstname, firstnamelastname, firstnamelastinitial, etc.
    """
    fname = fname.lower()
    lname = lname.lower()
    
    patterns = [
        fname,                              # john
        f"{fname}{lname}",                  # johnsmith
        f"{fname}{lname[0]}",               # johns
        f"{fname[0]}{lname}",               # jsmith
        f"{fname}_{lname}",                 # john_smith
        f"{fname}{lname[:3]}",              # johnsmi
    ]
    
    base = random.choice(patterns)
    
    if add_numbers and random.random() > 0.5:
        base += random_digits(random.randint(1, 4))
    
    return base


def _generate_professional_username(fname: str, lname: str, add_numbers: bool = True) -> str:
    """
    Generate a professional-looking username from first and last name.
    
    Formats: firstname.lastname, f.lastname, firstname_l, etc.
    """
    fname = fname.lower()
    lname = lname.lower()
    sep = random.choice(PROFESSIONAL_SEPARATORS)
    
    patterns = [
        f"{fname}{sep}{lname}",             # john.smith
        f"{fname[0]}{sep}{lname}",          # j.smith
        f"{fname}{sep}{lname[0]}",          # john.s
        f"{lname}{sep}{fname}",             # smith.john
        f"{lname}{sep}{fname[0]}",          # smith.j
    ]
    
    base = random.choice(patterns)
    
    if add_numbers and random.random() > 0.7:
        base += random_digits(random.randint(2, 4))
    
    return base


def _generate_gamer_username(add_numbers: bool = True) -> str:
    """
    Generate a gamer-style username with cool prefixes/suffixes.
    
    Formats: PrefixSuffix, PrefixSuffix123, etc.
    """
    # Different generation patterns
    pattern = random.randint(1, 4)
    
    if pattern == 1:
        # Prefix + Suffix
        base = random.choice(GAMER_PREFIXES) + random.choice(GAMER_SUFFIXES)
    elif pattern == 2:
        # Double prefix
        base = random.choice(GAMER_PREFIXES) + random.choice(GAMER_PREFIXES)
    elif pattern == 3:
        # Single word with x or X
        word = random.choice(GAMER_PREFIXES + GAMER_SUFFIXES)
        if random.random() > 0.5:
            base = f"x{word}x"
        else:
            base = f"X{word}X"
    else:
        # Prefix + short word
        base = random.choice(GAMER_PREFIXES) + random.choice(["X", "Z", "0", "xX"])
    
    if add_numbers:
        base += random_digits(random.randint(2, 4))
    
    return base


def username(style: UsernameStyle = "simple", add_numbers: bool = True) -> str:
    """
    Generate a random username in the specified style.
    
    Args:
        style: The style of username to generate. Options are:
            - 'simple': Basic usernames like 'johnsmith42' (default)
            - 'professional': Professional usernames like 'john.smith'
            - 'gamer': Gaming-style usernames like 'ShadowHunter99'
        add_numbers: Whether to append random numbers to the username.
            Defaults to True.
    
    Returns:
        str: A randomly generated username.
    
    Raises:
        ValueError: If an invalid style option is provided.
    
    Example:
        >>> username()
        'michael_johnson23'
        >>> username(style='gamer')
        'NightPhoenix42'
        >>> username(style='professional', add_numbers=False)
        'j.williams'
    """
    style = style.lower()
    
    if style == "gamer":
        return _generate_gamer_username(add_numbers)
    
    # For simple and professional styles, we need names
    fname = first_name()
    lname = last_name()
    
    if style == "simple":
        return _generate_simple_username(fname, lname, add_numbers)
    elif style == "professional":
        return _generate_professional_username(fname, lname, add_numbers)
    else:
        valid_options = get_available_styles()
        raise ValueError(
            f"Invalid style '{style}'. Valid options are: {valid_options}"
        )


def username_from_name(
    fname: str,
    lname: Optional[str] = None,
    style: UsernameStyle = "simple",
    add_numbers: bool = True,
) -> str:
    """
    Generate a username from a provided name.
    
    Args:
        fname: The first name to base the username on.
        lname: The last name to use. If not provided, a random one is used.
        style: The style of username to generate. Options are:
            - 'simple': Basic usernames like 'johnsmith42' (default)
            - 'professional': Professional usernames like 'john.smith'
            - 'gamer': Gaming-style usernames (ignores name input)
        add_numbers: Whether to append random numbers to the username.
            Defaults to True.
    
    Returns:
        str: A username based on the provided name(s).
    
    Raises:
        ValueError: If an invalid style option is provided.
    
    Example:
        >>> username_from_name('Alice')
        'alice_garcia87'
        >>> username_from_name('Bob', 'Wilson', style='professional')
        'b.wilson'
    """
    if not fname or not fname.strip():
        raise ValueError("First name cannot be empty")
    
    fname = slugify(fname.strip())
    lname = slugify(lname.strip()) if lname else last_name().lower()
    
    style = style.lower()
    
    if style == "simple":
        return _generate_simple_username(fname, lname, add_numbers)
    elif style == "professional":
        return _generate_professional_username(fname, lname, add_numbers)
    elif style == "gamer":
        # Gamer style ignores name input
        return _generate_gamer_username(add_numbers)
    else:
        valid_options = get_available_styles()
        raise ValueError(
            f"Invalid style '{style}'. Valid options are: {valid_options}"
        )
