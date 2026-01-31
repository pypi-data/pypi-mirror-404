import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Any

from .formatters import (
    ColoredFormatter,
    JSONFormatter,
    SimpleFormatter,
    StructuredFormatter,
)
from .settings import LogFormat, LogSettings, RotationStrategy, settings


class FastLogger:
    """
    Professional logger wrapper for FastAPI applications.

    Provides environment-aware logging with support for:
    - Multiple output formats (JSON, colored, structured, simple)
    - File rotation
    - Module-based loggers
    - Context injection (request_id, user_id, etc.)
    """

    _instances: dict[str, logging.Logger] = {}
    _configured: bool = False

    def __init__(
        self,
        name: str,
        config: LogSettings | None = None,
    ):
        """
        Initialize a FastLogger instance.

        Args:
            name: Logger name (typically module name)
            config: Optional custom configuration (uses global settings if not provided)
        """
        self.name = name
        self.config = config or settings
        self.logger = self._get_or_create_logger(name)

    @classmethod
    def _get_or_create_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger instance."""
        if name not in cls._instances:
            logger = logging.getLogger(name)

            # Configure logger if not already configured
            if not cls._configured:
                cls._configure_root_logger()

            cls._instances[name] = logger

        return cls._instances[name]

    @classmethod
    def _configure_root_logger(cls) -> None:
        """Configure the root logger with handlers and formatters."""
        if cls._configured:
            return

        root_logger = logging.getLogger()
        root_logger.setLevel(settings.get_effective_level())

        # Remove existing handlers
        root_logger.handlers.clear()

        # Add console handler if enabled
        if settings.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(settings.get_effective_level())
            console_handler.setFormatter(
                cls._get_formatter(settings.get_effective_format())
            )
            root_logger.addHandler(console_handler)

        # Add file handler if enabled
        if settings.file_settings.enabled:
            file_handler = cls._create_file_handler()
            if file_handler:
                file_handler.setLevel(settings.get_effective_level())
                # Always use JSON format for file output in production
                if settings.get_effective_format() == LogFormat.JSON.value:
                    file_handler.setFormatter(cls._get_formatter(LogFormat.JSON.value))
                else:
                    file_handler.setFormatter(
                        cls._get_formatter(LogFormat.STRUCTURED.value)
                    )
                root_logger.addHandler(file_handler)

        cls._configured = True

    @classmethod
    def _get_formatter(cls, format_type: str) -> logging.Formatter:
        """Get the appropriate formatter based on format type."""
        formatters = {
            LogFormat.JSON.value: JSONFormatter(),
            LogFormat.COLORED.value: ColoredFormatter(
                fmt="[%(asctime)s] %(levelname)s | %(name)s | %(message)s"
            ),
            LogFormat.STRUCTURED.value: StructuredFormatter(),
            LogFormat.SIMPLE.value: SimpleFormatter(),
        }
        return formatters.get(format_type, SimpleFormatter())

    @classmethod
    def _create_file_handler(
        cls, logger_name: str | None = None
    ) -> RotatingFileHandler | TimedRotatingFileHandler | None:
        """
        Create a rotating file handler (time-based or size-based).

        Args:
            logger_name: Optional logger name for per-module files
        """
        try:
            # Create logs directory if it doesn't exist
            log_dir = settings.file_settings.directory
            if not os.path.isabs(log_dir):
                # Make it relative to current working directory (where the app runs)
                log_dir = os.path.join(os.getcwd(), log_dir)

            os.makedirs(log_dir, exist_ok=True)

            # Generate filename
            filename_vars = {
                "module": settings.module_name or "app",
                "environment": settings.log_environment.value,
                "logger": logger_name or "app",
            }

            # Use logger name if per_module_files is enabled
            if settings.file_settings.per_module_files and logger_name:
                # Sanitize logger name for filename (replace dots with underscores)
                safe_logger_name = logger_name.replace(".", "_")
                filename_vars["logger"] = safe_logger_name
                # Override pattern to include logger name
                filename = f"{safe_logger_name}_{settings.log_environment.value}.log"
            else:
                filename = settings.file_settings.filename_pattern.format(
                    **filename_vars
                )

            filepath = os.path.join(log_dir, filename)

            # Create handler based on rotation strategy
            if settings.file_settings.rotation_strategy == RotationStrategy.TIME:
                # Time-based rotation (default: daily at midnight, keep 31 days)
                handler = TimedRotatingFileHandler(
                    filepath,
                    when=settings.file_settings.when,
                    interval=settings.file_settings.interval,
                    backupCount=settings.file_settings.backup_count,
                    encoding="utf-8",
                )
            else:
                # Size-based rotation
                handler = RotatingFileHandler(
                    filepath,
                    maxBytes=settings.file_settings.max_bytes,
                    backupCount=settings.file_settings.backup_count,
                    encoding="utf-8",
                )

            return handler

        except Exception as e:
            print(f"⚠️  Failed to create file handler: {e}")
            return None

    @classmethod
    def reconfigure(cls, new_settings: LogSettings) -> None:
        """
        Reconfigure all loggers with new settings.

        Args:
            new_settings: New logging configuration
        """
        global settings
        settings = new_settings
        cls._configured = False
        cls._configure_root_logger()

    def _log_with_context(
        self,
        level: int,
        message: str,
        extra_data: dict[str, Any] | None = None,
        only_in: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Internal method to log with context.

        Args:
            level: Log level
            message: Log message
            extra_data: Extra context data
            only_in: List of environments where this log should appear (e.g., ['development', 'debug'])
                     If None, logs in all environments
            **kwargs: Additional arguments for logger
        """
        # Check if we should log in current environment
        if only_in is not None:
            current_env = self.config.log_environment.value
            if current_env not in only_in:
                # Skip logging in this environment
                return

        extra = kwargs.get("extra", {})

        if extra_data:
            extra["extra_data"] = extra_data

        kwargs["extra"] = extra
        self.logger.log(level, message, **kwargs)

    # Public logging methods
    def debug(
        self,
        message: str,
        extra_data: dict[str, Any] | None = None,
        only_in: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log a debug message.

        Args:
            message: Log message
            extra_data: Extra context data
            only_in: List of environments to log in (e.g., ['development', 'debug'])
        """
        self._log_with_context(logging.DEBUG, message, extra_data, only_in, **kwargs)

    def info(
        self,
        message: str,
        extra_data: dict[str, Any] | None = None,
        only_in: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log an info message.

        Args:
            message: Log message
            extra_data: Extra context data
            only_in: List of environments to log in (e.g., ['development', 'production'])
        """
        self._log_with_context(logging.INFO, message, extra_data, only_in, **kwargs)

    def warning(
        self,
        message: str,
        extra_data: dict[str, Any] | None = None,
        only_in: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log a warning message.

        Args:
            message: Log message
            extra_data: Extra context data
            only_in: List of environments to log in
        """
        self._log_with_context(logging.WARNING, message, extra_data, only_in, **kwargs)

    def error(
        self,
        message: str,
        extra_data: dict[str, Any] | None = None,
        only_in: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log an error message.

        Args:
            message: Log message
            extra_data: Extra context data
            only_in: List of environments to log in
        """
        self._log_with_context(logging.ERROR, message, extra_data, only_in, **kwargs)

    def critical(
        self,
        message: str,
        extra_data: dict[str, Any] | None = None,
        only_in: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log a critical message.

        Args:
            message: Log message
            extra_data: Extra context data
            only_in: List of environments to log in
        """
        self._log_with_context(logging.CRITICAL, message, extra_data, only_in, **kwargs)

    def exception(
        self,
        message: str,
        extra_data: dict[str, Any] | None = None,
        only_in: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log an exception with traceback.

        Args:
            message: Log message
            extra_data: Extra context data
            only_in: List of environments to log in
        """
        kwargs["exc_info"] = True
        self._log_with_context(logging.ERROR, message, extra_data, only_in, **kwargs)


def get_logger(name: str, config: LogSettings | None = None) -> FastLogger:
    """
    Factory function to get a module-specific logger.

    Args:
        name: Logger name (typically __name__ of the calling module)
        config: Optional custom configuration

    Returns:
        FastLogger instance

    Example:
        >>> from log2fast_fastapi import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return FastLogger(name, config)
