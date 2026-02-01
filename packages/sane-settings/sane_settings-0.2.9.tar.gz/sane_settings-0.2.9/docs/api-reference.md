# API Reference

**Source**: `/Users/nicolasparis/code/niparis/dataclasses-settings-cubed/docs/api-reference.md`  
**Verification Status**: Synchronized with source code as of 2026-02-01  
**Based On**: `src/sane_settings/` v0.2.7

---

## Table of Contents

1. [Classes](#classes)
   - [EnvConfigBase](#envconfigbase)
   - [SecretStr](#secretstr)
   - [Environments](#environments)
2. [Functions](#functions)
   - [env_field()](#env_field)
   - [prefix_field()](#prefix_field)
3. [Exceptions](#exceptions)
   - [MissingEnvVarError](#missingenvvarerror)
   - [InvalidTypeError](#invalidtypeerror)

---

## Classes

### EnvConfigBase

**Source**: `configbase.py:65-150`

Base class for all configuration dataclasses. Provides the `load_from_env()` class method for loading configuration from environment variables.

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase

@dataclass
class MyConfig(EnvConfigBase):
    # ... fields ...
    pass
```

#### Methods

##### load_from_env()

```python
@classmethod
def load_from_env(
    cls: type[T],
    _prefix: str = "",
    _separator: str = "__",
    pretty_check: bool = False,
    app_prefix: str = "",
) -> T
```

Load configuration from environment variables and return an instance of the class.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `_prefix` | `str` | `""` | Internal prefix for nested loading (usually not set directly) |
| `_separator` | `str` | `"__"` | Separator between prefix components |
| `pretty_check` | `bool` | `False` | If True, prints the configuration object using `pprint` |
| `app_prefix` | `str` | `""` | Application prefix prepended to all environment variables |

**Returns:**
Instance of the configuration class with values loaded from environment variables.

**Raises:**
- `MissingEnvVarError` - When a required field's environment variable is not set
- `InvalidTypeError` - When type casting fails

**Example:**

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field

@dataclass
class DatabaseConfig(EnvConfigBase):
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=5432)

# Load with app prefix
config = DatabaseConfig.load_from_env(app_prefix="MYAPP")
# Looks for MYAPP__HOST and MYAPP__PORT
```

**Implementation Details:**
- Iterates over all dataclass fields (line 80)
- Handles nested prefix fields recursively (lines 82-119)
- Handles direct environment variable fields (lines 122-144)
- Uses `_cast_var()` helper for type casting (lines 133-143)

---

### SecretStr

**Source**: `models.py:4-22`

A wrapper class for sensitive string values that masks the actual value in string representations.

```python
from sane_settings import SecretStr

secret = SecretStr("my-secret-value")
print(secret)           # **********
print(repr(secret))     # SecretStr('**********')
print(secret.get_secret_value())  # my-secret-value
```

#### Constructor

```python
def __init__(self, value: str)
```

Create a new SecretStr instance.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | The secret value to wrap |

#### Methods

##### get_secret_value()

```python
def get_secret_value(self) -> str
```

Retrieve the actual secret value.

**Returns:**
The unmasked secret string.

**Example:**

```python
secret = SecretStr("password123")
actual = secret.get_secret_value()  # "password123"
```

#### Special Methods

##### __str__()

```python
def __str__(self) -> str
```

Returns a masked string representation: `**********`

**Source**: `models.py:15-16`

##### __repr__()

```python
def __repr__(self) -> str
```

Returns a masked repr representation: `SecretStr('**********')`

**Source**: `models.py:12-13`

##### __eq__()

```python
def __eq__(self, other) -> bool
```

Compare with another SecretStr or string value.

**Source**: `models.py:18-21`

**Example:**

```python
secret = SecretStr("value")
secret == "value"              # True
secret == SecretStr("value")   # True
secret == "other"              # False
```

#### Usage with env_field

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, SecretStr, env_field

@dataclass
class SecureConfig(EnvConfigBase):
    password: SecretStr = env_field("PASSWORD")
    api_key: SecretStr = env_field("API_KEY")

config = SecureConfig.load_from_env(app_prefix="APP")
# Values are automatically cast to SecretStr
```

---

### Environments

**Source**: `models.py:24-27`

A StrEnum defining common environment types.

```python
from sane_settings import Environments

print(Environments.DEV)      # "DEV"
print(Environments.STAGING)  # "STAGING"
print(Environments.PROD)     # "PROD"
```

#### Values

| Value | String |
|-------|--------|
| `Environments.DEV` | `"DEV"` |
| `Environments.STAGING` | `"STAGING"` |
| `Environments.PROD` | `"PROD"` |

#### Usage with env_field

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, Environments, env_field

@dataclass
class AppConfig(EnvConfigBase):
    environment: Environments = env_field("ENVIRONMENT", default=Environments.DEV)

config = AppConfig.load_from_env(app_prefix="APP")
# With APP__ENVIRONMENT=PROD
# config.environment == Environments.PROD
```

---

## Functions

### env_field()

**Source**: `fields.py:7-12`

Creates a dataclass field that loads its value from an environment variable.

```python
def env_field(env_var: str, *, default: Any = dataclasses.MISSING) -> Field
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `env_var` | `str` | (required) | The environment variable name (without prefix) |
| `default` | `Any` | `MISSING` | Optional default value if env var not set |

**Returns:**
A dataclass `Field` with metadata indicating it should be loaded from an environment variable.

**Raises:**
None directly. The field will cause `MissingEnvVarError` at load time if no default is provided and the env var is missing.

**Examples:**

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field

@dataclass
class Config(EnvConfigBase):
    # Required field - will fail if env var not set
    api_key: str = env_field("API_KEY")
    
    # Optional field with default
    timeout: int = env_field("TIMEOUT", default=30)
    
    # Optional field that can be None
    optional_val: str | None = env_field("OPTIONAL_VAL")
```

**Implementation Details:**
- Stores the env var name in field metadata under key `"env"` (line 9)
- Returns a dataclass field with appropriate default and metadata (lines 10-12)

---

### prefix_field()

**Source**: `fields.py:15-19`

Creates a dataclass field for nested configuration with a prefix.

```python
def prefix_field(prefix: str) -> Field
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prefix` | `str` | (required) | The prefix for nested environment variables |

**Returns:**
A dataclass `Field` with metadata indicating it represents a nested configuration.

**Examples:**

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field, prefix_field

@dataclass
class DatabaseConfig(EnvConfigBase):
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=5432)

@dataclass
class AppConfig(EnvConfigBase):
    database: DatabaseConfig = prefix_field("DB")

config = AppConfig.load_from_env(app_prefix="MYAPP")
# database.host loads from MYAPP__DB__HOST
```

**Implementation Details:**
- Stores the prefix in field metadata under key `"prefix"` (line 19)
- The loader uses this prefix to construct nested environment variable names

---

## Exceptions

### MissingEnvVarError

**Source**: `exceptions.py:4-9`

Raised when a required environment variable is not set.

```python
class MissingEnvVarError(Exception):
    def __init__(self, full_env_var_name: str, name: str)
```

**Constructor Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `full_env_var_name` | `str` | The full environment variable name that was expected |
| `name` | `str` | The attribute name in the dataclass |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `full_env_var_name` | `str` | The full environment variable name |
| `name` | `str` | The field/attribute name |

**Error Message Format:**

```
Required environment variable '{full_env_var_name}' is not set for attribute '{name}'.
Available environment variables:
  - PATH
  - HOME
  - USER
  - ...
```

**Example:**

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field, MissingEnvVarError

@dataclass
class Config(EnvConfigBase):
    required: str = env_field("REQUIRED")

try:
    config = Config.load_from_env(app_prefix="APP")
except MissingEnvVarError as e:
    print(f"Missing: {e.full_env_var_name}")  # APP__REQUIRED
    print(f"Field: {e.name}")                  # required
    print(e)  # Full message with all env vars
```

---

### InvalidTypeError

**Source**: `exceptions.py:12-13`

Raised when type casting of an environment variable value fails.

```python
class InvalidTypeError(Exception):
    pass
```

**Error Message Formats:**

**Boolean casting failure:**
```
Failed to cast env var '{full_env_var_name}' (value: '{raw_value}') to type bool for attribute '{name}'.
```

**Literal type failure:**
```
Failed to cast env var '{full_env_var_name}' (value: '{raw_value}') to Literal for attribute '{name}'. 
Allowed values are {value1},{value2},...
```

**General casting failure:**
```
Failed to cast env var '{full_env_var_name}' (value from env var: '{raw_value}') to type {type_name} 
for attribute '{name}'. | {original_exception_message}
```

**Union type error:**
```
'{name}' is invalid. Union type is only allowed for exactly 2 types, one of both being None
```

**Example:**

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field, InvalidTypeError

@dataclass
class Config(EnvConfigBase):
    port: int = env_field("PORT")

# With APP__PORT=not_a_number
try:
    config = Config.load_from_env(app_prefix="APP")
except InvalidTypeError as e:
    print(e)  # Shows the env var name, value, and field
```

---

## Module Exports

**Source**: `__init__.py`

The public API is exported via `__all__`:

```python
__all__ = [
    "SecretStr",
    "Environments",
    "EnvConfigBase",
    "env_field",
    "prefix_field"
]
```

Note: Exceptions (`MissingEnvVarError`, `InvalidTypeError`) are available but not in `__all__`. Import them explicitly:

```python
from sane_settings import MissingEnvVarError, InvalidTypeError
```

Or:

```python
from sane_settings.exceptions import MissingEnvVarError, InvalidTypeError
```

