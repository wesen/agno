# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Setup: `./scripts/dev_setup.sh` (Unix) or `.\scripts\dev_setup.bat` (Windows)
- Format: `./scripts/format.sh` (Unix) or `.\scripts\format.bat` (Windows)
- Validate: `./scripts/validate.sh` (Unix) or `.\scripts\validate.bat` (Windows)
- Test: `./scripts/test.sh`
- Run single test: `pytest path/to/test_file.py::test_function_name`

## Code Style
- Python 3.7+ compatible
- Max line length: 120 characters
- Formatting: Use ruff (`ruff format`)
- Imports: Sorted with `ruff check --select I`
- Types: Type hints required, verified with mypy
- Naming: PascalCase for classes, snake_case for functions/methods
- Error handling: Extend `AgnoError` class for custom exceptions
- Documentation: Use docstrings for public APIs

Run format and validate scripts before submitting changes.