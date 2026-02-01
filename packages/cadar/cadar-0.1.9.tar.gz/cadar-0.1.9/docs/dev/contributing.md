# Contributing to CaDaR

Thank you for your interest in contributing to CaDaR! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in [GitHub Issues](https://github.com/Oit-Technologies/CaDaR/issues)
2. If not, create a new issue with:
   - Clear description of the problem/feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Development Setup

See [Building from Source](building.md) for detailed setup instructions.

Quick setup:

```bash
# Clone the repository
git clone https://github.com/Oit-Technologies/CaDaR.git
cd CaDaR

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install maturin

# Build and install in development mode
maturin develop

# Run tests
cargo test
python -m pytest tests/
```

## Code Style

### Rust Code

- Follow Rust standard formatting (`rustfmt`)
- Use `cargo clippy` for linting
- Write documentation comments for public APIs
- Keep functions focused and testable

### Python Code

- Follow PEP 8 style guide
- Use type hints where applicable
- Write docstrings for public functions
- Keep code simple and readable

## Testing

All new features must include tests:

```bash
# Run Rust tests
cargo test

# Run Python tests (if any)
python -m pytest tests/

# Run all tests
./run_tests.sh
```

## Documentation

Update documentation for:
- New features
- API changes
- Breaking changes
- Configuration options

Documentation files are in the `docs/` directory using Markdown format.

## Commit Messages

Write clear commit messages:

```
Add feature: Brief description

- Detailed explanation of changes
- Why the change was needed
- Any breaking changes
```

## Code Review

All contributions will be reviewed before merging. Please be patient and responsive to feedback.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to ask questions by:
- Opening an issue
- Starting a discussion on GitHub

Thank you for contributing to CaDaR!
