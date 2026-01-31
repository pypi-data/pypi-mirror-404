"""
Demo script showing time-based and size-based rotation strategies.
"""

import os
import sys

sys.path.insert(
    0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
)


def demo_time_based_rotation():
    """Demo: Time-based rotation (daily)."""
    print("\n" + "=" * 70)
    print("DEMO: Time-Based Rotation (Daily)")
    print("=" * 70)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogFileSettings,
        LogSettings,
        RotationStrategy,
        get_logger,
    )

    # Configure for daily rotation at midnight, keep 31 days
    settings = LogSettings(
        log_environment=LogEnvironment.DEVELOPMENT,
        console_enabled=True,
        file_settings=LogFileSettings(
            enabled=True,
            directory="/tmp/log2fast_demo_time",
            rotation_strategy=RotationStrategy.TIME,
            when="midnight",  # Rotate at midnight
            interval=1,  # Every day
            backup_count=31,  # Keep 31 days
        ),
        module_name="demo_app",
    )

    FastLogger.reconfigure(settings)
    logger = get_logger("time_rotation_demo")

    print("\n✅ Configuración:")
    print(f"   Estrategia: {settings.file_settings.rotation_strategy.value}")
    print(f"   Cuándo: {settings.file_settings.when}")
    print(f"   Intervalo: {settings.file_settings.interval}")
    print(f"   Backups: {settings.file_settings.backup_count}")
    print(f"   Directorio: {settings.file_settings.directory}")

    # Write some logs
    for i in range(5):
        logger.info(f"Log message {i} with time-based rotation")

    print("\n✅ Logs escritos con rotación diaria")
    print("   Los archivos rotarán automáticamente a medianoche")
    print("   Se mantendrán 31 días de backups")


def demo_size_based_rotation():
    """Demo: Size-based rotation."""
    print("\n" + "=" * 70)
    print("DEMO: Size-Based Rotation")
    print("=" * 70)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogFileSettings,
        LogSettings,
        RotationStrategy,
        get_logger,
    )

    # Configure for size-based rotation (1KB for demo, 3 backups)
    settings = LogSettings(
        log_environment=LogEnvironment.DEVELOPMENT,
        console_enabled=True,
        file_settings=LogFileSettings(
            enabled=True,
            directory="/tmp/log2fast_demo_size",
            rotation_strategy=RotationStrategy.SIZE,
            max_bytes=1024,  # 1KB (small for demo)
            backup_count=3,  # Keep 3 backups
        ),
        module_name="demo_app",
    )

    FastLogger.reconfigure(settings)
    logger = get_logger("size_rotation_demo")

    print("\n✅ Configuración:")
    print(f"   Estrategia: {settings.file_settings.rotation_strategy.value}")
    print(f"   Tamaño máximo: {settings.file_settings.max_bytes} bytes")
    print(f"   Backups: {settings.file_settings.backup_count}")
    print(f"   Directorio: {settings.file_settings.directory}")

    # Write enough logs to trigger rotation
    for i in range(50):
        logger.info(f"Log message {i} - writing enough data to trigger rotation")

    print("\n✅ Logs escritos con rotación por tamaño")
    print("   Los archivos rotan cuando alcanzan 1KB")
    print("   Se mantienen 3 archivos de backup")

    # Check files created
    import glob

    log_files = glob.glob(f"{settings.file_settings.directory}/*.log*")
    print(f"\n📁 Archivos creados: {len(log_files)}")
    for f in sorted(log_files):
        size = os.path.getsize(f)
        print(f"   - {os.path.basename(f)} ({size} bytes)")


def demo_per_module_files():
    """Demo: Separate files per module."""
    print("\n" + "=" * 70)
    print("DEMO: Archivos Separados por Módulo")
    print("=" * 70)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogFileSettings,
        LogSettings,
        RotationStrategy,
        get_logger,
    )

    # Configure for per-module files
    settings = LogSettings(
        log_environment=LogEnvironment.DEVELOPMENT,
        console_enabled=True,
        file_settings=LogFileSettings(
            enabled=True,
            directory="/tmp/log2fast_demo_modules",
            rotation_strategy=RotationStrategy.TIME,
            per_module_files=True,  # Separate file per module!
        ),
        module_name="demo_app",
    )

    FastLogger.reconfigure(settings)

    # Create loggers for different modules
    auth_logger = get_logger("app.auth")
    db_logger = get_logger("app.database")
    api_logger = get_logger("app.api.users")

    print("\n✅ Configuración:")
    print(f"   Archivos por módulo: {settings.file_settings.per_module_files}")
    print(f"   Directorio: {settings.file_settings.directory}")

    # Each logger writes to its own file
    auth_logger.info("Authentication module initialized")
    db_logger.info("Database connection established")
    api_logger.info("User API ready")

    print("\n✅ Cada módulo tiene su propio archivo:")

    # Check files created
    import glob

    log_files = glob.glob(f"{settings.file_settings.directory}/*.log")
    for f in sorted(log_files):
        print(f"   - {os.path.basename(f)}")


def demo_custom_directory():
    """Demo: Custom log directory."""
    print("\n" + "=" * 70)
    print("DEMO: Directorio Personalizado")
    print("=" * 70)

    from log2fast_fastapi import (
        FastLogger,
        LogEnvironment,
        LogFileSettings,
        LogSettings,
        get_logger,
    )

    # Use absolute path
    custom_dir = "/tmp/my_custom_logs/app_logs"

    settings = LogSettings(
        log_environment=LogEnvironment.PRODUCTION,
        console_enabled=True,
        file_settings=LogFileSettings(
            enabled=True,
            directory=custom_dir,  # Custom absolute path
        ),
        module_name="my_app",
    )

    FastLogger.reconfigure(settings)
    logger = get_logger("custom_dir_demo")

    print(f"\n✅ Directorio personalizado: {custom_dir}")

    logger.info("Log saved in custom directory")

    # Verify
    log_file = f"{custom_dir}/my_app_production.log"
    if os.path.exists(log_file):
        print(f"✅ Archivo creado: {log_file}")
    else:
        print(f"❌ Archivo no encontrado: {log_file}")


if __name__ == "__main__":
    demo_time_based_rotation()
    demo_size_based_rotation()
    demo_per_module_files()
    demo_custom_directory()

    print("\n" + "=" * 70)
    print("✅ TODAS LAS DEMOS COMPLETADAS")
    print("=" * 70)
    print("\nResumen:")
    print("1. Rotación por tiempo: Diaria, semanal, horaria")
    print("2. Rotación por tamaño: Cuando alcanza X MB")
    print("3. Archivos por módulo: Cada módulo su archivo")
    print("4. Directorio personalizado: Configurable desde .env")
    print("=" * 70 + "\n")
