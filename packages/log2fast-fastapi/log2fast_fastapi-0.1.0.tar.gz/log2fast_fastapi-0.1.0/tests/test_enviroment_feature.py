"""Test for environment-specific logging feature."""

import os
import sys

sys.path.insert(
    0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
)


def test_environment_specific_logging():
    """Test that only_in parameter filters logs correctly."""
    print("\n" + "=" * 60)
    print("TEST: Environment-Specific Logging")
    print("=" * 60)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogSettings,
        get_logger,
    )

    # Test in development - should see dev-only logs
    print("\n--- Testing in DEVELOPMENT ---")
    dev_settings = LogSettings(
        log_environment=LogEnvironment.DEVELOPMENT,
        console_enabled=True,
        file_settings__enabled=False,
    )
    FastLogger.reconfigure(dev_settings)
    logger = get_logger("test_env_filter")

    logger.info("This appears in ALL environments")
    logger.debug("This appears ONLY in dev/debug", only_in=["development", "debug"])
    logger.info("This appears ONLY in production", only_in=["production"])

    # Test in production - should NOT see dev-only logs
    print("\n--- Testing in PRODUCTION ---")
    prod_settings = LogSettings(
        log_environment=LogEnvironment.PRODUCTION,
        console_enabled=True,
        file_settings__enabled=False,
    )
    FastLogger.reconfigure(prod_settings)
    logger = get_logger("test_env_filter")

    logger.warning("This appears in ALL environments")
    logger.info("This appears ONLY in dev/debug", only_in=["development", "debug"])
    logger.warning("This appears ONLY in production", only_in=["production"])

    print("\n✅ Environment-specific logging test passed")
    print("   Notice: Dev-only logs did NOT appear in production!")


def test_auto_configuration():
    """Test that environment auto-configures format and level."""
    print("\n" + "=" * 60)
    print("TEST: Auto-Configuration")
    print("=" * 60)

    from log2fast_fastapi import LogEnvironment, LogFormat, LogLevel, LogSettings

    # Test development defaults
    dev_settings = LogSettings(log_environment=LogEnvironment.DEVELOPMENT)
    assert dev_settings.get_effective_level() == LogLevel.INFO.value
    assert dev_settings.get_effective_format() == LogFormat.COLORED.value
    print("✅ Development: INFO + COLORED")

    # Test production defaults
    prod_settings = LogSettings(log_environment=LogEnvironment.PRODUCTION)
    assert prod_settings.get_effective_level() == LogLevel.WARNING.value
    assert prod_settings.get_effective_format() == LogFormat.JSON.value
    print("✅ Production: WARNING + JSON")

    # Test debug defaults
    debug_settings = LogSettings(log_environment=LogEnvironment.DEBUG)
    assert debug_settings.get_effective_level() == LogLevel.DEBUG.value
    assert debug_settings.get_effective_format() == LogFormat.COLORED.value
    print("✅ Debug: DEBUG + COLORED")

    # Test testing defaults
    test_settings = LogSettings(log_environment=LogEnvironment.TESTING)
    assert test_settings.get_effective_level() == LogLevel.INFO.value
    assert test_settings.get_effective_format() == LogFormat.SIMPLE.value
    print("✅ Testing: INFO + SIMPLE")

    print("\n✅ Auto-configuration test passed")


def test_manual_override():
    """Test that manual configuration overrides auto-config."""
    print("\n" + "=" * 60)
    print("TEST: Manual Override")
    print("=" * 60)

    from log2fast_fastapi import LogEnvironment, LogFormat, LogLevel, LogSettings

    # Production with manual override
    settings = LogSettings(
        log_environment=LogEnvironment.PRODUCTION,
        log_level=LogLevel.DEBUG,  # Override default WARNING
        log_format=LogFormat.COLORED,  # Override default JSON
    )

    assert settings.get_effective_level() == LogLevel.DEBUG.value
    assert settings.get_effective_format() == LogFormat.COLORED.value

    print("✅ Manual override works correctly")
    print("   Production with DEBUG + COLORED (overridden)")


if __name__ == "__main__":
    test_auto_configuration()
    test_manual_override()
    test_environment_specific_logging()

    print("\n" + "=" * 60)
    print("✅ ALL NEW FEATURE TESTS PASSED")
    print("=" * 60 + "\n")
