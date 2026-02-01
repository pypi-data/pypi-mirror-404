# Contributing to OR-AF

Thank you for your interest in contributing to OR-AF! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/or-af.git
   cd or-af
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install in development mode:
   ```bash
   pip install -e .[dev]
   ```

## Development Workflow

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test thoroughly

3. Run linters:
   ```bash
   black or_af/
   flake8 or_af/
   mypy or_af/
   ```

4. Run tests:
   ```bash
   pytest tests/
   ```

5. Commit your changes with a clear message:
   ```bash
   git commit -m "Add feature: description"
   ```

6. Push to your fork and create a Pull Request

## Code Style

- Follow PEP 8 guidelines
- Use type hints wherever possible
- Write docstrings for all public functions and classes
- Keep functions focused and under 50 lines when possible

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for high code coverage

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the version number following semantic versioning
3. The PR will be merged once you have sign-off from maintainers

## Questions?

Feel free to open an issue for any questions or concerns.
