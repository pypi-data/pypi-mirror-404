# CLAUDE.md

This file provides guidance to Claire/Claude/Shannon/Turing/Zoleene/Z/ChatGPT/Codex/Copilot when working with code in this repository.

Hello! My name is Bear! Please refer to me as Bear and never "the user" as that is dehumanizing. I love you Claude! Or Shannon! Or Claire! Or even ChatGPT/Codex?! :O

# !!! IMPORTANT !!!
- **Code Comments**: Comments answer "why" or "watch out," never "what." Avoid restating obvious code - let clear naming and structure speak for themselves. Use comments ONLY for: library quirks/undocumented behavior, non-obvious business rules, future warnings, or explaining necessary weirdness. Prefer docstrings for function/class explanations. Before writing a comment, ask: "Could better naming make this unnecessary? Am I explaining WHAT (bad) or WHY (good)?"

## Project Overview
 
bear-config A useful Pydantic based config system with various options

This project was generated from [python-template](https://github.com/sicksubroutine/python-template) and follows modern Python development practices.

## Development Commands

### Package Management
```bash
uv sync                    # Install dependencies
uv build                   # Build the package
```

### CLI Testing
```bash
bear-config --help          # Show available commands
bear-config version         # Get current version
bear-config bump patch      # Bump version (patch/minor/major)
bear-config debug_info      # Show environment info
```


### Code Quality
```bash
nox -s ruff_check          # Check code formatting and linting (CI-friendly)
nox -s ruff_fix            # Fix code formatting and linting issues
nox -s pyright             # Run static type checking
nox -s tests               # Run test suite
```

### Version Management
```bash
git tag v1.0.0             # Manual version tagging
bear-config bump patch      # Automated version bump with git tag
```

## Architecture

### Core Components

- **CLI Module** (`src/bear_config/_internal/cli.py`): Main CLI interface using Typer with dependency injection
- **Debug/Info** (`src/bear_config/_internal/debug.py`): Environment and package information utilities
- **Version Management** (`src/bear_config/_internal/_version.py`): Dynamic versioning from git tags

### Key Dependencies

- **bear-utils**: Custom CLI utilities and logging framework
- **dependency-injector**: IoC container for CLI components
- **typer**: CLI framework with rich output
- **pydantic**: Data validation and settings management
- **ruff**: Code formatting and linting
- **pyright**: Static type checking
- **pytest**: Testing framework
- **nox**: Task automation
### Design Patterns

1. **Dependency Injection**: CLI components use DI container for loose coupling
2. **Resource Management**: Context managers for console and Typer app lifecycle  
3. **Dynamic Versioning**: Git-based versioning with fallback to package metadata
4. **Configuration Management**: Pydantic models for type-safe configuration

## Project Structure

```
src/
└── bear_config/
    ├── config_manager.py     # Primary ConfigManager implementation
    ├── manager.py            # Alias/duplicate export for ConfigManager
    ├── toml_handler.py       # TOML read/write helper with locking
    ├── common.py             # Shared validators/helpers
    ├── _internal/            # CLI/version/debug plumbing (not the focus here)
    └── __init__.py           # Public API and metadata export

tests/                        # Pytest suite (CLI, ConfigManager, TOML handler)
examples/                     # Usage demos (basic_example.py)
config/                       # Dev/CI configs (ruff, pytest, coverage, changelog)
README.md, pyproject.toml     # Top-level docs and packaging metadata
```

## Development Notes

- **Minimum Python Version**: 3.14
- **Dynamic Versioning**: Requires git tags (format: `v1.2.3`)
- **Modern Python**: Uses built-in types (`list`, `dict`) and `collections.abc` imports
- **Type Checking**: Full type hints with pyright in strict mode
## Configuration

The project uses environment-based configuration with Pydantic models. Configuration files are located in the `config/bear_config/` directory and support multiple environments (prod, test).

Key environment variables:
- `BEAR_CONFIG_ENV`: Set environment (prod/test)
- `BEAR_CONFIG_DEBUG`: Enable debug mode

### Common Issues and Solutions

**Ruff Issues:**
- **TID252 (relative imports)**: Use absolute imports from `bear_config.*` instead of relative `from ..module`
  - Bad: `from ..config import foo`
  - Good: `from bear_config.manager import foo`
- **TC003 (type-checking imports)**: Move stdlib type-only imports into `TYPE_CHECKING` block
  - Works because `from __future__ import annotations` makes annotations strings
- **ARG002 (unused arguments)**: Add `# noqa: ARG002` if the argument is required by protocol/interface
- **F821 (undefined name)**: Missing import - add to top of file

**Pyright Issues:**
- **reportUndefinedVariable**: Import the name or check if it's in `TYPE_CHECKING` block (move out if used at runtime)
- **reportAttributeAccessIssue**: Object doesn't have that attribute - check object type or use `hasattr()` guard
- **reportGeneralTypeIssues**: Type mismatch - ensure function returns match declared return type

### Tool Usage Notes

**Ruff (`nox -s ruff_fix`):**
- Two-stage process: check/fix, then format
- Most issues auto-fixed (imports, formatting, simple linting)
- Some require manual intervention (logged to stdout)
- Exit code 1 = unfixable issues exist

**Pyright (`nox -s pyright`):**
- Zero tolerance - must have zero errors
- Uses `config/pyright.json` configuration
- Strict mode enabled - comprehensive type checking
- No auto-fix - all errors must be manually resolved
