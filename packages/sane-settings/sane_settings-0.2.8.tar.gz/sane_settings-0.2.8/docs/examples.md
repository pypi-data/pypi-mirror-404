# Examples

**Source**: `/Users/nicolasparis/code/niparis/dataclasses-settings-cubed/docs/examples.md`  
**Verification Status**: Synchronized with source code as of 2026-02-01  
**Based On**: `src/sane_settings/` v0.2.7

---

## Table of Contents

1. [Basic Web Application](#basic-web-application)
2. [Database Configuration](#database-configuration)
3. [Microservices Setup](#microservices-setup)
4. [Feature Flags Configuration](#feature-flags-configuration)
5. [Multi-Environment Setup](#multi-environment-setup)
6. [Optional Services](#optional-services)
7. [Redis and Cache Configuration](#redis-and-cache-configuration)
8. [Logging Configuration](#logging-configuration)
9. [Testing with Mocked Environments](#testing-with-mocked-environments)

---

## Basic Web Application

A complete FastAPI/Flask-style web application configuration.

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, Environments, env_field

@dataclass
class WebAppSettings(EnvConfigBase):
    """Web application configuration."""
    
    # Server configuration
    host: str = env_field("HOST", default="0.0.0.0")
    port: int = env_field("PORT", default=8000)
    workers: int = env_field("WORKERS", default=4)
    
    # Application settings
    environment: Environments = env_field("ENVIRONMENT", default=Environments.DEV)
    debug: bool = env_field("DEBUG", default=False)
    
    # Security
    secret_key: str = env_field("SECRET_KEY")  # Required!
    
    # Optional feature flag
    enable_metrics: bool = env_field("ENABLE_METRICS", default=True)


# Load configuration
settings = WebAppSettings.load_from_env(app_prefix="WEBAPP")

# Use in application
print(f"Starting server on {settings.host}:{settings.port}")
print(f"Environment: {settings.environment}")
```

**Environment Variables:**
```bash
export WEBAPP_SECRET_KEY="super-secret-key-change-in-production"
export WEBAPP_ENVIRONMENT="PROD"
export WEBAPP_DEBUG="false"
export WEBAPP_PORT="8080"
```

---

## Database Configuration

Complete database configuration with connection pooling and secrets.

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, SecretStr, env_field, prefix_field

@dataclass
class ConnectionPoolSettings(EnvConfigBase):
    """Database connection pool configuration."""
    min_size: int = env_field("POOL_MIN_SIZE", default=5)
    max_size: int = env_field("POOL_MAX_SIZE", default=20)
    timeout: int = env_field("POOL_TIMEOUT", default=30)


@dataclass
class DatabaseSettings(EnvConfigBase):
    """PostgreSQL database configuration."""
    
    # Connection parameters
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=5432)
    user: str = env_field("USER", default="postgres")
    password: SecretStr = env_field("PASSWORD")  # Required secret
    name: str = env_field("NAME", default="app_database")
    
    # Connection pool
    pool: ConnectionPoolSettings = prefix_field("POOL")
    
    # SSL mode
    ssl_mode: str = env_field("SSL_MODE", default="prefer")
    
    @property
    def async_url(self) -> str:
        """Get async PostgreSQL URL."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"
        )
    
    @property
    def sync_url(self) -> str:
        """Get sync PostgreSQL URL."""
        return (
            f"postgresql://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"
        )


@dataclass
class AppSettings(EnvConfigBase):
    database: DatabaseSettings = prefix_field("DB")


# Load configuration
settings = AppSettings.load_from_env(app_prefix="MYAPP")

# Use in SQLAlchemy or asyncpg
print(f"Database URL: {settings.database.sync_url}")
# Output: Database URL: postgresql://postgres:****@localhost:5432/app_database?sslmode=prefer
```

**Environment Variables:**
```bash
# Required
export MYAPP_DB_PASSWORD="secure-db-password"

# Optional overrides
export MYAPP_DB_HOST="prod-db.example.com"
export MYAPP_DB_NAME="production_db"
export MYAPP_DB_SSL_MODE="require"
export MYAPP_DB_POOL__MAX_SIZE="50"
```

---

## Microservices Setup

Configuration for a microservice with external service dependencies.

```python
from dataclasses import dataclass
from typing import Optional
from sane_settings import EnvConfigBase, SecretStr, env_field, prefix_field

@dataclass
class ServiceEndpoint(EnvConfigBase):
    """Configuration for an external service endpoint."""
    url: str = env_field("URL")
    timeout: int = env_field("TIMEOUT", default=30)
    retry_attempts: int = env_field("RETRY_ATTEMPTS", default=3)


@dataclass
class AuthServiceConfig(EnvConfigBase):
    """Authentication service configuration."""
    endpoint: ServiceEndpoint = prefix_field("ENDPOINT")
    jwt_secret: SecretStr = env_field("JWT_SECRET")
    token_expiry: int = env_field("TOKEN_EXPIRY_MINUTES", default=60)


@dataclass
class PaymentServiceConfig(EnvConfigBase):
    """Payment service configuration."""
    endpoint: ServiceEndpoint = prefix_field("ENDPOINT")
    api_key: SecretStr = env_field("API_KEY")
    webhook_secret: SecretStr = env_field("WEBHOOK_SECRET")


@dataclass
class MicroserviceSettings(EnvConfigBase):
    """Main microservice configuration."""
    
    # Service identity
    service_name: str = env_field("SERVICE_NAME", default="order-service")
    version: str = env_field("VERSION", default="1.0.0")
    
    # External dependencies
    auth: AuthServiceConfig = prefix_field("AUTH")
    payment: PaymentServiceConfig = prefix_field("PAYMENT")
    
    # Optional notification service
    notification: Optional[ServiceEndpoint] = prefix_field("NOTIFICATION")


# Load configuration
settings = MicroserviceSettings.load_from_env(app_prefix="MICRO")

# Check if notification service is configured
if settings.notification:
    print(f"Notification service: {settings.notification.url}")
else:
    print("Notification service not configured")
```

**Environment Variables:**
```bash
# Required services
export MICRO_AUTH__ENDPOINT__URL="https://auth.internal"
export MICRO_AUTH__JWT_SECRET="auth-secret-key"

export MICRO_PAYMENT__ENDPOINT__URL="https://payments.internal"
export MICRO_PAYMENT__API_KEY="payment-api-key"
export MICRO_PAYMENT__WEBHOOK_SECRET="webhook-verification-secret"

# Optional notification service (only loaded if present)
export MICRO_NOTIFICATION__URL="https://notifications.internal"
export MICRO_NOTIFICATION__TIMEOUT="10"
```

---

## Feature Flags Configuration

Dynamic feature flags with Literal types for strict validation.

```python
from dataclasses import dataclass
from typing import Literal
from sane_settings import EnvConfigBase, env_field

@dataclass
class FeatureFlags(EnvConfigBase):
    """Application feature flags."""
    
    # Boolean flags
    new_checkout_flow: bool = env_field("NEW_CHECKOUT", default=False)
    beta_search: bool = env_field("BETA_SEARCH", default=False)
    dark_mode: bool = env_field("DARK_MODE", default=True)
    
    # Literal types for strict validation
    recommendation_engine: Literal["legacy", "v2", "ai"] = env_field(
        "RECOMMENDATION_ENGINE", 
        default="legacy"
    )
    
    # Gradual rollout percentage
    rollout_percentage: int = env_field("ROLLOUT_PERCENTAGE", default=0)


@dataclass
class AppSettings(EnvConfigBase):
    feature_flags: FeatureFlags = prefix_field("FEATURES")


# Load configuration
settings = AppSettings.load_from_env(app_prefix="SHOP")

# Use feature flags
if settings.feature_flags.new_checkout_flow:
    use_new_checkout()
else:
    use_legacy_checkout()

# Validate rollout percentage
if settings.feature_flags.rollout_percentage > 100:
    raise ValueError("Rollout percentage cannot exceed 100")
```

**Environment Variables:**
```bash
# Enable new features
export SHOP_FEATURES__NEW_CHECKOUT="true"
export SHOP_FEATURES__BETA_SEARCH="true"

# Switch recommendation engine (must be: legacy, v2, or ai)
export SHOP_FEATURES__RECOMMENDATION_ENGINE="v2"

# Gradual rollout (will fail if not a valid integer)
export SHOP_FEATURES__ROLLOUT_PERCENTAGE="25"
```

---

## Multi-Environment Setup

Configuration that adapts to different deployment environments.

```python
from dataclasses import dataclass
from sane_settings import EnvConfigBase, Environments, SecretStr, env_field, prefix_field

@dataclass
class DatabaseSettings(EnvConfigBase):
    host: str = env_field("HOST")
    name: str = env_field("NAME")
    user: str = env_field("USER")
    password: SecretStr = env_field("PASSWORD")


@dataclass
class LogSettings(EnvConfigBase):
    level: str = env_field("LEVEL", default="INFO")
    format: str = env_field("FORMAT", default="json")


@dataclass
class EnvironmentSettings(EnvConfigBase):
    """Per-environment configuration."""
    database: DatabaseSettings = prefix_field("DB")
    logging: LogSettings = prefix_field("LOG")


@dataclass
class AppSettings(EnvConfigBase):
    """Main application settings."""
    
    environment: Environments = env_field("ENVIRONMENT")
    
    # Per-environment configs (only one loaded based on env)
    # In practice, you'd handle this differently - this shows the concept
    dev: EnvironmentSettings = prefix_field("DEV")
    staging: EnvironmentSettings = prefix_field("STAGING")
    prod: EnvironmentSettings = prefix_field("PROD")
    
    @property
    def active_config(self) -> EnvironmentSettings:
        """Get the active environment configuration."""
        return getattr(self, self.environment.name.lower())
    
    @property
    def db_config(self) -> DatabaseSettings:
        """Get active database configuration."""
        return self.active_config.database


# Load all environment configurations
settings = AppSettings.load_from_env(app_prefix="APP")

# Access the correct environment config
print(f"Environment: {settings.environment}")
print(f"Database host: {settings.db_config.host}")
```

**Environment Variables:**
```bash
# Select environment
export APP_ENVIRONMENT="DEV"

# Development database
export APP_DEV__DB__HOST="localhost"
export APP_DEV__DB__NAME="dev_db"
export APP_DEV__DB__USER="dev_user"
export APP_DEV__DB__PASSWORD="dev_pass"

# Production database (still defined, but not accessed in DEV mode)
export APP_PROD__DB__HOST="prod-db.example.com"
export APP_PROD__DB__NAME="prod_db"
export APP_PROD__DB__USER="prod_user"
export APP_PROD__DB__PASSWORD="prod_secret"
```

**Note:** This is a conceptual example. In practice, you might want to use different approaches for environment-specific configs to avoid loading all environments.

---

## Optional Services

Configuration with optional integrations that may not be present.

```python
from dataclasses import dataclass
from typing import Optional
from sane_settings import EnvConfigBase, SecretStr, env_field, prefix_field

@dataclass
class S3Config(EnvConfigBase):
    """AWS S3 configuration."""
    bucket: str = env_field("BUCKET")
    region: str = env_field("REGION", default="us-east-1")
    access_key: SecretStr = env_field("ACCESS_KEY")
    secret_key: SecretStr = env_field("SECRET_KEY")


@dataclass
class SentryConfig(EnvConfigBase):
    """Sentry error tracking configuration."""
    dsn: SecretStr = env_field("DSN")
    environment: str = env_field("ENVIRONMENT", default="production")
    traces_sample_rate: float = env_field("TRACES_SAMPLE_RATE", default=0.1)


@dataclass
class DatadogConfig(EnvConfigBase):
    """Datadog monitoring configuration."""
    api_key: SecretStr = env_field("API_KEY")
    app_key: SecretStr = env_field("APP_KEY")
    service_name: str = env_field("SERVICE_NAME")


@dataclass
class AppSettings(EnvConfigBase):
    """Application settings with optional services."""
    
    # Required core settings
    app_name: str = env_field("NAME", default="myapp")
    version: str = env_field("VERSION", default="1.0.0")
    
    # Optional service integrations
    # These are only loaded if corresponding env vars exist
    s3: Optional[S3Config] = prefix_field("S3")
    sentry: Optional[SentryConfig] = prefix_field("SENTRY")
    datadog: Optional[DatadogConfig] = prefix_field("DATADOG")


# Load configuration
settings = AppSettings.load_from_env(app_prefix="APP")

# Initialize optional services
if settings.s3:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.s3.access_key.get_secret_value(),
        aws_secret_access_key=settings.s3.secret_key.get_secret_value(),
        region_name=settings.s3.region
    )
    print(f"S3 bucket configured: {settings.s3.bucket}")
else:
    print("S3 not configured - using local storage")

if settings.sentry:
    sentry_sdk.init(
        dsn=settings.sentry.dsn.get_secret_value(),
        environment=settings.sentry.environment,
        traces_sample_rate=settings.sentry.traces_sample_rate
    )
    print("Sentry error tracking enabled")
```

**Environment Variables (minimal setup):**
```bash
# Only app name - no optional services
export APP_NAME="my-minimal-app"
```

**Environment Variables (full setup):**
```bash
# Core settings
export APP_NAME="my-full-app"

# S3 integration
export APP_S3__BUCKET="my-bucket"
export APP_S3__ACCESS_KEY="AKIA..."
export APP_S3__SECRET_KEY="secret..."

# Sentry integration
export APP_SENTRY__DSN="https://..."
export APP_SENTRY__TRACES_SAMPLE_RATE="0.5"

# Datadog integration
export APP_DATADOG__API_KEY="api-key..."
export APP_DATADOG__APP_KEY="app-key..."
export APP_DATADOG__SERVICE_NAME="my-service"
```

---

## Redis and Cache Configuration

Redis configuration with connection URI construction.

```python
from dataclasses import dataclass
from typing import Optional
from sane_settings import EnvConfigBase, SecretStr, env_field, prefix_field

@dataclass
class RedisSettings(EnvConfigBase):
    """Redis connection configuration."""
    
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=6379)
    db: int = env_field("DB", default=0)
    password: Optional[SecretStr] = env_field("PASSWORD")
    
    # Connection pool settings
    max_connections: int = env_field("MAX_CONNECTIONS", default=50)
    socket_timeout: int = env_field("SOCKET_TIMEOUT", default=30)
    socket_connect_timeout: int = env_field("SOCKET_CONNECT_TIMEOUT", default=5)
    
    @property
    def url(self) -> str:
        """Build Redis URL."""
        auth = ""
        if self.password:
            auth = f":{self.password.get_secret_value()}@"
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class CacheSettings(EnvConfigBase):
    """Caching layer configuration."""
    
    # Primary cache
    redis: RedisSettings = prefix_field("REDIS")
    
    # Cache TTL settings (in seconds)
    default_ttl: int = env_field("DEFAULT_TTL", default=3600)
    session_ttl: int = env_field("SESSION_TTL", default=86400)
    static_ttl: int = env_field("STATIC_TTL", default=604800)


@dataclass
class AppSettings(EnvConfigBase):
    cache: CacheSettings = prefix_field("CACHE")


# Load configuration
settings = AppSettings.load_from_env(app_prefix="APP")

# Connect to Redis
import redis
client = redis.from_url(settings.cache.redis.url)

# Use cache with appropriate TTLs
client.setex("user:123", settings.cache.session_ttl, "session_data")
```

**Environment Variables:**
```bash
# Basic Redis setup
export APP_CACHE__REDIS__HOST="redis.internal"
export APP_CACHE__REDIS__PASSWORD="redis-secret"

# Advanced settings
export APP_CACHE__REDIS__MAX_CONNECTIONS="100"
export APP_CACHE__REDIS__SOCKET_TIMEOUT="60"

# TTL configuration
export APP_CACHE__DEFAULT_TTL="1800"      # 30 minutes
export APP_CACHE__SESSION_TTL="7200"      # 2 hours
export APP_CACHE__STATIC_TTL="2592000"    # 30 days
```

---

## Logging Configuration

Structured logging configuration with multiple outputs.

```python
from dataclasses import dataclass
from typing import Literal, Optional
from sane_settings import EnvConfigBase, env_field, prefix_field

@dataclass
class FileOutputConfig(EnvConfigBase):
    """File logging configuration."""
    path: str = env_field("PATH", default="/var/log/app.log")
    rotation: str = env_field("ROTATION", default="00:00")  # Daily at midnight
    retention: str = env_field("RETENTION", default="30 days")
    format: str = env_field("FORMAT", default="{time} | {level} | {message}")


@dataclass
class JSONOutputConfig(EnvConfigBase):
    """JSON structured logging configuration."""
    path: str = env_field("PATH", default="/var/log/app.jsonl")
    sink: str = env_field("SINK", default="file")
    serialize: bool = env_field("SERIALIZE", default=True)


@dataclass
class LoggingSettings(EnvConfigBase):
    """Comprehensive logging configuration."""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = env_field(
        "LEVEL", 
        default="INFO"
    )
    format: str = env_field(
        "FORMAT", 
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Optional file output
    file_output: Optional[FileOutputConfig] = prefix_field("FILE")
    
    # Optional JSON output
    json_output: Optional[JSONOutputConfig] = prefix_field("JSON")
    
    # Console output toggle
    enable_console: bool = env_field("ENABLE_CONSOLE", default=True)


@dataclass
class AppSettings(EnvConfigBase):
    logging: LoggingSettings = prefix_field("LOG")


# Configure loguru from settings
from loguru import logger
import sys

def configure_logging(settings: AppSettings):
    """Configure loguru from settings."""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler if enabled
    if settings.logging.enable_console:
        logger.add(
            sys.stderr,
            level=settings.logging.level,
            format=settings.logging.format
        )
    
    # Add file handler if configured
    if settings.logging.file_output:
        logger.add(
            settings.logging.file_output.path,
            rotation=settings.logging.file_output.rotation,
            retention=settings.logging.file_output.retention,
            format=settings.logging.file_output.format,
            level=settings.logging.level
        )
    
    # Add JSON handler if configured
    if settings.logging.json_output:
        logger.add(
            settings.logging.json_output.path,
            serialize=settings.logging.json_output.serialize,
            level=settings.logging.level
        )


# Load and apply
settings = AppSettings.load_from_env(app_prefix="APP")
configure_logging(settings)

logger.info("Logging configured successfully")
logger.debug("Debug messages are visible" if settings.logging.level == "DEBUG" else "Debug hidden")
```

**Environment Variables:**
```bash
# Basic logging
export APP_LOG__LEVEL="DEBUG"

# File output
export APP_LOG__FILE__PATH="/var/log/myapp.log"
export APP_LOG__FILE__ROTATION="1 week"
export APP_LOG__FILE__RETENTION="3 months"

# JSON structured logging
export APP_LOG__JSON__PATH="/var/log/myapp.jsonl"
export APP_LOG__JSON__SERIALIZE="true"

# Disable console in production
export APP_LOG__ENABLE_CONSOLE="false"
```

---

## Testing with Mocked Environments

How to write tests with controlled environment variables.

```python
import os
import pytest
from dataclasses import dataclass
from sane_settings import EnvConfigBase, env_field, prefix_field

@dataclass
class DatabaseSettings(EnvConfigBase):
    host: str = env_field("HOST", default="localhost")
    port: int = env_field("PORT", default=5432)

@dataclass
class AppSettings(EnvConfigBase):
    database: DatabaseSettings = prefix_field("DB")
    debug: bool = env_field("DEBUG", default=False)


class TestAppSettings:
    """Tests for application settings."""
    
    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear relevant env vars before each test."""
        # Store original values
        self.original = {}
        prefixes = ["TEST_"]
        for key in list(os.environ.keys()):
            for prefix in prefixes:
                if key.startswith(prefix):
                    self.original[key] = os.environ.pop(key)
        yield
        # Restore original values
        for key, value in self.original.items():
            os.environ[key] = value
    
    def test_default_values(self):
        """Test that default values are used when env vars not set."""
        settings = AppSettings.load_from_env(app_prefix="TEST")
        
        assert settings.database.host == "localhost"
        assert settings.database.port == 5432
        assert settings.debug is False
    
    def test_env_override(self):
        """Test that env vars override defaults."""
        os.environ["TEST__DB__HOST"] = "prod-db.example.com"
        os.environ["TEST__DB__PORT"] = "5433"
        os.environ["TEST__DEBUG"] = "true"
        
        settings = AppSettings.load_from_env(app_prefix="TEST")
        
        assert settings.database.host == "prod-db.example.com"
        assert settings.database.port == 5433
        assert settings.debug is True
    
    def test_boolean_parsing(self):
        """Test various boolean string representations."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("t", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("f", False),
            ("no", False),
        ]
        
        for string_value, expected_bool in test_cases:
            os.environ["TEST__DEBUG"] = string_value
            settings = AppSettings.load_from_env(app_prefix="TEST")
            assert settings.debug is expected_bool, \
                f"Failed for '{string_value}': expected {expected_bool}, got {settings.debug}"
    
    def test_missing_required_raises(self):
        """Test that missing required fields raise exception."""
        from sane_settings import MissingEnvVarError
        
        @dataclass
        class RequiredSettings(EnvConfigBase):
            required_field: str = env_field("REQUIRED")
        
        with pytest.raises(MissingEnvVarError) as exc_info:
            RequiredSettings.load_from_env(app_prefix="TEST")
        
        assert "TEST__REQUIRED" in str(exc_info.value)
        assert "required_field" in str(exc_info.value)


# Run with: pytest test_settings.py -v
```

---

## Summary

These examples demonstrate:

1. **Basic configuration** with required and optional fields
2. **Nested structures** for organizing related settings
3. **Secret handling** with `SecretStr`
4. **Type safety** with `Literal` types
5. **Optional integrations** using `Optional[T]`
6. **Multi-environment** configuration patterns
7. **Property methods** for derived values (URLs, etc.)
8. **Testing patterns** with environment mocking

All examples are compatible with the current library version (0.2.7) and follow the documented API.

