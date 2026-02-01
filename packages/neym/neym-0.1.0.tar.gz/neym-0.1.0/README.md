# neym

A simple Turkish name generator library.

## Description

`neym` is a lightweight Python library that generates random Turkish names. It's perfect for testing, data generation, and any application that needs authentic Turkish names.

## Installation

Install from PyPI:

```bash
pip install neym
```

Or install from the local repository:

```bash
pip install .
```

## Usage

### Generate a Random Turkish Name

```python
from generators.name_generator import generate_turkish_name

name = generate_turkish_name()
print(name)  # Generates a random Turkish name
```

### Get All Available Names

```python
from core.randomizer import names

all_names = names()
print(len(all_names))  # Total number of names
print(all_names[:5])   # First 5 names
```

## Features

- 📚 Comprehensive list of Turkish names
- 🎲 Random name generation
- 🔧 Simple and easy-to-use API
- 🐍 Pure Python, no external dependencies

## Requirements

- Python >= 3.8

## Project Structure

```
neym/
├── core/
│   ├── __init__.py
│   ├── randomizer.py      # Core name loading functionality
│   └── names.txt          # Turkish names database
├── generators/
│   ├── __init__.py
│   └── name_generator.py  # Random name generation
├── pyproject.toml
└── README.md
```

## License

MIT

## Author

Developed by Arif
