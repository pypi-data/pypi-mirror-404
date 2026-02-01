# ghnova

[![Python CI](https://github.com/isaac-cf-wong/ghnova/actions/workflows/CI.yml/badge.svg)](https://github.com/isaac-cf-wong/ghnova/actions/workflows/CI.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/isaac-cf-wong/ghnova/main.svg)](https://results.pre-commit.ci/latest/github/isaac-cf-wong/ghnova/main)
[![Documentation Status](https://github.com/isaac-cf-wong/ghnova/actions/workflows/documentation.yml/badge.svg)](https://isaac-cf-wong.github.io/ghnova/)
[![codecov](https://codecov.io/gh/isaac-cf-wong/ghnova/graph/badge.svg?token=COF8341N60)](https://codecov.io/gh/isaac-cf-wong/ghnova)
[![PyPI Version](https://img.shields.io/pypi/v/ghnova)](https://pypi.org/project/ghnova/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ghnova)](https://pypi.org/project/ghnova/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![DOI](https://zenodo.org/badge/1136398756.svg)](https://doi.org/10.5281/zenodo.18290200)

**Note:** This project is still in progress. The promised features are not fully ready yet, and APIs are subject to change.

A Python package for interacting with the GitHub API.
This package provides a simple and intuitive interface to access
GitHub repositories, users, organizations, issues, and more,
enabling seamless integration with GitHub instances for automation, data retrieval, and management tasks.

## Features

Full API Coverage: Access to repositories, users, organizations, issues, pull requests, and more.

- Easy Authentication: Support for token-based authentication.
- Asynchronous Support: Built with async/await for non-blocking operations.
- Type Hints: Full type annotations for better IDE support and code reliability.
- Comprehensive Documentation: Detailed guides and API reference.
- Command-Line Interface: Interact with the GitHub API directly from the terminal for
  quick, scriptable operations without writing code.

## Installation

We recommend using `uv` to manage virtual environments for installing `ghnova`.

If you don't have `uv` installed, you can install it with pip. See the project pages for more details:

- Install via pip: `pip install --upgrade pip && pip install uv`
- Project pages: [uv on PyPI](https://pypi.org/project/uv/) | [uv on GitHub](https://github.com/astral-sh/uv)
- Full documentation and usage guide: [uv docs](https://docs.astral.sh/uv/)

### Requirements

- Python 3.10 or higher
- Operating System: Linux, macOS, or Windows

### Install from PyPI

The recommended way to install `ghnova` is from PyPI:

```bash
# Create a virtual environment (recommended with uv)
uv venv --python 3.10
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install ghnova
```

#### Optional Dependencies

For development or specific features:

```bash
# Development dependencies (testing, linting, etc.)
uv pip install ghnova[dev]

# Documentation dependencies
uv pip install ghnova[docs]

# All dependencies
uv pip install ghnova[dev,docs]
```

### Install from Source

For the latest development version:

```bash
git clone git@github.com:isaac-cf-wong/ghnova.git
cd ghnova
# Create a virtual environment (recommended with uv)
uv venv --python 3.10
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install .
```

#### Development Installation

To set up for development:

```bash
git clone git@github.com:isaac-cf-wong/ghnova.git
cd ghnova

# Create a virtual environment (recommended with uv)
uv venv --python 3.10
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install ".[dev]"

# Install the commitlint dependencies
npm install

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Verify Installation

Check that `ghnova` is installed correctly:

```bash
ghnova --help
```

```bash
python -c "import ghnova; print(ghnova.__version__)"
```

## Release Schedule

Releases follow a fixed schedule: every Tuesday at 00:00 UTC,
unless an emergent bugfix is required.
This ensures predictable updates while allowing flexibility for critical issues.
Users can view upcoming changes in the draft release on the
[GitHub Releases page](https://github.com/isaac-cf-wong/ghnova/releases).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions, please:

- Check the [documentation](https://isaac-cf-wong.github.io/ghnova/)
- Open an issue on [GitHub](https://github.com/isaac-cf-wong/ghnova/issues)
- Join our [discussions](https://github.com/isaac-cf-wong/ghnova/discussions)

## Changelog

See [Release Notes](https://github.com/isaac-cf-wong/ghnova/releases) for version history.
