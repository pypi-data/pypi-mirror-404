"""
Demo script showing the new environment-based auto-configuration
and environment-specific logging features.
"""

import os
import sys

# Add root to sys.path
sys.path.insert(
    0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

from log2fast_fastapi import (
    FastLogger,
    LogEnvironment,
    LogSettings,
    get_logger,
)


def demo_auto_configuration():
    """Demo: Auto-configuration based on environment."""
    print("\n" + "=" * 70)
    print("DEMO 1: Auto-Configuration Based on Environment")
    print("=" * 70)
    print("\nYou only need to set LOG_ENVIRONMENT in .env!")
    print("Format and level are automatically configured.\n")

    environments = [
        (LogEnvironment.DEVELOPMENT, "Development"),
        (LogEnvironment.PRODUCTION, "Production"),
        (LogEnvironment.TESTING, "Testing"),
        (LogEnvironment.DEBUG, "Debug"),
    ]

    for env, name in environments:
        print(f"\n--- {name} Environment ---")

        # Only set the environment - format and level auto-configure!
        settings = LogSettings(
            log_environment=env,
            console_enabled=True,
            file_settings__enabled=False,
        )

        print(f"  Environment: {env.value}")
        print(f"  Auto Level: {settings.get_effective_level()}")
        print(f"  Auto Format: {settings.get_effective_format()}")

        FastLogger.reconfigure(settings)
        logger = get_logger(f"demo_{env.value}")

        logger.info(f"This is {name} environment")


def demo_environment_specific_logging():
    """Demo: Log only in specific environments."""
    print("\n" + "=" * 70)
    print("DEMO 2: Environment-Specific Logging")
    print("=" * 70)
    print("\nPrevent sensitive data from being logged in production!\n")

    # Simulate different environments
    environments = [
        LogEnvironment.DEVELOPMENT,
        LogEnvironment.PRODUCTION,
        LogEnvironment.DEBUG,
    ]

    for env in environments:
        print(f"\n--- Current Environment: {env.value} ---")

        settings = LogSettings(
            log_environment=env,
            console_enabled=True,
            file_settings__enabled=False,
        )
        FastLogger.reconfigure(settings)
        logger = get_logger("security_demo")

        # This logs in ALL environments
        logger.info("User logged in", extra_data={"user_id": "12345"})

        # This logs ONLY in development and debug (NOT in production)
        logger.debug(
            "Sensitive debug info: password hash, tokens, etc.",
            extra_data={
                "password_hash": "bcrypt$2b$12$...",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "def50200...",
            },
            only_in=["development", "debug"],
        )

        # This logs ONLY in production (e.g., for monitoring)
        logger.warning(
            "High memory usage detected",
            extra_data={"memory_percent": 85, "threshold": 80},
            only_in=["production"],
        )

        # This logs in development and testing (NOT in production)
        logger.info(
            "Database query details",
            extra_data={
                "query": "SELECT * FROM users WHERE email = ?",
                "params": ["user@example.com"],
                "execution_time_ms": 45,
            },
            only_in=["development", "testing", "debug"],
        )


def demo_override_defaults():
    """Demo: Override auto-configuration when needed."""
    print("\n" + "=" * 70)
    print("DEMO 3: Override Auto-Configuration")
    print("=" * 70)
    print("\nYou can still override format and level if needed.\n")

    # Auto-configuration (production defaults to JSON + WARNING)
    print("--- Production with Auto-Config ---")
    auto_settings = LogSettings(
        log_environment=LogEnvironment.PRODUCTION,
        console_enabled=True,
        file_settings__enabled=False,
    )
    print(f"  Level: {auto_settings.get_effective_level()}")
    print(f"  Format: {auto_settings.get_effective_format()}")

    # Manual override (force DEBUG level in production)
    print("\n--- Production with Manual Override ---")
    from log2fast_fastapi import LogFormat, LogLevel

    override_settings = LogSettings(
        log_environment=LogEnvironment.PRODUCTION,
        log_level=LogLevel.DEBUG,  # Override!
        log_format=LogFormat.COLORED,  # Override!
        console_enabled=True,
        file_settings__enabled=False,
    )
    print(f"  Level: {override_settings.get_effective_level()}")
    print(f"  Format: {override_settings.get_effective_format()}")

    FastLogger.reconfigure(override_settings)
    logger = get_logger("override_demo")
    logger.debug("This debug message appears even in production!")


def demo_practical_example():
    """Demo: Practical real-world example."""
    print("\n" + "=" * 70)
    print("DEMO 4: Practical Real-World Example")
    print("=" * 70)
    print("\nSimulating a user authentication flow.\n")

    # Simulate production environment
    settings = LogSettings(
        log_environment=LogEnvironment.PRODUCTION,
        console_enabled=True,
        file_settings__enabled=False,
    )
    FastLogger.reconfigure(settings)
    logger = get_logger("auth_service")

    # Public info - logs in all environments
    logger.info("Authentication attempt", extra_data={"email": "user@example.com"})

    # Sensitive debug info - ONLY in dev/debug
    logger.debug(
        "Password verification details",
        extra_data={
            "password_hash": "bcrypt$2b$12$abcdef...",
            "salt": "random_salt_123",
            "hash_algorithm": "bcrypt",
        },
        only_in=["development", "debug"],
    )

    # Business logic - logs in all environments
    logger.info("User authenticated successfully", extra_data={"user_id": "12345"})

    # Token details - ONLY in dev/debug
    logger.debug(
        "JWT token generated",
        extra_data={
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
        only_in=["development", "debug"],
    )

    # Monitoring metric - ONLY in production
    logger.info(
        "Authentication metrics",
        extra_data={
            "success_rate": 0.95,
            "avg_response_time_ms": 120,
            "total_attempts": 1000,
        },
        only_in=["production"],
    )

    print("\n✅ Notice: Sensitive data (passwords, tokens) NOT logged in production!")


if __name__ == "__main__":
    demo_auto_configuration()
    demo_environment_specific_logging()
    demo_override_defaults()
    demo_practical_example()

    print("\n" + "=" * 70)
    print("✅ ALL DEMOS COMPLETED")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. Just set LOG_ENVIRONMENT in .env - format and level auto-configure")
    print(
        "2. Use only_in=['development', 'debug'] to prevent sensitive logs in production"
    )
    print("3. You can still override defaults when needed")
    print("4. Perfect for keeping secrets safe while debugging locally")
    print("=" * 70 + "\n")
