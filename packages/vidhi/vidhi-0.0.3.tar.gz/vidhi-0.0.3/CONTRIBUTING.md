# Contributing to Vidhi

Thank you for your interest in contributing to Vidhi! This document provides guidelines for contributing to the project.

## Getting Started

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/project-vajra/vidhi.git
   cd vidhi
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_frozen_dataclass.py -v
```

### Code Formatting

```bash
# Format code
make format

# Run linters
make lint
```

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [GitHub Issues](https://github.com/project-vajra/vidhi/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Python version and OS
   - Minimal code example if possible

### Suggesting Features

1. Open a new issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Any alternatives you've considered

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Ensure all tests pass
5. Run `make format` and `make lint`
6. Submit a pull request

#### Pull Request Guidelines

- Keep PRs focused on a single change
- Write clear commit messages
- Add tests for new functionality
- Update documentation as needed
- Follow the existing code style

## Code Style

- Use [Black](https://github.com/psf/black) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write docstrings for public functions

## Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Use pytest for testing
- Keep tests focused and readable

## Documentation

- Update README.md for user-facing changes
- Update docs/USER_GUIDE.md for new features
- Add docstrings to new functions/classes
- Include code examples where helpful

## Questions?

Feel free to open an issue for any questions about contributing.
