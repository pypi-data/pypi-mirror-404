import json
import logging
from datetime import datetime
from typing import Any


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        IMPORTANT: We create a shallow copy of the record to avoid modifying
        the original, which would cause color codes to leak into file logs.
        """
        # Create a shallow copy to avoid modifying the original record
        record_copy = logging.makeLogRecord(record.__dict__)

        # Add color to level name
        levelname = record_copy.levelname
        if levelname in self.COLORS:
            record_copy.levelname = (
                f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
            )

        # Add color to module name
        record_copy.name = f"\033[94m{record_copy.name}{self.RESET}"  # Blue

        # Format timestamp
        record_copy.asctime = self.formatTime(record_copy, "%Y-%m-%d %H:%M:%S")

        # Format the message using the copy
        formatted = super().format(record_copy)

        return formatted


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Add any custom attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "request_id",
                "user_id",
                "extra_data",
            ]:
                if not key.startswith("_"):
                    log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """Structured formatter for human-readable logs with context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured information."""
        # Base format
        base = f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] {record.levelname:8s} | {record.name:20s} | {record.getMessage()}"

        # Add context if available
        context_parts = []

        if hasattr(record, "request_id"):
            context_parts.append(f"request_id={record.request_id}")

        if hasattr(record, "user_id"):
            context_parts.append(f"user_id={record.user_id}")

        if hasattr(record, "extra_data") and record.extra_data:
            for key, value in record.extra_data.items():
                context_parts.append(f"{key}={value}")

        if context_parts:
            base += f" [{', '.join(context_parts)}]"

        # Add exception if present
        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


class SimpleFormatter(logging.Formatter):
    """Simple formatter for testing and minimal output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record simply."""
        return f"[{record.levelname}] {record.name}: {record.getMessage()}"
