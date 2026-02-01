# Contributing to Edgework

Thank you for your interest in contributing to Edgework! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Poetry (for dependency management)
- Git

### Setting up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/edgework.git
   cd edgework
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

4. Activate the virtual environment:
   ```bash
   poetry shell
   ```

5. Install pre-commit hooks (if available):
   ```bash
   pre-commit install
   ```

## Making Changes

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and small

### Documentation
- Update docstrings when changing function signatures
- Add examples for new features
- Update README.md if adding new functionality

### Testing
- Write tests for new features
- Ensure existing tests still pass
- Aim for good test coverage

Run tests with:
```bash
poetry run pytest
```

## Submitting Changes

### Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request on GitHub

### Pull Request Guidelines
- Use a clear and descriptive title
- Describe what changes you made and why
- Reference any related issues
- Include tests for new functionality
- Update documentation as needed

## Types of Contributions

### Bug Reports
When reporting bugs, please include:
- Python version
- Edgework version
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages

### Feature Requests
For new features:
- Describe the feature and its use case
- Explain why it would be valuable
- Consider if it fits with the project's goals

### Code Contributions
Areas where contributions are welcome:
- Bug fixes
- New API endpoints
- Performance improvements
- Better error handling
- Documentation improvements
- Test coverage improvements

## Code Review Process

1. All pull requests require review
2. Maintainers will review code for:
   - Correctness
   - Code style
   - Test coverage
   - Documentation
3. Address any feedback from reviewers
4. Once approved, the PR will be merged

## Development Guidelines

### API Client Development
- Follow the existing pattern for new endpoints
- Use appropriate error handling
- Include proper logging where needed
- Validate input parameters

### Model Development
- Use dataclasses or similar patterns
- Include proper type hints
- Add docstrings with examples
- Handle API response variations

### Testing Guidelines
- Write unit tests for individual functions
- Write integration tests for API calls
- Mock external API calls in tests
- Test error conditions

## Documentation

### Building Documentation
Documentation is built using MkDocs:

```bash
# Install documentation dependencies
poetry install --extras docs

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### Documentation Standards
- Use clear, concise language
- Include code examples
- Keep examples up to date
- Use proper Markdown formatting

## Getting Help

If you need help with development:
- Check existing issues and discussions
- Create an issue for questions
- Reach out to maintainers

## License

By contributing to Edgework, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- GitHub contributor list
- Documentation acknowledgments

Thank you for contributing to Edgework!
