# Architecture Guide

**Source**: `/Users/nicolasparis/code/niparis/dataclasses-settings-cubed/docs/architecture.md`  
**Verification Status**: Synchronized with source code as of 2026-02-01  
**Based On**: `src/sane_settings/` v0.2.7

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Core Components](#core-components)
3. [Loading Mechanism](#loading-mechanism)
4. [Type Casting System](#type-casting-system)
5. [Prefix Resolution](#prefix-resolution)
6. [Nested Configuration Loading](#nested-configuration-loading)
7. [Error Handling](#error-handling)
8. [Logging System](#logging-system)
9. [Design Decisions](#design-decisions)

---

## Project Structure

```
src/sane_settings/
├── __init__.py          # Public API exports
├── configbase.py        # EnvConfigBase class and loading logic (151 lines)
├── fields.py            # Field factory functions (23 lines)
├── models.py            # SecretStr and Environments (28 lines)
├── exceptions.py        # Custom exceptions (16 lines)
└── py.typed             # Type hints marker file
```

**Source**: `CLAUDE.md:51-59`

---

## Core Components

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Configuration                        │
│  @dataclass                                                  │
│  class Settings(EnvConfigBase):                              │
│      db: Database = prefix_field("DB")                       │
│      port: int = env_field("PORT", default=8080)            │
└───────────────────────┬─────────────────────────────────────┘
                        │ load_from_env(app_prefix="APP")
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  EnvConfigBase (configbase.py)               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  1. Iterate dataclass fields                            ││
│  │  2. Check metadata for "prefix" or "env"                ││
│  │  3. Resolve full env var name                           ││
│  │  4. Load from environment or use default                ││
│  │  5. Cast to target type via _cast_var()                 ││
│  └─────────────────────────────────────────────────────────┘│
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    fields    │ │  _cast_var   │ │  exceptions  │
│   (fields.py)│ │ (configbase) │ │(exceptions  │
│              │ │              │ │    .py)      │
│ env_field()  │ │ Type casting │ │ MissingEnvVar│
│ prefix_field()│ │   logic      │ │ InvalidType  │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Loading Mechanism

### Main Loading Flow

**Source**: `configbase.py:68-150` - `load_from_env()` method

```python
@classmethod
def load_from_env(
    cls: type[T],
    _prefix: str = "",
    _separator: str = "__",
    pretty_check: bool = False,
    app_prefix: str = "",
) -> T:
```

### Step-by-Step Loading Process

1. **Prefix Construction** (lines 76-78)
   ```python
   if app_prefix:
       _prefix = f"{app_prefix}{_separator}{_prefix}" if _prefix else app_prefix
   ```
   - Combines `app_prefix` with any existing `_prefix`
   - Example: `app_prefix="APP", _prefix="DB"` -> `"APP__DB"`

2. **Field Iteration** (line 80)
   ```python
   for f in dataclasses.fields(cls):
   ```
   - Iterates over all defined fields in the dataclass

3. **Prefix Field Handling** (lines 82-119)
   ```python
   nested_prefix = f.metadata.get("prefix")
   if nested_prefix:
       # Recursively load nested config
   ```
   - Detects fields created with `prefix_field()`
   - Constructs full prefix for nested loading
   - Handles Optional[NestedConfig] types

4. **Env Field Handling** (lines 122-144)
   ```python
   env_var_name_part = f.metadata.get("env")
   if env_var_name_part:
       # Load from environment variable
   ```
   - Detects fields created with `env_field()`
   - Constructs full env var name
   - Loads value from `os.getenv()`

5. **Value Resolution** (lines 131-144)
   - If env var exists: cast and use the value
   - If env var missing and has default: use default (with debug log)
   - If env var missing and no default: raise `MissingEnvVarError`

6. **Instance Creation** (line 146)
   ```python
   retval = cls(**config_kwargs)
   ```
   - Creates instance with resolved values

7. **Pretty Check** (lines 147-149)
   ```python
   if pretty_check:
       pprint(retval)
   ```
   - Optionally prints the configuration

---

## Type Casting System

### _cast_var() Function

**Source**: `configbase.py:16-62`

The type casting engine handles conversion from string (environment variable values) to Python types.

```python
def _cast_var(
    ftype: Any, name: str, raw_value: Any, config_kwargs: dict, full_env_var_name: str
):
```

### Supported Type Categories

#### 1. Boolean Types

**Source**: `configbase.py:20-32`

```python
if ftype is bool:
    if isinstance(raw_value, bool):
        config_kwargs[name] = raw_value
    else:
        match str(raw_value).lower():
            case "true" | "1" | "t" | "yes":
                config_kwargs[name] = True
            case "false" | "0" | "f" | "no":
                config_kwargs[name] = False
            case _:
                raise InvalidTypeError(...)
```

**Behavior:**
- Preserves actual boolean defaults (not re-cast)
- Accepts multiple string representations
- Case-insensitive matching

**Valid True Values:** `"true"`, `"1"`, `"t"`, `"yes"`
**Valid False Values:** `"false"`, `"0"`, `"f"`, `"no"`

#### 2. Literal Types

**Source**: `configbase.py:33-39`

```python
elif typing.get_origin(ftype) is typing.Literal:
    if raw_value in typing.get_args(ftype):
        config_kwargs[name] = raw_value
    else:
        raise InvalidTypeError(...)
```

Uses `typing.get_origin()` and `typing.get_args()` to validate against allowed values.

#### 3. Union/Optional Types

**Source**: `configbase.py:40-54`

```python
elif typing.get_origin(ftype) in (types.UnionType, typing.Union):
    union_types = typing.get_args(ftype)
    if len(union_types) == 2 and types.NoneType in union_types:
        if raw_value in ("None", "none", None):
            config_kwargs[name] = None
        else:
            non_none_type = next(t for t in union_types if t is not type(None))
            config_kwargs = _cast_var(non_none_type, ...)
    else:
        raise InvalidTypeError(...)
```

**Important:** Only supports `Optional[T]` (2-type union with None). Complex unions are rejected.

**Handles both syntaxes:**
- `Optional[T]` (typing.Union)
- `T | None` (types.UnionType, Python 3.10+)

#### 4. Simple Constructor Casting

**Source**: `configbase.py:55-60`

```python
else:
    config_kwargs[name] = ftype(raw_value)
```

For all other types, calls the type constructor with the raw value. This works for:
- `int("123")` -> 123
- `str("hello")` -> "hello"
- `SecretStr("secret")` -> SecretStr instance
- `Path("/tmp")` -> Path instance

#### 5. Error Handling

**Source**: `configbase.py:57-60`

```python
except (ValueError, TypeError) as exc:
    raise InvalidTypeError(
        f"Failed to cast env var '{full_env_var_name}' ... to type {ftype.__name__} ... | {str(exc)}"
    )
```

Converts Python casting errors into descriptive `InvalidTypeError`.

---

## Prefix Resolution

### Prefix Construction Algorithm

**Source**: `configbase.py:76-78, 85-89, 124-127`

```
Full Prefix Construction:
┌─────────────────┐     ┌──────────┐     ┌─────────────┐
│   app_prefix    │  +  │ _prefix  │  +  │ field name  │
│  (optional)     │     │(optional)│     │  or prefix  │
└─────────────────┘     └──────────┘     └─────────────┘
```

### Examples

| app_prefix | _prefix | field env | Result |
|------------|---------|-----------|--------|
| `"APP"` | `""` | `"KEY"` | `APP__KEY` |
| `"APP"` | `"DB"` | `"HOST"` | `APP__DB__HOST` |
| `""` | `""` | `"KEY"` | `KEY` |
| `""` | `"DB"` | `"HOST"` | `DB__HOST` |

### Nested Prefix Handling

For `prefix_field()`:

```python
full_prefix = (
    f"{_prefix}{_separator}{nested_prefix}"
    if _prefix
    else nested_prefix
)
```

**Example Flow:**

```
Settings.load_from_env(app_prefix="MYAPP")
  │
  ├─ database: DatabaseSettings = prefix_field("DB")
  │  │
  │  ├─ _prefix = "MYAPP"
  │  ├─ nested_prefix = "DB"
  │  ├─ full_prefix = "MYAPP__DB"
  │  │
  │  └─ DatabaseSettings.load_from_env(_prefix="MYAPP__DB")
  │     │
  │     ├─ host: str = env_field("HOST")
  │     │  └─ full_env = "MYAPP__DB__HOST"
  │     └─ port: int = env_field("PORT")
  │        └─ full_env = "MYAPP__DB__PORT"
  │
  └─ timeout: int = env_field("TIMEOUT")
     └─ full_env = "MYAPP__TIMEOUT"
```

---

## Nested Configuration Loading

### Recursive Loading

**Source**: `configbase.py:82-119`

```python
nested_prefix = f.metadata.get("prefix")
if nested_prefix:
    full_prefix = ...
    
    # Handle Optional[NestedConfig]
    if typing.get_origin(f.type) in (types.UnionType, typing.Union):
        # Check if any env vars with this prefix exist
        prefix_exists = any(
            key.startswith(full_prefix + _separator)
            for key in os.environ.keys()
        )
        if prefix_exists:
            config_kwargs[f.name] = non_none_type.load_from_env(...)
        else:
            config_kwargs[f.name] = None
    else:
        # Normal nested config
        config_kwargs[f.name] = f.type.load_from_env(
            _prefix=full_prefix, app_prefix=""
        )
```

### Optional Nested Config Detection

For `Optional[NestedConfig]`, the system checks if any environment variables exist with the expected prefix:

```python
prefix_exists = any(
    key.startswith(full_prefix + _separator)
    for key in os.environ.keys()
)
```

**Example:**

```python
@dataclass
class TracingConfig(EnvConfigBase):
    endpoint: str = env_field("ENDPOINT")

@dataclass
class AppConfig(EnvConfigBase):
    tracing: Optional[TracingConfig] = prefix_field("TRACING")

# If MYAPP__TRACING__ENDPOINT exists -> tracing = TracingConfig(...)
# If no MYAPP__TRACING__* vars exist -> tracing = None
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── MissingEnvVarError    # Required env var not found
└── InvalidTypeError      # Type casting failed
```

### MissingEnvVarError

**Source**: `exceptions.py:4-9`

```python
class MissingEnvVarError(Exception):
    def __init__(self, full_env_var_name: str, name: str):
        self.full_env_var_name = full_env_var_name
        self.name = name
        env_vars = "\nAvailable environment variables:\n" + \
                   "\n".join(f"  - {key}" for key in os.environ.keys())
        super().__init__(
            f"Required environment variable '{full_env_var_name}' is not set "
            f"for attribute '{name}'.\n{env_vars}"
        )
```

**Design Rationale:**
- Stores the env var name and field name as attributes for programmatic handling
- Includes all available environment variables in the message for debugging
- Helps catch typos by showing similar env vars

### InvalidTypeError

**Source**: `exceptions.py:12-13`

Simple exception class used as a marker for type casting failures. Detailed messages are constructed at the point of failure.

---

## Logging System

### Logger

Uses `loguru` for structured logging.

**Source**: `configbase.py:9`

```python
from loguru import logger
```

### Log Events

#### 1. Default Value Used

**Source**: `configbase.py:136-138`

```python
logger.debug(
    f"field {f.name} loading from {full_env_var_name} used its default value"
)
```

**Purpose:** Helps identify when a default is being used, which may indicate a missing or misspelled environment variable.

#### 2. None Value Detected

**Source**: `configbase.py:44`

```python
logger.debug(f"field {name} detected as none")
```

**Purpose:** Tracks when an optional field is explicitly set to None via the "None" string.

---

## Design Decisions

### 1. Dataclass-Based Approach

**Decision:** Build on Python's `dataclasses` module.

**Rationale:**
- Type hints are natural and already familiar to Python developers
- Automatic `__init__`, `__repr__`, `__eq__` generation
- IDE support and type checking work out of the box
- No custom class definition DSL needed

### 2. Explicit Over Implicit

**Decision:** Fail fast when required configuration is missing.

**Rationale:**
- Missing configuration is a common source of production issues
- Silent defaults can hide typos in environment variable names
- Clear error messages reduce debugging time

**Contrast with other libraries:**
- Many libraries silently use defaults
- sane-settings logs when defaults are used (debug level)

### 3. Environment Variables Only

**Decision:** Only support environment variables, not config files.

**Rationale:** (from README.md)
- 12-factor app methodology
- Environment variables are the standard for containerized applications
- No file parsing complexity
- No file path configuration needed

**Source**: `README.md:14-16` - Non Goals section

### 4. Double Underscore Separator

**Decision:** Use `__` as the default separator.

**Rationale:**
- Single underscore is common in variable names
- Double underscore is visually distinct and unlikely to conflict
- Similar to Django's environment variable convention
- Still shell-friendly (unlike dots or colons)

### 5. Union Type Limitation

**Decision:** Only support `Optional[T]` (2-type unions with None).

**Rationale:**
- Complex unions are ambiguous for environment variable parsing
- `Union[int, str]` - which type should be tried first?
- Keeps the type system predictable
- Covers the most common use case (optional values)

### 6. SecretStr Wrapper

**Decision:** Use a wrapper class instead of field metadata.

**Rationale:**
- Explicit type indicates "this is sensitive" in the code
- Prevents accidental logging at the type level
- Works with mypy and type checkers
- `get_secret_value()` makes access explicit

### 7. Debug Logging Over Validation

**Decision:** Log when defaults are used instead of validation warnings.

**Rationale:**
- Environment variable presence varies by environment
- Debug logs can be enabled when needed
- Non-blocking - doesn't prevent startup
- Can be aggregated across deployments

---

## Future Considerations

### Potential Extensions

1. **List/Collection Support**
   - Parse comma-separated values into lists
   - Support `list[int]`, `list[str]`, etc.

2. **Custom Parsers**
   - Allow field-level custom parsing functions
   - `env_field("DATA", parser=custom_parser)`

3. **Validation**
   - Post-load validation hooks
   - Cross-field validation

4. **Documentation Generation**
   - Auto-generate documentation from config classes
   - List all required/optional env vars

### Maintained Constraints

These design decisions are unlikely to change:

1. Environment variables only (no config files)
2. Dataclass-based
3. Explicit failure on missing required values
4. No complex Union types
5. Type-safe by default

