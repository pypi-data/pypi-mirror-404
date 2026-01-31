# Gestión de Archivos de Log - log2fast_fastapi

## Configuración desde `.env`

### ✅ Configuración Mínima (Recomendada)

```bash
# Solo necesitas esto - usa defaults inteligentes
LOG_ENVIRONMENT=production
```

**Defaults automáticos:**
- ✅ Rotación diaria a medianoche
- ✅ Mantiene 31 días de backups
- ✅ Directorio: `logs/` (en raíz del proyecto)
- ✅ Formato JSON en producción

---

## Opciones de Almacenamiento

### 1. Rotación por Tiempo (Default - Recomendado)

**Mejor para:** Aplicaciones en producción, auditoría, compliance

**Ventajas:**
- ✅ Logs organizados por fecha
- ✅ Fácil de archivar y buscar
- ✅ Predecible (sabes exactamente cuántos días tienes)
- ✅ Ideal para compliance (ej: "mantener 90 días de logs")

#### Configuración Diaria (Default)

```bash
# .env
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=31
```

**Resultado:**
```
logs/
├── app_production.log              # Hoy
├── app_production.log.2026-01-29   # Ayer
├── app_production.log.2026-01-28   # Hace 2 días
├── ...
└── app_production.log.2025-12-30   # Hace 31 días
```

#### Configuración Horaria

```bash
# .env - Para aplicaciones de alto tráfico
LOG_FILE_SETTINGS__WHEN=H
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=24
```

**Resultado:** Rota cada hora, mantiene 24 horas

#### Configuración Semanal

```bash
# .env - Para aplicaciones de bajo tráfico
LOG_FILE_SETTINGS__WHEN=W0  # W0=Lunes, W6=Domingo
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=12
```

**Resultado:** Rota cada lunes, mantiene 12 semanas

---

### 2. Rotación por Tamaño

**Mejor para:** Desarrollo, debugging, aplicaciones con tráfico variable

**Ventajas:**
- ✅ Control preciso del espacio en disco
- ✅ Útil cuando el tráfico es impredecible
- ✅ Evita archivos gigantes en picos de tráfico

#### Configuración Básica

```bash
# .env
LOG_FILE_SETTINGS__ROTATION_STRATEGY=size
LOG_FILE_SETTINGS__MAX_BYTES=10485760  # 10MB
LOG_FILE_SETTINGS__BACKUP_COUNT=5
```

**Resultado:**
```
logs/
├── app_development.log    # Actual (hasta 10MB)
├── app_development.log.1  # Backup 1
├── app_development.log.2  # Backup 2
├── app_development.log.3  # Backup 3
├── app_development.log.4  # Backup 4
└── app_development.log.5  # Backup 5 (más antiguo)
```

#### Tamaños Comunes

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

## Localización de Logs

### Opción 1: Ruta Relativa (Default)

```bash
# .env
LOG_FILE_SETTINGS__DIRECTORY=logs
```

**Resultado:** `<proyecto>/logs/`

### Opción 2: Ruta Absoluta

```bash
# .env
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
```

**Resultado:** `/var/log/myapp/`

### Opción 3: Ruta Personalizada por Ambiente

```bash
# .env.development
LOG_FILE_SETTINGS__DIRECTORY=./dev_logs

# .env.production
LOG_FILE_SETTINGS__DIRECTORY=/var/log/production/myapp
```

---

## Archivos por Módulo

### Sin Separación (Default)

Todos los módulos escriben al mismo archivo.

```bash
# .env
LOG_FILE_SETTINGS__PER_MODULE_FILES=false
```

**Resultado:**
```
logs/
└── app_production.log  # Todos los módulos aquí
```

**Ventajas:**
- ✅ Más simple
- ✅ Fácil de seguir el flujo completo
- ✅ Menos archivos

### Con Separación por Módulo

Cada módulo tiene su propio archivo.

```bash
# .env
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
```

**Resultado:**
```
logs/
├── app_auth_production.log
├── app_database_production.log
├── app_api_users_production.log
├── oauth2fast_fastapi_routers_auth_production.log
└── alembic2fast_fastapi_base_production.log
```

**Ventajas:**
- ✅ Fácil de debuggear módulos específicos
- ✅ Mejor para microservicios
- ✅ Logs más organizados

**Código:**
```python
# Cada logger automáticamente usa su nombre
auth_logger = get_logger("app.auth")  # → app_auth_production.log
db_logger = get_logger("app.database")  # → app_database_production.log
```

---

## Comparación de Estrategias

### ¿Cuándo usar Rotación por Tiempo?

✅ **Usar cuando:**
- Necesitas compliance (ej: "mantener 90 días")
- Quieres logs organizados por fecha
- Tráfico predecible
- Producción

❌ **No usar cuando:**
- Tráfico muy variable (puede generar archivos gigantes)
- Espacio en disco limitado y tráfico impredecible

### ¿Cuándo usar Rotación por Tamaño?

✅ **Usar cuando:**
- Espacio en disco limitado
- Tráfico impredecible
- Desarrollo/debugging
- Quieres control preciso del espacio

❌ **No usar cuando:**
- Necesitas compliance por tiempo
- Quieres buscar logs por fecha

---

## Configuraciones Recomendadas por Escenario

### Desarrollo Local

```bash
LOG_ENVIRONMENT=development
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=7  # Solo 7 días
LOG_FILE_SETTINGS__DIRECTORY=./logs
```

**Razón:** Logs diarios, no ocupan mucho espacio

### Producción - Aplicación Web

```bash
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=90  # 90 días para compliance
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
```

**Razón:** Compliance, fácil de archivar

### Producción - Alto Tráfico

```bash
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=H  # Cada hora
LOG_FILE_SETTINGS__INTERVAL=1
LOG_FILE_SETTINGS__BACKUP_COUNT=168  # 7 días × 24 horas
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
```

**Razón:** Evita archivos gigantes

### Debugging Intensivo

```bash
LOG_ENVIRONMENT=debug
LOG_FILE_SETTINGS__ROTATION_STRATEGY=size
LOG_FILE_SETTINGS__MAX_BYTES=52428800  # 50MB
LOG_FILE_SETTINGS__BACKUP_COUNT=3
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
```

**Razón:** Control de espacio, logs por módulo

### Testing/CI

```bash
LOG_ENVIRONMENT=testing
LOG_FILE_SETTINGS__ENABLED=false  # Solo consola
```

**Razón:** No necesitas archivos en tests

---

## Opciones Adicionales de Almacenamiento

### 1. Archivos de Log (Actual)

**Ventajas:**
- ✅ Simple y estándar
- ✅ Fácil de leer con `tail`, `grep`, etc.
- ✅ Compatible con todas las herramientas

**Desventajas:**
- ❌ No escala bien para millones de logs
- ❌ Búsqueda lenta en archivos grandes

### 2. Bases de Datos (Futuro)

Para implementar en el futuro si es necesario:

```python
# Ejemplo conceptual
from log2fast_fastapi import LogSettings, DatabaseHandler

settings = LogSettings(
    database_handler=DatabaseHandler(
        url="postgresql://...",
        table="application_logs"
    )
)
```

**Ventajas:**
- ✅ Búsqueda rápida
- ✅ Queries complejas
- ✅ Retención configurable

**Desventajas:**
- ❌ Más complejo
- ❌ Overhead de BD

### 3. Servicios Externos (Futuro)

Para implementar si es necesario:

```python
# Ejemplo conceptual
from log2fast_fastapi import LogSettings, SentryHandler

settings = LogSettings(
    external_handlers=[
        SentryHandler(dsn="..."),
        DatadogHandler(api_key="..."),
    ]
)
```

**Servicios populares:**
- Sentry (errores)
- Datadog (monitoreo)
- CloudWatch (AWS)
- Stackdriver (GCP)

---

## Mejores Prácticas

### 1. Usa Rotación por Tiempo en Producción

```bash
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=90
```

**Razón:** Compliance, organización, predecibilidad

### 2. Configura el Directorio Apropiado

```bash
# Desarrollo
LOG_FILE_SETTINGS__DIRECTORY=./logs

# Producción (Linux)
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp

# Producción (Docker)
LOG_FILE_SETTINGS__DIRECTORY=/app/logs
```

### 3. Ajusta Backups según Necesidad

```bash
# Desarrollo: 7 días es suficiente
LOG_FILE_SETTINGS__BACKUP_COUNT=7

# Producción: 30-90 días según compliance
LOG_FILE_SETTINGS__BACKUP_COUNT=90

# Alto tráfico horario: 7 días × 24 horas
LOG_FILE_SETTINGS__BACKUP_COUNT=168
```

### 4. Usa Archivos por Módulo en Microservicios

```bash
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
```

**Razón:** Cada servicio tiene sus logs separados

### 5. Monitorea el Espacio en Disco

```bash
# Calcula espacio necesario
# Rotación diaria: tamaño_diario × backup_count
# Ejemplo: 100MB/día × 90 días = 9GB

# Rotación por tamaño: max_bytes × (backup_count + 1)
# Ejemplo: 50MB × 6 = 300MB
```

---

## Ejemplos Completos

### Ejemplo 1: Startup Simple

```bash
# .env
LOG_ENVIRONMENT=production
LOG_MODULE_NAME=myapp
```

**Resultado:**
- Rotación diaria a medianoche
- 31 días de backups
- Formato JSON
- Directorio: `logs/`

### Ejemplo 2: Empresa con Compliance

```bash
# .env
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=365  # 1 año
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
LOG_MODULE_NAME=myapp
```

### Ejemplo 3: Microservicios

```bash
# .env
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
LOG_FILE_SETTINGS__ROTATION_STRATEGY=time
LOG_FILE_SETTINGS__WHEN=midnight
LOG_FILE_SETTINGS__BACKUP_COUNT=30
LOG_FILE_SETTINGS__DIRECTORY=/var/log/services
```

**Resultado:**
```
/var/log/services/
├── auth_service_production.log
├── payment_service_production.log
├── user_service_production.log
└── notification_service_production.log
```

---

## Resumen

| Característica | Default | Configurable | Recomendación |
|---------------|---------|--------------|---------------|
| **Estrategia** | Time (diaria) | ✅ | Time para producción |
| **Cuándo** | Medianoche | ✅ | Medianoche o cada hora |
| **Backups** | 31 días | ✅ | 30-90 días producción |
| **Directorio** | `logs/` | ✅ | `/var/log/app` producción |
| **Por módulo** | No | ✅ | Sí para microservicios |
| **Tamaño max** | 10MB | ✅ | 50-100MB si usas size |

**Configuración recomendada para producción:**

```bash
LOG_ENVIRONMENT=production
LOG_FILE_SETTINGS__DIRECTORY=/var/log/myapp
LOG_FILE_SETTINGS__BACKUP_COUNT=90
```

¡Eso es todo! El sistema es flexible y se adapta a tus necesidades. 🚀
