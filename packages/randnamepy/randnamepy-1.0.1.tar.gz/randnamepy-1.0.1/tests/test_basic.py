"""
Unit tests for the randnamepy library.

This module contains basic tests to verify the functionality of
the name and username generation features.
"""

import unittest
import random

# Import the library
import sys
import os

# Add parent directory to path for testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import randnamepy
from randnamepy import names, usernames, utils


class TestNameGeneration(unittest.TestCase):
    """Tests for name generation functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set seed for reproducibility in some tests
        random.seed(42)
    
    def test_first_name_returns_string(self):
        """Test that first_name returns a non-empty string."""
        name = randnamepy.first_name()
        self.assertIsInstance(name, str)
        self.assertTrue(len(name) > 0)
    
    def test_first_name_male(self):
        """Test that male first names are from the male list."""
        for _ in range(10):
            name = randnamepy.first_name(gender="male")
            self.assertIn(name, names.MALE_FIRST_NAMES)
    
    def test_first_name_female(self):
        """Test that female first names are from the female list."""
        for _ in range(10):
            name = randnamepy.first_name(gender="female")
            self.assertIn(name, names.FEMALE_FIRST_NAMES)
    
    def test_first_name_unisex(self):
        """Test that unisex first names are from the unisex list."""
        for _ in range(10):
            name = randnamepy.first_name(gender="unisex")
            self.assertIn(name, names.UNISEX_FIRST_NAMES)
    
    def test_first_name_invalid_gender(self):
        """Test that invalid gender raises ValueError."""
        with self.assertRaises(ValueError):
            randnamepy.first_name(gender="invalid")
    
    def test_last_name_returns_string(self):
        """Test that last_name returns a non-empty string."""
        name = randnamepy.last_name()
        self.assertIsInstance(name, str)
        self.assertTrue(len(name) > 0)
        self.assertIn(name, names.LAST_NAMES)
    
    def test_full_name_format(self):
        """Test that full_name returns a properly formatted name."""
        name = randnamepy.full_name()
        parts = name.split(" ")
        self.assertEqual(len(parts), 2)
        self.assertTrue(all(len(part) > 0 for part in parts))
    
    def test_get_available_genders(self):
        """Test that available genders list is correct."""
        genders = randnamepy.get_available_genders()
        self.assertIn("male", genders)
        self.assertIn("female", genders)
        self.assertIn("unisex", genders)
        self.assertIn("random", genders)


class TestUsernameGeneration(unittest.TestCase):
    """Tests for username generation functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        random.seed(42)
    
    def test_username_returns_string(self):
        """Test that username returns a non-empty string."""
        uname = randnamepy.username()
        self.assertIsInstance(uname, str)
        self.assertTrue(len(uname) > 0)
    
    def test_username_simple_style(self):
        """Test simple username style."""
        uname = randnamepy.username(style="simple")
        self.assertIsInstance(uname, str)
        # Simple usernames should be lowercase
        self.assertEqual(uname, uname.lower())
    
    def test_username_professional_style(self):
        """Test professional username style."""
        uname = randnamepy.username(style="professional")
        self.assertIsInstance(uname, str)
        self.assertTrue(len(uname) > 0)
    
    def test_username_gamer_style(self):
        """Test gamer username style."""
        uname = randnamepy.username(style="gamer")
        self.assertIsInstance(uname, str)
        self.assertTrue(len(uname) > 0)
    
    def test_username_invalid_style(self):
        """Test that invalid style raises ValueError."""
        with self.assertRaises(ValueError):
            randnamepy.username(style="invalid")
    
    def test_username_without_numbers(self):
        """Test username generation without numbers."""
        # Run multiple times to ensure no numbers
        for _ in range(10):
            uname = randnamepy.username(style="gamer", add_numbers=False)
            # Gamer names without numbers shouldn't end with digits
            self.assertFalse(uname[-1].isdigit())
    
    def test_username_from_name(self):
        """Test username generation from a provided name."""
        uname = randnamepy.username_from_name("Alice")
        self.assertIsInstance(uname, str)
        self.assertIn("alice", uname.lower())
    
    def test_username_from_name_with_last_name(self):
        """Test username generation with both first and last name."""
        uname = randnamepy.username_from_name("Bob", "Wilson", add_numbers=False)
        self.assertIsInstance(uname, str)
        # Should contain parts of the name
        self.assertTrue("bob" in uname or "wilson" in uname)
    
    def test_username_from_name_empty(self):
        """Test that empty first name raises ValueError."""
        with self.assertRaises(ValueError):
            randnamepy.username_from_name("")
    
    def test_get_available_styles(self):
        """Test that available styles list is correct."""
        styles = randnamepy.get_available_styles()
        self.assertIn("simple", styles)
        self.assertIn("professional", styles)
        self.assertIn("gamer", styles)


class TestUtilities(unittest.TestCase):
    """Tests for utility functions."""
    
    def test_random_digits(self):
        """Test random_digits returns correct length."""
        digits = randnamepy.random_digits(5)
        self.assertEqual(len(digits), 5)
        self.assertTrue(digits.isdigit())
    
    def test_random_digits_invalid_length(self):
        """Test that invalid length raises ValueError."""
        with self.assertRaises(ValueError):
            randnamepy.random_digits(0)
        with self.assertRaises(ValueError):
            randnamepy.random_digits(-1)
    
    def test_slugify(self):
        """Test slugify function."""
        self.assertEqual(randnamepy.slugify("John Doe"), "johndoe")
        self.assertEqual(randnamepy.slugify("Mary Jane", separator="_"), "mary_jane")
        self.assertEqual(randnamepy.slugify("O'Brien"), "obrien")
    
    def test_slugify_empty(self):
        """Test slugify with empty string."""
        self.assertEqual(randnamepy.slugify(""), "")
    
    def test_capitalize_words(self):
        """Test capitalize_words function."""
        self.assertEqual(randnamepy.capitalize_words("john doe"), "John Doe")
        self.assertEqual(randnamepy.capitalize_words("MARY JANE"), "Mary Jane")
    
    def test_capitalize_words_empty(self):
        """Test capitalize_words with empty string."""
        self.assertEqual(randnamepy.capitalize_words(""), "")


class TestVersionInfo(unittest.TestCase):
    """Tests for version and metadata."""
    
    def test_version_exists(self):
        """Test that version info exists."""
        self.assertTrue(hasattr(randnamepy, "__version__"))
        self.assertIsInstance(randnamepy.__version__, str)
    
    def test_author_exists(self):
        """Test that author info exists."""
        self.assertTrue(hasattr(randnamepy, "__author__"))
    
    def test_license_exists(self):
        """Test that license info exists."""
        self.assertTrue(hasattr(randnamepy, "__license__"))
        self.assertEqual(randnamepy.__license__, "MIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
