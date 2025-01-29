# Development Guide for `APIClient`

## Overview

This guide provides instructions for developers who wish to contribute to or modify the `APIClient` package. It covers setting up the development environment, running tests, and best practices for contributing.

---

## Table of Contents

1. [Setup](#setup)
2. [Directory Structure](#directory-structure)
3. [Testing](#testing)
4. [Coding Standards](#coding-standards)
5. [Contributing](#contributing)

---

## Setup

### Prerequisites

Ensure you have the following installed:

- Python >= 3.7
- pip (Python package manager)
- git

### Clone the Repository

Clone the repository from GitHub:

```bash
git clone https://github.com/your-repo/datacubepp.git
```

Navigate to the project directory:

```bash
cd datacubepp
```

### Install Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

For development dependencies (e.g., linters, formatters, and testing tools):

```bash
pip install -r dev-requirements.txt
```

---

## Directory Structure

Here is the directory structure of the project:

```
.
├── datacubepp/              # Main package code
│   ├── __init__.py         # Package initialization
│   ├── client.py           # API client implementation
|   ├── endpoints.py        # API endpoints
│   ├── exceptions.py       # Custom exception classes
│   ├── validators.py       # Input validation logic
│   └── settings.py         # Configuration settings
├── tests/                  # Unit and integration tests
│   ├── __init__.py         # Test initialization
│   ├── test_client.py      # Tests for APIClient
│   ├── test_validators.py  # Tests for validation logic
│   └── test_exceptions.py  # Tests for exceptions
├── README.md               # Documentation
├── setup.py                # Package setup
├── requirements.txt        # Production dependencies
├── dev-requirements.txt    # Development dependencies
└── MANIFEST.in             # Additional files for packaging
```

---

## Testing

Run tests using `pytest` to ensure that all functionality is working correctly.

### Running All Tests

```bash
pytest
```

### Running Specific Tests

Run a specific test file:

```bash
pytest tests/test_client.py
```

Run a specific test case:

```bash
pytest tests/test_client.py::test_create_database
```

### Code Coverage

Check test coverage using `pytest-cov`:

```bash
pytest --cov=datacubepp
```

---

## Coding Standards

Follow these coding standards to ensure consistency and quality:

### Style Guide

- Use [PEP 8](https://peps.python.org/pep-0008/) as the style guide.
- Use `black` for code formatting:

  ```bash
  black .
  ```

- Use `pylint` for static code analysis:

  ```bash
  pylint datacubepp
  ```

- Use `mypy` for type checking:

  ```bash
  mypy datacubepp
  ```

### Docstrings

- Write clear and concise docstrings for all public functions and classes using the [Google Style Guide](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods).

### Type Hints

- Use Python type hints to annotate function signatures and variables.

Example:

```python
def create_database(db_name: str, collections: list[dict]) -> dict:
    ...
```

---

## Contributing

### Branching Strategy

1. Create a new branch for your feature or bug fix:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Commit your changes:

   ```bash
   git commit -m "Add your commit message"
   ```

3. Push the branch to the remote repository:

   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request on GitHub and describe your changes.

### Writing Tests

- Write unit tests for any new functionality.
- Ensure all tests pass before submitting your pull request.

### Code Review

- Address all feedback during the code review process.
- Ensure that your changes do not break existing functionality.

---

Happy coding! Feel free to reach out if you encounter any issues or have questions.
