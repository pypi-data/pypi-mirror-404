# User Guide

**Source**: `/Users/nicolasparis/code/niparis/dataclasses-settings-cubed/docs/user-guide.md`  
**Verification Status**: Synchronized with source code as of 2026-02-01  
**Based On**: `src/sane_settings/` v0.2.7

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Configuration](#basic-configuration)
3. [Environment Variable Naming](#environment-variable-naming)
4. [Type Casting](#type-casting)
5. [Nested Configuration](#nested-configuration)
6. [Optional Fields](#optional-fields)
7. [Secret Handling](#secret-handling)
8. [Error Messages](#error-messages)
9. [Debug Logging](#debug-logging)
10. [Best Practices](#best-practices)

---

## Getting Started

### Installation

```bash
pip install sane-settings
```

### Your First Configuration

Create a simple configuration class:

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field

@dataclass
class Settings(EnvConfigBase):
    # Required field - will fail if MYAPP_API_KEY is not set
    api_key: str = env_field("API_KEY")
    
    # Optional field with default
    timeout: int = env_field("TIMEOUT", default=30)

# Load from environment
settings = Settings.load_from_env(app_prefix="MYAPP")
```

**Source Reference**: `configbase.py:68-74` - `load_from_env()` method signature

---

## Basic Configuration

### Required Fields

Fields without defaults are required. The library will raise an error if the environment variable is not set:

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field, MissingEnvVarError

@dataclass
class RequiredSettings(EnvConfigBase):
    database_url: str = env_field("DATABASE_URL")  # Required!

try:
    settings = RequiredSettings.load_from_env(app_prefix="APP")
except MissingEnvVarError as e:
    # Error message includes the exact env var name and all available env vars
    print(e)
    # Output: Required environment variable 'APP__DATABASE_URL' is not set 
    #         for attribute 'database_url'.
    #         Available environment variables:
    #           - PATH
    #           - HOME
    #           - ...
```

### Fields with Defaults

Fields with defaults are optional. If the environment variable is not set, the default value is used:

```python
@dataclass
class OptionalSettings(EnvConfigBase):
    port: int = env_field("PORT", default=8080)
    debug: bool = env_field("DEBUG", default=False)

settings = OptionalSettings.load_from_env(app_prefix="APP")
# If APP__PORT and APP__DEBUG are not set:
# - port = 8080
# - debug = False
```

**Behavior**: When a default is used, a debug log message is emitted:
```
DEBUG:sane_settings:field port loading from APP__PORT used its default value
```

**Source Reference**: `configbase.py:131-138` - Default value handling with debug logging

---

## Environment Variable Naming

### App Prefix

The `app_prefix` parameter prepends a prefix to all environment variables:

```python
settings = Settings.load_from_env(app_prefix="MYAPP")
# env_field("API_KEY") -> looks for MYAPP__API_KEY
```

### Separator

The default separator is `__` (double underscore). You can customize it:

```python
settings = Settings.load_from_env(
    app_prefix="MYAPP",
    _separator="_"
)
# env_field("API_KEY") -> looks for MYAPP_API_KEY
```

**Source Reference**: `configbase.py:71` - Separator parameter

### Full Naming Convention

| Component | Example | Result |
|-----------|---------|--------|
| app_prefix | "MYAPP" | `MYAPP` |
| separator | "__" | `__` |
| field env name | "API_KEY" | `API_KEY` |
| **Full name** | - | `MYAPP__API_KEY` |

With nested prefixes:

```python
@dataclass
class Settings(EnvConfigBase):
    database: DatabaseSettings = prefix_field("DB")

settings = Settings.load_from_env(app_prefix="MYAPP")
# DatabaseSettings.host = env_field("HOST")
# Result: MYAPP__DB__HOST
```

---

## Type Casting

The library automatically casts environment variable strings to the declared type.

### Supported Types

**Source Reference**: `configbase.py:16-62` - `_cast_var()` function

#### Boolean

Booleans accept multiple string representations:

| Input Value | Result |
|-------------|--------|
| "true", "1", "t", "yes" | `True` |
| "false", "0", "f", "no" | `False` |

```python
@dataclass
class BoolSettings(EnvConfigBase):
    enabled: bool = env_field("ENABLED", default=False)

# With MYAPP__ENABLED=true
settings = BoolSettings.load_from_env(app_prefix="MYAPP")
print(settings.enabled)  # True
```

**Important**: Boolean default values are preserved when the env var is not set.

**Source Reference**: `tests/test_bool_default_fix.py` - Boolean default handling tests

#### Integer

```python
@dataclass
class IntSettings(EnvConfigBase):
    port: int = env_field("PORT", default=8080)
    retries: int = env_field("RETRIES", default=3)

# With MYAPP__PORT=3000
settings = IntSettings.load_from_env(app_prefix="MYAPP")
print(settings.port)  # 3000 (integer, not string)
```

#### String

Strings are the base type - no casting needed:

```python
@dataclass
class StrSettings(EnvConfigBase):
    name: str = env_field("NAME", default="default")
```

#### Literal Types

Restrict values to specific options:

```python
from typing import Literal

@dataclass
class LiteralSettings(EnvConfigBase):
    log_level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = env_field("LOG_LEVEL", default="INFO")

# With MYAPP__LOG_LEVEL=DEBUG -> works
# With MYAPP__LOG_LEVEL=INVALID -> raises InvalidTypeError
```

**Source Reference**: `configbase.py:33-39` - Literal type handling

### Custom Types

Any type with a callable constructor works:

```python
from pathlib import Path

@dataclass
class PathSettings(EnvConfigBase):
    data_dir: Path = env_field("DATA_DIR", default=Path("/tmp"))

# With MYAPP__DATA_DIR=/var/lib/app
settings = PathSettings.load_from_env(app_prefix="MYAPP")
print(settings.data_dir)  # Path('/var/lib/app')
```

---

## Nested Configuration

Use `prefix_field()` to create nested configuration objects with prefixed environment variables.

### Basic Nesting

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field, prefix_field

@dataclass
class DatabaseSettings(EnvConfigBase):
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=5432)
    name: str = env_field("NAME", default="mydb")

@dataclass
class CacheSettings(EnvConfigBase):
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=6379)

@dataclass
class AppSettings(EnvConfigBase):
    database: DatabaseSettings = prefix_field("DB")
    cache: CacheSettings = prefix_field("CACHE")
    app_name: str = env_field("NAME", default="myapp")

settings = AppSettings.load_from_env(app_prefix="MYAPP")
```

**Environment Variables:**
- `MYAPP__DB__HOST` -> `settings.database.host`
- `MYAPP__DB__PORT` -> `settings.database.port`
- `MYAPP__CACHE__HOST` -> `settings.cache.host`
- `MYAPP__NAME` -> `settings.app_name`

**Source Reference**: `configbase.py:81-119` - Nested prefix handling

### Deep Nesting

Nesting can go multiple levels deep:

```python
@dataclass
class ConnectionPoolSettings(EnvConfigBase):
    max_size: int = env_field("MAX_SIZE", default=10)
    timeout: int = env_field("TIMEOUT", default=30)

@dataclass
class DatabaseSettings(EnvConfigBase):
    pool: ConnectionPoolSettings = prefix_field("POOL")
    host: str = env_field("HOST", default="localhost")

@dataclass
class AppSettings(EnvConfigBase):
    database: DatabaseSettings = prefix_field("DB")

# Results in:
# MYAPP__DB__POOL__MAX_SIZE
# MYAPP__DB__POOL__TIMEOUT
# MYAPP__DB__HOST
```

---

## Optional Fields

Use `Optional[T]` or `T | None` for fields that may not be configured.

### Optional with None

```python
from typing import Optional

@dataclass
class OptionalSettings(EnvConfigBase):
    # Optional - will be None if env var not set
    tracing_backend: Optional[str] = env_field("TRACING_BACKEND")

settings = OptionalSettings.load_from_env(app_prefix="MYAPP")
# If MYAPP__TRACING_BACKEND is not set:
# settings.tracing_backend = None
```

### Optional Nested Config

```python
from typing import Optional

@dataclass
class TracingSettings(EnvConfigBase):
    endpoint: str = env_field("ENDPOINT")
    sample_rate: float = env_field("SAMPLE_RATE", default=0.1)

@dataclass
class AppSettings(EnvConfigBase):
    # Optional nested config - only loaded if env vars with prefix exist
    tracing: Optional[TracingSettings] = prefix_field("TRACING")

settings = AppSettings.load_from_env(app_prefix="MYAPP")
# If no MYAPP__TRACING__* env vars exist:
# settings.tracing = None
# If MYAPP__TRACING__ENDPOINT is set:
# settings.tracing = TracingSettings(...)
```

**Source Reference**: `configbase.py:92-113` - Optional nested config detection

### Setting to None Explicitly

To explicitly set an optional field to None, use the string "None" or "none":

```python
# With MYAPP__TRACING_BACKEND=None
settings = OptionalSettings.load_from_env(app_prefix="MYAPP")
print(settings.tracing_backend)  # None
```

**Source Reference**: `configbase.py:43-45` - None value handling

---

## Secret Handling

Use `SecretStr` to prevent secrets from appearing in logs or string representations.

### Basic Usage

```python
from sane_settings import SecretStr

@dataclass
class SecretSettings(EnvConfigBase):
    password: SecretStr = env_field("PASSWORD")
    api_key: SecretStr = env_field("API_KEY")

settings = SecretSettings.load_from_env(app_prefix="APP")

# Masked in repr/str
print(settings.password)           # **********
print(repr(settings.password))     # SecretStr('**********')

# Access actual value
print(settings.password.get_secret_value())  # actual_secret_value
```

**Source Reference**: `models.py:4-22` - `SecretStr` implementation

### Comparison

`SecretStr` can be compared with strings:

```python
settings.password == "actual_password"  # True
settings.password == SecretStr("actual_password")  # True
```

**Source Reference**: `models.py:18-21` - `__eq__` implementation

---

## Error Messages

### MissingEnvVarError

Raised when a required environment variable is not set.

**Source Reference**: `exceptions.py:4-9`

```python
from sane_settings import MissingEnvVarError

@dataclass
class RequiredSettings(EnvConfigBase):
    required_val: str = env_field("REQUIRED")

try:
    settings = RequiredSettings.load_from_env(app_prefix="APP")
except MissingEnvVarError as e:
    print(e.full_env_var_name)  # APP__REQUIRED
    print(e.name)               # required_val
    # Full message includes all available environment variables for debugging
```

### InvalidTypeError

Raised when type casting fails.

**Source Reference**: `exceptions.py:12-13`

```python
from sane_settings import InvalidTypeError

@dataclass
class IntSettings(EnvConfigBase):
    port: int = env_field("PORT")  # Required int

# With APP__PORT=not_a_number
try:
    settings = IntSettings.load_from_env(app_prefix="APP")
except InvalidTypeError as e:
    # Message shows the env var name, value, target type, and field name
    print(e)
    # Failed to cast env var 'APP__PORT' (value from env var: 'not_a_number') 
    # to type int for attribute 'port'. | ...
```

---

## Debug Logging

The library uses `loguru` for debug logging.

### Enabled by Default

Set the log level to see debug messages:

```python
from loguru import logger
import sys

logger.add(sys.stderr, level="DEBUG")

settings = Settings.load_from_env(app_prefix="MYAPP")
# DEBUG:sane_settings:field port loading from MYAPP__PORT used its default value
```

### What Gets Logged

| Event | Level | Message |
|-------|-------|---------|
| Default value used | DEBUG | `field {name} loading from {env_var} used its default value` |
| None value detected | DEBUG | `field {name} detected as none` |

**Source Reference**: 
- `configbase.py:136-138` - Default used logging
- `configbase.py:44` - None detected logging

---

## Best Practices

### 1. Always Use app_prefix

Always provide an `app_prefix` to avoid collisions with system environment variables:

```python
# Good
settings = Settings.load_from_env(app_prefix="MYAPP")

# Bad - may conflict with system vars
settings = Settings.load_from_env()
```

### 2. Group Related Settings

Use nested configs to organize related settings:

```python
@dataclass
class AppSettings(EnvConfigBase):
    database: DatabaseSettings = prefix_field("DB")
    cache: CacheSettings = prefix_field("CACHE")
    queue: QueueSettings = prefix_field("QUEUE")
```

### 3. Use SecretStr for Sensitive Data

Always use `SecretStr` for passwords, API keys, tokens:

```python
@dataclass
class SecureSettings(EnvConfigBase):
    api_key: SecretStr = env_field("API_KEY")
    db_password: SecretStr = env_field("DB_PASSWORD")
```

### 4. Fail Fast in Production

Don't provide defaults for critical settings:

```python
@dataclass
class ProductionSettings(EnvConfigBase):
    # These must be explicitly set - no defaults
    database_url: SecretStr = env_field("DATABASE_URL")
    secret_key: SecretStr = env_field("SECRET_KEY")
    
    # These have sensible defaults
    workers: int = env_field("WORKERS", default=4)
    timeout: int = env_field("TIMEOUT", default=30)
```

### 5. Use Environments Enum

Use the built-in `Environments` enum for environment detection:

```python
from sane_settings import Environments

@dataclass
class Settings(EnvConfigBase):
    environment: Environments = env_field("ENVIRONMENT", default=Environments.DEV)

settings = Settings.load_from_env(app_prefix="APP")
if settings.environment == Environments.PROD:
    # Production-specific logic
    pass
```

**Source Reference**: `models.py:24-27` - `Environments` enum

### 6. Use pretty_check During Development

Enable pretty printing to verify your configuration:

```python
settings = Settings.load_from_env(
    app_prefix="MYAPP",
    pretty_check=True  # Prints the config object
)
```

**Source Reference**: `configbase.py:72` - `pretty_check` parameter

### 7. Handle Errors Gracefully

```python
from sane_settings import MissingEnvVarError, InvalidTypeError

def load_settings():
    try:
        return Settings.load_from_env(app_prefix="MYAPP")
    except MissingEnvVarError as e:
        logger.error(f"Missing required configuration: {e.full_env_var_name}")
        raise SystemExit(1)
    except InvalidTypeError as e:
        logger.error(f"Invalid configuration value: {e}")
        raise SystemExit(1)
```

