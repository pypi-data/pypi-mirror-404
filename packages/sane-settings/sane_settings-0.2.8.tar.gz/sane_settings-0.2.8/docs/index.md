# Sane Settings Documentation

**Source**: `/Users/nicolasparis/code/niparis/dataclasses-settings-cubed/docs/index.md`  
**Verification Status**: Synchronized with source code as of 2026-02-01  
**Package Version**: 0.2.7

---

## Overview

Sane Settings is a Python library for environment variable-based configuration management that prioritizes **explicit behavior** and **clear error messages**. It helps you catch configuration errors immediately with zero ambiguity.

### Key Principles

1. **Explicit is better than implicit** - Never silently use defaults when you meant to configure something
2. **Fail fast with clarity** - Missing env vars show you exactly what was expected
3. **Debuggability** - Debug logs highlight when defaults are used, helping catch typos
4. **Security** - Secret values are masked in logs automatically

### Quick Example

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field, prefix_field, SecretStr

@dataclass
class DatabaseSettings(EnvConfigBase):
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=5432)
    password: SecretStr = env_field("PASSWORD")  # Required - will fail if missing

@dataclass
class AppSettings(EnvConfigBase):
    database: DatabaseSettings = prefix_field("DB")
    debug: bool = env_field("DEBUG", default=False)

# Load from environment
settings = AppSettings.load_from_env(app_prefix="MYAPP")

# Access nested settings
print(settings.database.host)  # Uses MYAPP_DB_HOST
print(settings.password)       # SecretStr('**********')
```

---

## Documentation Sections

| Document | Purpose |
|----------|---------|
| [User Guide](./user-guide.md) | Getting started, configuration patterns, type casting, best practices |
| [API Reference](./api-reference.md) | Complete reference for all public classes and functions |
| [Architecture Guide](./architecture.md) | How the library works internally, type system, loading mechanism |
| [Examples](./examples.md) | Real-world usage patterns for common scenarios |

---

## Installation

```bash
pip install sane-settings
```

Requires Python 3.10 or higher.

---

## Documentation Principles

This documentation follows these principles:

1. **Truth over completeness** - All code examples are tested against the actual library implementation
2. **Evidence-aware** - Implementation details reference specific source files and line numbers
3. **Verification metadata** - Each document includes version information and verification status

