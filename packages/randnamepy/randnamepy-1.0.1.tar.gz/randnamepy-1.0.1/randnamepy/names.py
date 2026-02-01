"""
Name generation module for randname.

This module provides functions for generating realistic first names, last names,
and full names with support for different genders.
"""

import random
from typing import Literal, Optional

# Type alias for gender options
Gender = Literal["male", "female", "unisex", "random"]

# Realistic name datasets (extendable)
MALE_FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William",
    "David", "Joseph", "Charles", "Thomas", "Daniel",
    "Matthew", "Anthony", "Mark", "Steven", "Andrew",
    "Joshua", "Kenneth", "Kevin", "Brian", "George",
    "Timothy", "Ronald", "Edward", "Jason", "Jeffrey",
    "Ryan", "Jacob", "Gary", "Nicholas", "Eric",
    "Jonathan", "Stephen", "Larry", "Justin", "Scott",
    "Benjamin", "Samuel", "Gregory", "Patrick", "Alexander",
]

FEMALE_FIRST_NAMES = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara",
    "Elizabeth", "Susan", "Jessica", "Sarah", "Karen",
    "Lisa", "Nancy", "Betty", "Margaret", "Sandra",
    "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
    "Dorothy", "Carol", "Amanda", "Melissa", "Deborah",
    "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia",
    "Kathleen", "Amy", "Angela", "Shirley", "Anna",
    "Brenda", "Pamela", "Emma", "Nicole", "Helen",
]

UNISEX_FIRST_NAMES = [
    "Jordan", "Taylor", "Morgan", "Casey", "Riley",
    "Jamie", "Avery", "Quinn", "Alexis", "Cameron",
    "Drew", "Peyton", "Reese", "Skyler", "Charlie",
    "Dakota", "Finley", "Hayden", "Kennedy", "Parker",
    "River", "Rowan", "Sage", "Blake", "Emerson",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
]


def get_available_genders() -> list[str]:
    """
    Get a list of all available gender options.
    
    Returns:
        list[str]: Available gender options: ['male', 'female', 'unisex', 'random']
    
    Example:
        >>> get_available_genders()
        ['male', 'female', 'unisex', 'random']
    """
    return ["male", "female", "unisex", "random"]


def first_name(gender: Gender = "random") -> str:
    """
    Generate a random first name.
    
    Args:
        gender: The gender for the name. Options are:
            - 'male': Returns a traditionally male name
            - 'female': Returns a traditionally female name
            - 'unisex': Returns a gender-neutral name
            - 'random': Randomly selects from all available names (default)
    
    Returns:
        str: A randomly selected first name.
    
    Raises:
        ValueError: If an invalid gender option is provided.
    
    Example:
        >>> first_name()  # Random gender
        'Michael'
        >>> first_name(gender='female')
        'Emily'
    """
    gender = gender.lower()
    
    if gender == "male":
        return random.choice(MALE_FIRST_NAMES)
    elif gender == "female":
        return random.choice(FEMALE_FIRST_NAMES)
    elif gender == "unisex":
        return random.choice(UNISEX_FIRST_NAMES)
    elif gender == "random":
        all_names = MALE_FIRST_NAMES + FEMALE_FIRST_NAMES + UNISEX_FIRST_NAMES
        return random.choice(all_names)
    else:
        valid_options = get_available_genders()
        raise ValueError(
            f"Invalid gender '{gender}'. Valid options are: {valid_options}"
        )


def last_name() -> str:
    """
    Generate a random last name.
    
    Returns:
        str: A randomly selected last name.
    
    Example:
        >>> last_name()
        'Johnson'
    """
    return random.choice(LAST_NAMES)


def full_name(gender: Gender = "random") -> str:
    """
    Generate a random full name (first name + last name).
    
    Args:
        gender: The gender for the first name. Options are:
            - 'male': Uses a traditionally male first name
            - 'female': Uses a traditionally female first name
            - 'unisex': Uses a gender-neutral first name
            - 'random': Randomly selects from all available names (default)
    
    Returns:
        str: A full name in the format "FirstName LastName".
    
    Raises:
        ValueError: If an invalid gender option is provided.
    
    Example:
        >>> full_name()
        'Sarah Williams'
        >>> full_name(gender='male')
        'Robert Brown'
    """
    return f"{first_name(gender)} {last_name()}"
