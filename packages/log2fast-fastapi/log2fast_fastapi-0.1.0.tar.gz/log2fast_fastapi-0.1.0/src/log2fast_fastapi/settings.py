import os
from enum import Enum

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Look for .env in the current working directory (where the app is running)
# This allows the package to work correctly when installed via pip
DOTENV_PATH = os.path.join(os.getcwd(), ".env")


class LogLevel(str, Enum):
    """Log levels supported by the logger."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEnvironment(str, Enum):
    """Supported logging environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    DEBUG = "debug"


class LogFormat(str, Enum):
    """Supported log formats."""

    JSON = "json"
    COLORED = "colored"
    STRUCTURED = "structured"
    SIMPLE = "simple"


class RotationStrategy(str, Enum):
    """Log file rotation strategies."""

    TIME = "time"  # Rotate by time (daily, hourly, etc.)
    SIZE = "size"  # Rotate by file size


class LogFileSettings(BaseModel):
    """Configuration for file logging."""

    enabled: bool = Field(default=True, description="Enable file logging")
    directory: str = Field(default="logs", description="Directory for log files")

    # Rotation strategy
    rotation_strategy: RotationStrategy = Field(
        default=RotationStrategy.TIME,
        description="Rotation strategy: 'time' (daily) or 'size' (by file size)",
    )

    # Time-based rotation settings (when rotation_strategy='time')
    when: str = Field(
        default="midnight",
        description="When to rotate: 'midnight', 'H' (hourly), 'D' (daily), 'W0'-'W6' (weekday)",
    )
    interval: int = Field(
        default=1,
        description="Interval for rotation (e.g., 1 for daily, 2 for every 2 days)",
    )
    backup_count: int = Field(
        default=31, description="Number of backup files to keep (default 31 days)"
    )

    # Size-based rotation settings (when rotation_strategy='size')
    max_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="Max size per log file in bytes (10MB default, only for size-based rotation)",
    )

    # Common settings
    filename_pattern: str = Field(
        default="{module}_{environment}.log",
        description="Pattern for log filenames. Available: {module}, {environment}, {logger}",
    )
    per_module_files: bool = Field(
        default=False,
        description="Create separate log files per module (uses logger name in filename)",
    )


class LogSettings(BaseSettings):
    """Main logging configuration."""

    # Environment configuration
    log_environment: LogEnvironment = Field(
        default=LogEnvironment.DEVELOPMENT,
        description="Current logging environment",
    )

    # Log level configuration (None = auto-configure based on environment)
    log_level: LogLevel | None = Field(
        default=None,
        description="Minimum log level to capture (None = auto from environment)",
    )

    # Format configuration (None = auto-configure based on environment)
    log_format: LogFormat | None = Field(
        default=None, description="Log output format (None = auto from environment)"
    )

    # Console logging
    console_enabled: bool = Field(default=True, description="Enable console logging")

    # File logging
    file_settings: LogFileSettings = Field(
        default_factory=LogFileSettings, description="File logging configuration"
    )

    # Request logging (for FastAPI middleware)
    log_requests: bool = Field(
        default=True, description="Enable request/response logging"
    )
    log_request_body: bool = Field(
        default=False, description="Include request body in logs (be careful with PII)"
    )
    log_response_body: bool = Field(
        default=False,
        description="Include response body in logs (be careful with PII)",
    )

    # Module-specific settings
    module_name: str | None = Field(
        default=None, description="Default module name for loggers"
    )

    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="LOG_",
        env_nested_delimiter="__",  # Enable reading nested vars like LOG_FILE_SETTINGS__DIRECTORY
        extra="ignore",
    )

    def get_effective_level(self) -> str:
        """Get the effective log level based on environment."""
        # If explicitly set, use that value
        if self.log_level is not None:
            return self.log_level.value

        # Auto-configure based on environment
        environment_defaults = {
            LogEnvironment.DEBUG: LogLevel.DEBUG,
            LogEnvironment.DEVELOPMENT: LogLevel.INFO,
            LogEnvironment.TESTING: LogLevel.INFO,
            LogEnvironment.PRODUCTION: LogLevel.WARNING,
        }

        return environment_defaults.get(self.log_environment, LogLevel.INFO).value

    def get_effective_format(self) -> str:
        """Get the effective log format based on environment."""
        # If explicitly set, use that value
        if self.log_format is not None:
            return self.log_format.value

        # Auto-configure based on environment
        environment_defaults = {
            LogEnvironment.DEBUG: LogFormat.COLORED,
            LogEnvironment.DEVELOPMENT: LogFormat.COLORED,
            LogEnvironment.TESTING: LogFormat.SIMPLE,
            LogEnvironment.PRODUCTION: LogFormat.JSON,
        }

        return environment_defaults.get(self.log_environment, LogFormat.COLORED).value


try:
    settings = LogSettings()
except Exception as e:
    import traceback

    print("🚨 Error loading log configuration:")
    print(e)
    traceback.print_exc()
    # Fallback to defaults (auto-configure based on environment)
    settings = LogSettings(
        log_environment=LogEnvironment.DEVELOPMENT,
    )
    print("⚠️  Using fallback log configuration (DEVELOPMENT mode)")
