# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `sane-settings`, a Python library for environment variable-based configuration management. It provides explicit, type-safe settings loading from environment variables with clear error messages and debugging capabilities.

## Development Commands

This project uses `just` as a task runner and `uv` for Python package management:

- `just` - List all available commands
- `just version` - Show current version
- `just bump-patch` - Bump patch version and create git tag
- `just bump-minor` - Bump minor version and create git tag  
- `just bump-major` - Bump major version and create git tag
- `just push-all` - Push commits and tags to remote
- `uv sync` - Install dependencies and sync lock file

## Architecture

The library consists of several key components:

### Core Classes

- `EnvConfigBase` (configbase.py:64): Base class for all configuration objects with `load_from_env()` method
- `SecretStr` (models.py:4): Wrapper for sensitive strings that masks values in logs and repr
- `Environments` (models.py:24): Enum for common environment types (DEV, STAGING, PROD)

### Field Types

- `env_field(env_var, default=...)` (fields.py:7): Maps dataclass field to environment variable
- `prefix_field(prefix)` (fields.py:15): Creates nested configuration with prefixed environment variables

### Key Features

- Type casting with support for bool, Literal, Optional/Union types
- Nested configuration objects with prefix support
- Comprehensive error messages showing all available environment variables
- Debug logging for fields using default values
- Pretty printing option for configuration validation

### Error Handling

- `MissingEnvVarError` (exceptions.py:4): Raised when required environment variable is missing
- `InvalidTypeError` (exceptions.py:12): Raised when type casting fails

## Package Structure

```
src/sane_settings/
├── __init__.py          # Public API exports
├── configbase.py        # EnvConfigBase class and loading logic
├── fields.py            # Field factory functions
├── models.py            # SecretStr and Environments
├── exceptions.py        # Custom exceptions
└── py.typed            # Type hints marker
```

## Usage Pattern

The library follows a dataclass-based pattern where configuration classes inherit from `EnvConfigBase` and use field decorators to map to environment variables with optional prefixes for nested structures.