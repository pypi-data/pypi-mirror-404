# Sane Settings

Simply Sane Settings

Born of the desire of having app config behaving in an explicit way, to zero in and fix missing config very quickly

## Design Goals

- Having an extremely explicit settings library that minimise the time spent fighting with settings
- For attributes without defaults, if SaneSettings does not find a env var, it will fail loading and tell you EXACTLY what env var it was expecting.
- Any attributes with default that does NOT get replaced with an env var will be highlighted in logs (use DEBUG log level) which helps you quickly find typos in your Env Vars
- Only supports environment variables to override the defaults 

## Non goals

- Loading from config files



## Getting started

```bash
pip install sane_settings
```


```python
from sane_settings import (
    EnvConfigBase,
    env_field,
    prefix_field,
)


@dataclass
class DatabaseSettings(EnvConfigBase):
    """Database connection settings."""

    # Database connection parameters
    host: str = env_field("HOST", default="localhost")      # Database host
    port: int = env_field("PORT", default=5432)             # Database port
    user: str = env_field("USER", default="postgres")       # Database user
    password: str = env_field("PASSWORD", default="postgres")  # Database password



@dataclass
class Settings(EnvConfigBase):
    """Main application settings."""

    # Nested Settings objects
    database: DatabaseSettings = prefix_field("DB")     # Any nested attribute will be EXAMPLE__DB__{attribute}
    # defaults at the end
    SERVICE_NAME: str = "my-service"


settings = Settings.load_from_env(app_prefix="EXAMPLE", pretty_check=True)
```

## Example


```python
from sane_settings import (
    EnvConfigBase,
    Environments,
    SecretStr,
    env_field,
    prefix_field,
)


@dataclass
class DatabaseSettings(EnvConfigBase):
    """Database connection settings."""

    # Database connection parameters
    host: str = env_field("HOST", default="localhost")                # APP_DB_HOST
    port: int = env_field("PORT", default=5432)                       # APP_DB_PORT
    user: str = env_field("USER", default="postgres")                 # APP_DB_USER
    password: SecretStr = env_field("PASSWORD", default="postgres")   # APP_DB_PASSWORD, will NOT show in logs unless you use DatabaseSettings().password.get_secret_value()
    name: str = env_field("NAME", default="queue_service")            # APP_DB_NAME

    @property
    def uri(self) -> str:
        """Get the PostgreSQL connection URI."""
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}?sslmode=allow"


@dataclass
class Settings(EnvConfigBase):
    """Main application settings."""

    # Nested Settings objects
    database: DatabaseSettings = prefix_field("DB")     # Any nested attribute will use APP_DB_{atribute}
    
    # Basic settings
    TRACING_BACKEND: TracingBackends | None = env_field("TRACING_BACKEND")
    ENVIRONMENT: Environments = env_field("ENVIRONMENT")                    # a default enum for your environments


    # defaults at the end
    SERVICE_NAME: str = "my-service"


settings = Settings.load_from_env(app_prefix="APP", pretty_check=True)
```



## DEv

### Release

(https://github.com/alltuner/uv-version-bumper)
just bump-patch|minor|major
just push-all

uv run pytest -v
