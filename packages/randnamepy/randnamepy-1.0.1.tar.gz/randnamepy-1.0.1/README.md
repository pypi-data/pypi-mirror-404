# randname

A lightweight, dependency-free Python library for generating realistic random names, usernames, and placeholder data for testing purposes.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/randname.svg)](https://badge.fury.io/py/randname)

## ✨ Features

- 🎯 **Zero dependencies** - Uses only Python standard library
- 📝 **Realistic names** - Curated datasets of real first and last names
- 👤 **Gender support** - Male, female, unisex, or random name generation
- 🎮 **Username styles** - Simple, professional, and gamer-style usernames
- 🔤 **Type hints** - Full type annotation support
- 📚 **Well documented** - Comprehensive docstrings and examples

## 📦 Installation

```bash
pip install randname
```

Or install from source:

```bash
git clone https://github.com/yourusername/randname.git
cd randname
pip install -e .
```

## 🚀 Quick Start

```python
import randname

# Generate random names
print(randname.full_name())           # "Sarah Johnson"
print(randname.first_name())          # "Michael"
print(randname.last_name())           # "Williams"

# Generate with specific gender
print(randname.full_name(gender="male"))     # "Robert Brown"
print(randname.full_name(gender="female"))   # "Emily Garcia"
print(randname.full_name(gender="unisex"))   # "Jordan Taylor"

# Generate usernames
print(randname.username())                           # "michael_johnson23"
print(randname.username(style="professional"))       # "m.smith"
print(randname.username(style="gamer"))              # "ShadowHunter99"

# Generate username from a specific name
print(randname.username_from_name("Alice"))                    # "alice_martinez42"
print(randname.username_from_name("Bob", "Wilson"))            # "bobwilson"
print(randname.username_from_name("Jane", style="professional")) # "j.doe"
```

## 📖 API Reference

### Name Generation

#### `first_name(gender="random")`

Generate a random first name.

**Parameters:**
- `gender` (str): One of `"male"`, `"female"`, `"unisex"`, or `"random"` (default)

**Returns:** `str` - A randomly selected first name

```python
randname.first_name()                  # Any gender
randname.first_name(gender="male")     # Male name
randname.first_name(gender="female")   # Female name
randname.first_name(gender="unisex")   # Gender-neutral name
```

#### `last_name()`

Generate a random last name.

**Returns:** `str` - A randomly selected last name

```python
randname.last_name()  # "Johnson"
```

#### `full_name(gender="random")`

Generate a random full name (first + last).

**Parameters:**
- `gender` (str): One of `"male"`, `"female"`, `"unisex"`, or `"random"` (default)

**Returns:** `str` - A full name in "FirstName LastName" format

```python
randname.full_name()                   # "Emma Wilson"
randname.full_name(gender="male")      # "James Anderson"
```

#### `get_available_genders()`

Get a list of all available gender options.

**Returns:** `list[str]` - `["male", "female", "unisex", "random"]`

---

### Username Generation

#### `username(style="simple", add_numbers=True)`

Generate a random username.

**Parameters:**
- `style` (str): One of `"simple"`, `"professional"`, or `"gamer"` (default: `"simple"`)
- `add_numbers` (bool): Whether to append random numbers (default: `True`)

**Returns:** `str` - A randomly generated username

```python
randname.username()                                # "johnsmith42"
randname.username(style="simple")                  # "sarah_jones87"
randname.username(style="professional")            # "j.williams"
randname.username(style="gamer")                   # "NightPhoenix99"
randname.username(style="gamer", add_numbers=False)  # "ShadowHunter"
```

#### `username_from_name(fname, lname=None, style="simple", add_numbers=True)`

Generate a username from a provided name.

**Parameters:**
- `fname` (str): First name to base the username on
- `lname` (str, optional): Last name (random if not provided)
- `style` (str): Username style (default: `"simple"`)
- `add_numbers` (bool): Whether to append random numbers (default: `True`)

**Returns:** `str` - A username based on the provided name

```python
randname.username_from_name("Alice")                         # "alicesmith23"
randname.username_from_name("Bob", "Wilson")                 # "bob_wilson"
randname.username_from_name("Jane", style="professional")    # "j.doe"
```

#### `get_available_styles()`

Get a list of all available username styles.

**Returns:** `list[str]` - `["simple", "professional", "gamer"]`

---

### Utility Functions

#### `random_digits(length=4)`

Generate a string of random digits.

```python
randname.random_digits(4)   # "8472"
randname.random_digits(6)   # "123456"
```

#### `slugify(text, separator="")`

Convert a string to a URL/username-safe slug.

```python
randname.slugify("John Doe")              # "johndoe"
randname.slugify("Mary Jane", "_")        # "mary_jane"
randname.slugify("O'Brien")               # "obrien"
```

#### `capitalize_words(text)`

Capitalize the first letter of each word.

```python
randname.capitalize_words("john doe")     # "John Doe"
```

## 🎨 Username Styles Explained

| Style | Description | Examples |
|-------|-------------|----------|
| `simple` | Lowercase, basic formats | `johnsmith`, `john_doe42`, `jsmith` |
| `professional` | Clean, work-appropriate | `john.smith`, `j.doe`, `smith.j` |
| `gamer` | Cool prefixes/suffixes | `ShadowHunter99`, `NightPhoenix`, `xDragonx` |

## 🧪 Running Tests

```bash
# Run with unittest
python -m pytest tests/ -v

# Or directly
python tests/test_basic.py
```

## 📁 Project Structure

```
randname/
├── randname/                 # Main package
│   ├── __init__.py          # Public API
│   ├── names.py             # Name generation logic
│   ├── usernames.py         # Username generation logic
│   └── utils.py             # Helper utilities
├── tests/                   # Unit tests
│   └── test_basic.py
├── README.md                # This file
├── LICENSE                  # MIT License
├── pyproject.toml          # Package configuration
└── .gitignore
```

## 🔧 Development

```bash
# Clone the repository
git clone https://github.com/yourusername/randname.git
cd randname

# Install in development mode
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## 📋 Extending the Name Dataset

You can easily extend the name datasets by importing and modifying the lists:

```python
from randname.names import MALE_FIRST_NAMES, FEMALE_FIRST_NAMES, LAST_NAMES

# Add custom names
MALE_FIRST_NAMES.extend(["Krishna", "Arjun", "Rahul"])
FEMALE_FIRST_NAMES.extend(["Priya", "Ananya", "Sneha"])
LAST_NAMES.extend(["Patel", "Sharma", "Kumar"])
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for simple, dependency-free test data generation
- Name datasets curated from common names across various cultures

---

Made with ❤️ for developers who need quick, realistic test data.
