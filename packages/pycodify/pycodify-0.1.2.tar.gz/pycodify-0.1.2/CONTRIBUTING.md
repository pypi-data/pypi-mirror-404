# Contributing to pycodify

Thank you for your interest in contributing to pycodify! This document provides guidelines for development, testing, and submission.

## Development Setup

### Prerequisites
- Python 3.10+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/OpenHCSDev/pycodify.git
cd pycodify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,docs]"
```

## Code Style

pycodify follows strict code quality standards:

### Formatting
- **Black**: Code formatting (line length: 100)
- **Ruff**: Linting and import sorting
- **MyPy**: Static type checking

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Docstrings
- Use Google-style docstrings
- Include type hints in function signatures
- Document all public APIs

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/pycodify --cov-report=html

# Run specific test file
pytest tests/test_core.py -v
```

### Test Requirements
- Minimum 80% code coverage
- All tests must pass before submission
- Use pytest fixtures for setup/teardown
- Test both collection and regeneration passes

## Submitting Changes

### Before Submitting
1. Ensure all tests pass: `pytest tests/`
2. Format code: `black src/ tests/`
3. Run linter: `ruff check src/ tests/`
4. Type check: `mypy src/`
5. Update documentation if needed

### Pull Request Process
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with clear commit messages
3. Push to your fork and create a Pull Request
4. Ensure CI/CD checks pass
5. Request review from maintainers

### Commit Message Format
```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Documentation

### Building Docs Locally

```bash
cd docs
make html
# Open build/html/index.html in browser
```

### Documentation Standards
- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Document the two-pass algorithm for custom formatters

## Architecture Notes

pycodify uses a two-pass algorithm:
1. **Collection Pass**: Traverse object, emit code fragments, collect imports
2. **Resolution Pass**: Detect collisions, generate aliases, regenerate code

Custom formatters should inherit from `SourceFormatter` and implement:
- `can_format(value)`: Check if formatter handles this type
- `format(value, context)`: Return SourceFragment with code and imports

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Use discussions for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

