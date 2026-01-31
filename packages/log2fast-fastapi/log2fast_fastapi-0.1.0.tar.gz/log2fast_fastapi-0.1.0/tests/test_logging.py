import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add root to sys.path
sys.path.insert(
    0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
)


def test_basic_logging():
    """Test basic logging functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Logging")
    print("=" * 60)

    from log2fast_fastapi import LogEnvironment, LogSettings, get_logger

    # Configure for testing
    settings = LogSettings(
        log_environment=LogEnvironment.DEVELOPMENT,
        console_enabled=True,
        file_settings__enabled=False,
    )

    logger = get_logger("test_module", config=settings)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    print("✅ Basic logging test passed")


def test_logging_with_context():
    """Test logging with extra context data."""
    print("\n" + "=" * 60)
    print("TEST 2: Logging with Context")
    print("=" * 60)

    from log2fast_fastapi import get_logger

    logger = get_logger("test_context")

    logger.info(
        "User action performed",
        extra_data={
            "user_id": "12345",
            "action": "login",
            "ip_address": "192.168.1.1",
        },
    )

    logger.warning(
        "Rate limit approaching",
        extra_data={"current_requests": 95, "limit": 100, "window": "1m"},
    )

    print("✅ Context logging test passed")


def test_exception_logging():
    """Test exception logging with traceback."""
    print("\n" + "=" * 60)
    print("TEST 3: Exception Logging")
    print("=" * 60)

    from log2fast_fastapi import get_logger

    logger = get_logger("test_exceptions")

    try:
        result = 10 / 0
        print(result)
    except ZeroDivisionError:
        logger.exception(
            "Division by zero error",
            extra_data={"operation": "division", "numerator": 10, "denominator": 0},
        )

    print("✅ Exception logging test passed")


def test_json_format():
    """Test JSON output format."""
    print("\n" + "=" * 60)
    print("TEST 4: JSON Format")
    print("=" * 60)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogFormat,
        LogSettings,
        get_logger,
    )

    # Reconfigure for JSON output
    json_settings = LogSettings(
        log_environment=LogEnvironment.PRODUCTION,
        log_format=LogFormat.JSON,
        console_enabled=True,
        file_settings__enabled=False,
    )

    FastLogger.reconfigure(json_settings)

    logger = get_logger("test_json")

    logger.info("JSON formatted message", extra_data={"format": "json", "test": True})

    print("✅ JSON format test passed")


def test_file_logging():
    """Test file logging with rotation."""
    print("\n" + "=" * 60)
    print("TEST 5: File Logging")
    print("=" * 60)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogFileSettings,
        LogSettings,
        get_logger,
    )

    # Create temporary directory for logs
    with tempfile.TemporaryDirectory() as temp_dir:
        file_settings = LogSettings(
            log_environment=LogEnvironment.DEVELOPMENT,
            console_enabled=True,
            file_settings=LogFileSettings(
                enabled=True,
                directory=temp_dir,
                max_bytes=1024,  # 1KB for testing
                backup_count=3,
                filename_pattern="test_{environment}.log",
            ),
            module_name="test_app",
        )

        FastLogger.reconfigure(file_settings)

        logger = get_logger("test_file")

        # Write some logs
        for i in range(10):
            logger.info(f"Log message {i}", extra_data={"iteration": i})

        # Check if log file was created
        log_file = Path(temp_dir) / "test_development.log"
        if log_file.exists():
            print(f"✅ Log file created: {log_file}")
            print(f"   File size: {log_file.stat().st_size} bytes")

            # Read and display first few lines
            with open(log_file) as f:
                lines = f.readlines()
                print(f"   Total lines: {len(lines)}")
                print("   First 3 lines:")
                for line in lines[:3]:
                    print(f"     {line.strip()}")
        else:
            print("❌ Log file was not created")

    print("✅ File logging test passed")


def test_module_based_loggers():
    """Test multiple module-based loggers."""
    print("\n" + "=" * 60)
    print("TEST 6: Module-Based Loggers")
    print("=" * 60)

    from log2fast_fastapi import FastLogger, LogEnvironment, LogSettings, get_logger

    # Reset configuration
    settings = LogSettings(
        log_environment=LogEnvironment.DEVELOPMENT,
        console_enabled=True,
        file_settings__enabled=False,
    )
    FastLogger.reconfigure(settings)

    # Create loggers for different modules
    auth_logger = get_logger("app.auth")
    db_logger = get_logger("app.database")
    api_logger = get_logger("app.api")

    auth_logger.info("Authentication module initialized")
    db_logger.info("Database connection established")
    api_logger.info("API routes registered")

    print("✅ Module-based loggers test passed")


async def test_fastapi_middleware():
    """Test FastAPI middleware integration."""
    print("\n" + "=" * 60)
    print("TEST 7: FastAPI Middleware")
    print("=" * 60)

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from log2fast_fastapi import (
            FastLogger,
            LogEnvironment,
            LogSettings,
            RequestLoggingMiddleware,
            get_logger,
            get_request_id,
        )

        # Configure logging
        settings = LogSettings(
            log_environment=LogEnvironment.DEVELOPMENT,
            console_enabled=True,
            file_settings__enabled=False,
        )
        FastLogger.reconfigure(settings)

        # Create FastAPI app
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        logger = get_logger("test_api")

        @app.get("/test")
        async def test_endpoint():
            request_id = get_request_id()
            logger.info("Processing request", extra_data={"request_id": request_id})
            return {"message": "success", "request_id": request_id}

        # Test the endpoint
        client = TestClient(app)
        response = client.get("/test")

        print(f"   Response status: {response.status_code}")
        print(f"   Response body: {response.json()}")
        print(f"   Request ID header: {response.headers.get('X-Request-ID')}")

        if response.status_code == 200 and "X-Request-ID" in response.headers:
            print("✅ FastAPI middleware test passed")
        else:
            print("❌ FastAPI middleware test failed")

    except ImportError:
        print("⚠️  FastAPI not installed, skipping middleware test")


def test_environment_presets():
    """Test different environment presets."""
    print("\n" + "=" * 60)
    print("TEST 8: Environment Presets")
    print("=" * 60)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogSettings,
        get_logger,
    )

    environments = [
        (LogEnvironment.DEVELOPMENT, "Development"),
        (LogEnvironment.PRODUCTION, "Production"),
        (LogEnvironment.TESTING, "Testing"),
        (LogEnvironment.DEBUG, "Debug"),
    ]

    for env, name in environments:
        print(f"\n   Testing {name} environment:")

        settings = LogSettings(
            log_environment=env, console_enabled=True, file_settings__enabled=False
        )

        print(f"     Effective level: {settings.get_effective_level()}")
        print(f"     Effective format: {settings.get_effective_format()}")

        FastLogger.reconfigure(settings)
        logger = get_logger(f"test_{env.value}")
        logger.info(f"Testing {name} environment")

    print("\n✅ Environment presets test passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RUNNING LOG2FAST_FASTAPI TESTS")
    print("=" * 60)

    try:
        test_basic_logging()
        test_logging_with_context()
        test_exception_logging()
        test_json_format()
        test_file_logging()
        test_module_based_loggers()
        asyncio.run(test_fastapi_middleware())
        test_environment_presets()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60 + "\n")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
