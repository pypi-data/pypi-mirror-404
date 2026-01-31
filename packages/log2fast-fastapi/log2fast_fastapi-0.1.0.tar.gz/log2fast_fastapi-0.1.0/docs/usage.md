# log2fast_fastapi Usage Guide

Professional logging module for FastAPI applications with environment-aware configuration, structured logging, and file rotation.

## Features

- **Environment-Based Configuration**: Automatic configuration for development, production, testing, and debug environments
- **Multiple Output Formats**: JSON (production), Colored (development), Structured (debugging), Simple (testing)
- **Module-Based Loggers**: Each module can have its own logger instance
- **File Rotation**: Automatic log file rotation with configurable size and backup count
- **FastAPI Integration**: Middleware for automatic request/response logging with unique request IDs
- **Context Injection**: Support for request_id, user_id, and custom context data

---

## Quick Start

### 1. Basic Usage

```python
from log2fast_fastapi import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log messages at different levels
logger.debug("Debugging information")
logger.info("Application started successfully")
logger.warning("This is a warning")
logger.error("An error occurred")
logger.critical("Critical system failure")
```

### 2. Logging with Context

```python
from log2fast_fastapi import get_logger

logger = get_logger(__name__)

# Add extra context to your logs
logger.info(
    "User logged in",
    extra_data={
        "user_id": "12345",
        "ip_address": "192.168.1.1",
        "login_method": "oauth2"
    }
)
```

### 3. Exception Logging

```python
from log2fast_fastapi import get_logger

logger = get_logger(__name__)

try:
    result = 10 / 0
except Exception as e:
    # Automatically includes traceback
    logger.exception("Division error occurred", extra_data={"operation": "division"})
```

---

## Environment Configuration

**The easiest way to configure logging is to just set the environment in your `.env` file:**

```bash
# That's it! Format and level auto-configure based on environment
LOG_ENVIRONMENT=production
```

### Auto-Configuration (Recommended)

When you only set `LOG_ENVIRONMENT`, the module automatically configures:

| Environment | Auto Level | Auto Format | Use Case |
|------------|-----------|-------------|----------|
| `development` | INFO | colored | Local development |
| `production` | WARNING | json | Production servers |
| `testing` | INFO | simple | Automated tests |
| `debug` | DEBUG | colored | Troubleshooting |

### Full Configuration Options (Optional)

You can override the auto-configuration if needed:

```bash
# Environment (required - determines auto-config)
LOG_ENVIRONMENT=development

# Optional overrides (leave blank for auto-config)
LOG_LEVEL=DEBUG              # Override auto level
LOG_FORMAT=json              # Override auto format

# Console output
LOG_CONSOLE_ENABLED=true

# File logging
LOG_FILE_SETTINGS__ENABLED=true
LOG_FILE_SETTINGS__DIRECTORY=logs
LOG_FILE_SETTINGS__MAX_BYTES=10485760  # 10MB
LOG_FILE_SETTINGS__BACKUP_COUNT=5
LOG_FILE_SETTINGS__FILENAME_PATTERN={module}_{environment}.log

# Request logging
LOG_LOG_REQUESTS=true
LOG_LOG_REQUEST_BODY=false
LOG_LOG_RESPONSE_BODY=false

# Module name (optional)
LOG_MODULE_NAME=my_app
```

---

## Environment-Specific Logging

**Prevent sensitive data from being logged in the wrong environment!**

Use the `only_in` parameter to specify which environments should log a message:

```python
from log2fast_fastapi import get_logger

logger = get_logger(__name__)

# Logs in ALL environments
logger.info("User logged in", extra_data={"user_id": "12345"})

# Logs ONLY in development and debug (NOT in production)
logger.debug(
    "Sensitive debug info",
    extra_data={
        "password_hash": "bcrypt$2b$12$...",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    },
    only_in=["development", "debug"]
)

# Logs ONLY in production (for monitoring)
logger.warning(
    "High memory usage",
    extra_data={"memory_percent": 85},
    only_in=["production"]
)

# Logs in dev and testing (NOT in production)
logger.info(
    "Database query details",
    extra_data={"query": "SELECT * FROM users", "time_ms": 45},
    only_in=["development", "testing", "debug"]
)
```

### Common Use Cases

**1. Sensitive Data (passwords, tokens, PII)**
```python
# ❌ Bad - logs everywhere including production
logger.debug(f"Token: {access_token}")

# ✅ Good - only logs in dev/debug
logger.debug(
    "Token generated",
    extra_data={"token": access_token},
    only_in=["development", "debug"]
)
```

**2. Detailed Query Information**
```python
# Only show SQL queries in development
logger.info(
    "Database query executed",
    extra_data={"sql": query, "params": params},
    only_in=["development", "testing"]
)
```

**3. Production Monitoring**
```python
# Only log metrics in production
logger.info(
    "Performance metrics",
    extra_data={"response_time": 120, "memory_mb": 512},
    only_in=["production"]
)
```

---

## FastAPI Integration

### Add Request Logging Middleware

```python
from fastapi import FastAPI
from log2fast_fastapi import RequestLoggingMiddleware, get_logger

app = FastAPI()

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

logger = get_logger(__name__)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    logger.info(f"Fetching user", extra_data={"user_id": user_id})
    # Your logic here
    return {"user_id": user_id}
```

### Access Request ID

```python
from log2fast_fastapi import get_logger, get_request_id

logger = get_logger(__name__)

@app.get("/process")
async def process_data():
    request_id = get_request_id()
    logger.info(f"Processing data for request {request_id}")
    return {"request_id": request_id}
```

---

## Advanced Usage

### Custom Configuration

```python
from log2fast_fastapi import get_logger, LogSettings, LogEnvironment, LogFormat, LogLevel

# Create custom settings
custom_settings = LogSettings(
    log_environment=LogEnvironment.PRODUCTION,
    log_level=LogLevel.WARNING,
    log_format=LogFormat.JSON,
    console_enabled=True,
    module_name="custom_module"
)

# Get logger with custom settings
logger = get_logger(__name__, config=custom_settings)
```

### Reconfigure at Runtime

```python
from log2fast_fastapi import FastLogger, LogSettings, LogEnvironment

# Create new settings
new_settings = LogSettings(
    log_environment=LogEnvironment.DEBUG,
    log_level=LogLevel.DEBUG
)

# Reconfigure all loggers
FastLogger.reconfigure(new_settings)
```

### Module-Specific Loggers

```python
# In oauth2fast_fastapi/routers/auth.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # Creates logger named "oauth2fast_fastapi.routers.auth"

logger.info("Authentication router initialized")
```

```python
# In app/services/user_service.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # Creates logger named "app.services.user_service"

logger.info("User service initialized")
```

---

## Output Examples

### Colored Format (Development)

```
[2026-01-29 15:30:45] INFO     | app.main                | Application started
[2026-01-29 15:30:46] DEBUG    | app.services.auth       | Validating credentials
[2026-01-29 15:30:47] WARNING  | app.database            | Connection pool at 80% capacity
[2026-01-29 15:30:48] ERROR    | app.api.users           | Failed to fetch user data
```

### JSON Format (Production)

```json
{
  "timestamp": "2026-01-29T15:30:45.123456",
  "level": "INFO",
  "logger": "app.main",
  "message": "Application started",
  "module": "main",
  "function": "startup",
  "line": 42
}
```

```json
{
  "timestamp": "2026-01-29T15:30:46.789012",
  "level": "INFO",
  "logger": "app.api.users",
  "message": "User logged in",
  "module": "users",
  "function": "login",
  "line": 87,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "extra": {
    "user_id": "12345",
    "ip_address": "192.168.1.1"
  }
}
```

### Structured Format (Debugging)

```
[2026-01-29 15:30:45] INFO     | app.main             | Application started
[2026-01-29 15:30:46] INFO     | app.api.users        | User logged in [request_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890, user_id=12345, ip_address=192.168.1.1]
```

---

## File Rotation

Log files are automatically rotated based on configuration:

```
logs/
├── app_development.log          # Current log file
├── app_development.log.1        # First backup
├── app_development.log.2        # Second backup
├── app_development.log.3        # Third backup
├── app_development.log.4        # Fourth backup
└── app_development.log.5        # Fifth backup (oldest)
```

When the current log file reaches `max_bytes` (default 10MB), it's rotated and a new file is created.

---

## Best Practices

### 1. Use Module-Specific Loggers

```python
# ✅ Good - Each module has its own logger
logger = get_logger(__name__)
```

```python
# ❌ Bad - Using root logger
import logging
logger = logging.getLogger()
```

### 2. Add Context to Important Events

```python
# ✅ Good - Rich context
logger.info(
    "Payment processed",
    extra_data={
        "user_id": user.id,
        "amount": payment.amount,
        "currency": payment.currency,
        "payment_method": payment.method
    }
)
```

```python
# ❌ Bad - No context
logger.info("Payment processed")
```

### 3. Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information (variable values, flow control)
- **INFO**: General informational messages (startup, shutdown, major events)
- **WARNING**: Warning messages (deprecated features, recoverable errors)
- **ERROR**: Error messages (exceptions, failures)
- **CRITICAL**: Critical errors (system failures, data corruption)

### 4. Don't Log Sensitive Information

```python
# ❌ Bad - Logging passwords
logger.info(f"User login: {username} with password {password}")
```

```python
# ✅ Good - No sensitive data
logger.info(f"User login attempt", extra_data={"username": username})
```

### 5. Use Exception Logging for Errors

```python
# ✅ Good - Includes traceback
try:
    process_data()
except Exception as e:
    logger.exception("Failed to process data")
```

```python
# ❌ Bad - No traceback
try:
    process_data()
except Exception as e:
    logger.error(f"Error: {e}")
```

---

## Integration with Existing Modules

### oauth2fast_fastapi Example

```python
# oauth2fast_fastapi/routers/auth.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)

@router.post("/login")
async def login(credentials: LoginCredentials):
    logger.info("Login attempt", extra_data={"email": credentials.email})

    try:
        user = await authenticate_user(credentials)
        logger.info("Login successful", extra_data={"user_id": user.id})
        return {"access_token": create_token(user)}
    except AuthenticationError as e:
        logger.warning("Login failed", extra_data={"email": credentials.email, "reason": str(e)})
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

### alembic2fast_fastapi Example

```python
# alembic2fast_fastapi/base.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)

class FastAlembic:
    @staticmethod
    def run_migrations_offline(url: str, target_metadata: Any, **kwargs: Any) -> None:
        logger.info("Running migrations in offline mode")
        # ... migration logic ...
        logger.info("Offline migrations completed")
```

---

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration
2. Verify console/file output is enabled
3. Check file permissions for log directory

### File Rotation Not Working

1. Verify `max_bytes` configuration
2. Check disk space
3. Ensure write permissions on log directory

### Colors Not Showing

1. Ensure terminal supports ANSI colors
2. Check `LOG_FORMAT` is set to `colored`
3. Verify `LOG_ENVIRONMENT` is `development` or `debug`

---

## Summary

`log2fast_fastapi` provides a complete logging solution for FastAPI applications with:
- Zero-configuration defaults that work out of the box
- Environment-aware settings for development, testing, and production
- Professional output formats for different use cases
- Seamless FastAPI integration with request tracking
- Module-based organization for large applications

Start logging professionally with just two lines:

```python
from log2fast_fastapi import get_logger
logger = get_logger(__name__)
```
