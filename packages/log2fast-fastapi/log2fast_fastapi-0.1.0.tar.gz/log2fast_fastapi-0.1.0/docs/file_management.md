# Log File Management - log2fast_fastapi

## Configuration from `.env`

### ✅ Minimal Configuration (Recommended)

```bash
# That's all you need - uses smart defaults
LOG_ENVIRONMENT=production
```

**Automatic defaults:**
- ✅ Daily rotation at midnight
- ✅ Keeps 31 days of backups
- ✅ Directory: `logs/` (at project root)
- ✅ JSON format in production

---

## Storage Options

### 1. Time-Based Rotation (Default - Recommended)

**Best for:** Production applications, auditing, compliance

**Advantages:**
- ✅ Logs organized by date
- ✅ Easy to archive and search
- ✅ Predictable (you know exactly how many days you have)
- ✅ Ideal for compliance (e.g., "keep 90 days of logs")

#### Daily Configuration (Default)

```bash
# .env
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=31
```

**Result:**
```
logs/
├── app_production.log              # Today
├── app_production.log.2026-01-29   # Yesterday
├── app_production.log.2026-01-28   # 2 days ago
├── ...
└── app_production.log.2025-12-30   # 31 days ago
```

#### Hourly Configuration

```bash
# .env - For high-traffic applications
LOG_FILE_SETTINGS__WHEN=H
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=24
```

**Result:** Rotates every hour, keeps 24 hours

#### Weekly Configuration

```bash
# .env - For low-traffic applications
LOG_FILE_SETTINGS__WHEN=W0  # W0=Monday, W6=Sunday
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=12
```

**Result:** Rotates every Monday, keeps 12 weeks

---

### 2. Size-Based Rotation

**Best for:** Development, debugging, applications with variable traffic

**Advantages:**
- ✅ Precise disk space control
- ✅ Useful when traffic is unpredictable
- ✅ Prevents huge files during traffic spikes

#### Basic Configuration

```bash
# .env
LOG_FILE_SETTINGS__ROTATION_STRATEGY=size
LOG_FILE_SETTINGS__MAX_BYTES=10485760  # 10MB
LOG_FILE_SETTINGS__BACKUP_COUNT=5
```

**Result:**
```
logs/
├── app_development.log    # Current (up to 10MB)
├── app_development.log.1  # Backup 1
├── app_development.log.2  # Backup 2
├── app_development.log.3  # Backup 3
├── app_development.log.4  # Backup 4
└── app_development.log.5  # Backup 5 (oldest)
```

#### Common Sizes

```bash
# 10MB (default)
LOG_FILE_SETTINGS__MAX_BYTES=10485760

# 50MB
LOG_FILE_SETTINGS__MAX_BYTES=52428800

# 100MB
LOG_FILE_SETTINGS__MAX_BYTES=104857600

# 500MB
LOG_FILE_SETTINGS__MAX_BYTES=524288000
```

---

## Log Location

### Option 1: Relative Path (Default)

```bash
# .env
LOG_FILE_SETTINGS__DIRECTORY=logs
```

**Result:** `<project>/logs/`

### Option 2: Absolute Path

```bash
# .env
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
```

**Result:** `/var/log/myapp/`

### Option 3: Custom Path per Environment

```bash
# .env.development
LOG_FILE_SETTINGS__DIRECTORY=./dev_logs

# .env.production
LOG_FILE_SETTINGS__DIRECTORY=/var/log/production/myapp
```

---

## Per-Module Files

### Without Separation (Default)

All modules write to the same file.

```bash
# .env
LOG_FILE_SETTINGS__PER_MODULE_FILES=false
```

**Result:**
```
logs/
└── app_production.log  # All modules here
```

**Advantages:**
- ✅ Simpler
- ✅ Easy to follow complete flow
- ✅ Fewer files

### With Per-Module Separation

Each module has its own file.

```bash
# .env
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
```

**Result:**
```
logs/
├── app_auth_production.log
├── app_database_production.log
├── app_api_users_production.log
├── oauth2fast_fastapi_routers_auth_production.log
└── alembic2fast_fastapi_base_production.log
```

**Advantages:**
- ✅ Easy to debug specific modules
- ✅ Better for microservices
- ✅ More organized logs

**Code:**
```python
# Each logger automatically uses its name
auth_logger = get_logger("app.auth")  # → app_auth_production.log
db_logger = get_logger("app.database")  # → app_database_production.log
```

---

## Strategy Comparison

### When to use Time-Based Rotation?

✅ **Use when:**
- You need compliance (e.g., "keep 90 days")
- You want logs organized by date
- Predictable traffic
- Production

❌ **Don't use when:**
- Very variable traffic (can generate huge files)
- Limited disk space and unpredictable traffic

### When to use Size-Based Rotation?

✅ **Use when:**
- Limited disk space
- Unpredictable traffic
- Development/debugging
- You want precise space control

❌ **Don't use when:**
- You need time-based compliance
- You want to search logs by date

---

## Recommended Configurations by Scenario

### Local Development

```bash
LOG_ENVIRONMENT=development
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=7  # Only 7 days
LOG_FILE_SETTINGS__DIRECTORY=./logs
```

**Reason:** Daily logs, don't take much space

### Production - Web Application

```bash
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=90  # 90 days for compliance
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
```

**Reason:** Compliance, easy to archive

### Production - High Traffic

```bash
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=H  # Every hour
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=168  # 7 days × 24 hours
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
```

**Reason:** Prevents huge files

### Intensive Debugging

```bash
LOG_ENVIRONMENT=debug
LOG_FILE_SETTINGS__ROTATION_STRATEGY=size
LOG_FILE_SETTINGS__MAX_BYTES=52428800  # 50MB
LOG_FILE_SETTINGS__BACKUP_COUNT=3
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
```

**Reason:** Space control, per-module logs

### Testing/CI

```bash
LOG_ENVIRONMENT=testing
LOG_FILE_SETTINGS__ENABLED=false  # Console only
```

**Reason:** You don't need files in tests

---

## Additional Storage Options

### 1. Log Files (Current)

**Advantages:**
- ✅ Simple and standard
- ✅ Easy to read with `tail`, `grep`, etc.
- ✅ Compatible with all tools

**Disadvantages:**
- ❌ Doesn't scale well for millions of logs
- ❌ Slow search in large files

### 2. Databases (Future)

To implement in the future if needed:

```python
# Conceptual example
from log2fast_fastapi import LogSettings, DatabaseHandler

settings = LogSettings(
    database_handler=DatabaseHandler(
        url="postgresql://...",
        table="application_logs"
    )
)
```

**Advantages:**
- ✅ Fast search
- ✅ Complex queries
- ✅ Configurable retention

**Disadvantages:**
- ❌ More complex
- ❌ Database overhead

### 3. External Services (Future)

To implement if needed:

```python
# Conceptual example
from log2fast_fastapi import LogSettings, SentryHandler

settings = LogSettings(
    external_handlers=[
        SentryHandler(dsn="..."),
        DatadogHandler(api_key="..."),
    ]
)
```

**Popular services:**
- Sentry (errors)
- Datadog (monitoring)
- CloudWatch (AWS)
- Stackdriver (GCP)

---

## Best Practices

### 1. Use Time-Based Rotation in Production

```bash
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=90
```

**Reason:** Compliance, organization, predictability

### 2. Configure Appropriate Directory

```bash
# Development
LOG_FILE_SETTINGS__DIRECTORY=./logs

# Production (Linux)
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp

# Production (Docker)
LOG_FILE_SETTINGS__DIRECTORY=/app/logs
```

### 3. Adjust Backups According to Need

```bash
# Development: 7 days is enough
LOG_FILE_SETTINGS__BACKUP_COUNT=7

# Production: 30-90 days according to compliance
LOG_FILE_SETTINGS__BACKUP_COUNT=90

# High traffic hourly: 7 days × 24 hours
LOG_FILE_SETTINGS__BACKUP_COUNT=168
```

### 4. Use Per-Module Files in Microservices

```bash
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
```

**Reason:** Each service has its logs separated

### 5. Monitor Disk Space

```bash
# Calculate needed space
# Daily rotation: daily_size × backup_count
# Example: 100MB/day × 90 days = 9GB

# Size rotation: max_bytes × (backup_count + 1)
# Example: 50MB × 6 = 300MB
```

---

## Complete Examples

### Example 1: Simple Startup

```bash
# .env
LOG_ENVIRONMENT=production
LOG_MODULE_NAME=myapp
```

**Result:**
- Daily rotation at midnight
- 31 days of backups
- JSON format
- Directory: `logs/`

### Example 2: Enterprise with Compliance

```bash
# .env
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=365  # 1 year
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
LOG_MODULE_NAME=myapp
```

### Example 3: Microservices

```bash
# .env
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=30
LOG_FILE_SETTINGS__DIRECTORY=/var/log/services
```

**Result:**
```
/var/log/services/
├── auth_service_production.log
├── payment_service_production.log
├── user_service_production.log
└── notification_service_production.log
```

---

## Summary

| Feature | Default | Configurable | Recommendation |
|---------|---------|--------------|----------------|
| **Strategy** | Time (daily) | ✅ | Time for production |
| **When** | Midnight | ✅ | Midnight or hourly |
| **Backups** | 31 days | ✅ | 30-90 days production |
| **Directory** | `logs/` | ✅ | `/var/log/app` production |
| **Per module** | No | ✅ | Yes for microservices |
| **Max size** | 10MB | ✅ | 50-100MB if using size |

**Recommended configuration for production:**

```bash
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
LOG_FILE_SETTINGS__BACKUP_COUNT=90
```

That's it! The system is flexible and adapts to your needs. 🚀
