# Mejores Prácticas para Loggers - log2fast_fastapi

## 1. Usar `__name__` vs Nombre Hardcodeado

### ✅ RECOMENDADO: Usar `__name__`

```python
# En cualquier archivo
from log2fast_fastapi import get_logger

logger = get_logger(__name__)
```

**¿Por qué?**
- `__name__` automáticamente usa el nombre completo del módulo
- Si el archivo está en `app/routers/tenant_router.py` → `__name__` = `"app.routers.tenant_router"`
- Si el archivo está en `oauth2fast_fastapi/settings.py` → `__name__` = `"oauth2fast_fastapi.settings"`
- Es más mantenible (si mueves el archivo, el nombre se actualiza automáticamente)
- Sigue la convención estándar de Python

### ❌ NO RECOMENDADO: Nombre hardcodeado

```python
# Solo en casos muy específicos
logger = get_logger("oauth2fast_fastapi.settings")
```

**Cuándo usar:**
- Solo cuando necesitas un nombre específico diferente al módulo
- Casos muy raros (generalmente no es necesario)

---

## 2. ¿Dónde Crear el Logger?

### ✅ OPCIÓN 1: En cada archivo (RECOMENDADO)

```python
# app/routers/tenant_router.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # "app.routers.tenant_router"

@router.post("/tenants")
async def create_tenant(tenant_data: TenantCreate):
    logger.info("Creating new tenant", extra_data={"name": tenant_data.name})
    # ...
```

```python
# app/services/tenant_service.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # "app.services.tenant_service"

async def create_tenant_db(tenant_data: TenantCreate):
    logger.debug("Inserting tenant into database")
    # ...
```

**Ventajas:**
- ✅ Cada archivo tiene su propio logger con nombre específico
- ✅ Fácil identificar de dónde vienen los logs
- ✅ Puedes filtrar logs por módulo específico
- ✅ Si usas `LOG_FILE_SETTINGS__PER_MODULE_FILES=true`, cada módulo tiene su archivo
- ✅ Mejor para debugging (sabes exactamente qué archivo generó el log)

**Ejemplo de salida:**
```
[2026-01-29 16:40:00] INFO | app.routers.tenant_router | Creating new tenant
[2026-01-29 16:40:01] DEBUG | app.services.tenant_service | Inserting tenant into database
[2026-01-29 16:40:02] INFO | app.routers.tenant_router | ✅ Tenant created successfully
```

### ❌ OPCIÓN 2: En `__init__.py` compartido (NO RECOMENDADO)

```python
# app/__init__.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # "app"

# Luego en otros archivos
# app/routers/tenant_router.py
from app import logger  # ❌ Todos usan el mismo logger "app"

@router.post("/tenants")
async def create_tenant():
    logger.info("Creating tenant")  # Log aparece como "app", no "app.routers.tenant_router"
```

**Desventajas:**
- ❌ Todos los módulos comparten el mismo logger
- ❌ No puedes identificar de qué archivo específico viene el log
- ❌ Pierdes granularidad
- ❌ Dificulta el debugging

**Ejemplo de salida (malo):**
```
[2026-01-29 16:40:00] INFO | app | Creating new tenant
[2026-01-29 16:40:01] DEBUG | app | Inserting tenant into database
[2026-01-29 16:40:02] INFO | app | ✅ Tenant created successfully
```
↑ No sabes si viene de router, service, o dónde

---

## 3. Patrón Recomendado

### Estructura de Archivos

```
app/
├── __init__.py                 # NO crear logger aquí
├── main.py                     # ✅ logger = get_logger(__name__)
├── routers/
│   ├── __init__.py            # NO crear logger aquí
│   ├── tenant_router.py       # ✅ logger = get_logger(__name__)
│   └── user_router.py         # ✅ logger = get_logger(__name__)
├── services/
│   ├── __init__.py            # NO crear logger aquí
│   ├── tenant_service.py      # ✅ logger = get_logger(__name__)
│   └── user_service.py        # ✅ logger = get_logger(__name__)
└── utils/
    ├── __init__.py            # NO crear logger aquí
    └── permission_cache.py    # ✅ logger = get_logger(__name__)
```

### Código en Cada Archivo

```python
# app/routers/tenant_router.py
from fastapi import APIRouter
from log2fast_fastapi import get_logger

router = APIRouter()
logger = get_logger(__name__)  # ✅ Siempre al inicio del archivo

@router.post("/tenants")
async def create_tenant(tenant_data: TenantCreate):
    logger.info("Creating new tenant", extra_data={"name": tenant_data.name})
    # ...
```

```python
# app/services/tenant_service.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # ✅ Siempre al inicio del archivo

async def create_tenant_db(tenant_data: TenantCreate):
    logger.debug("Inserting tenant into database")
    # ...
```

```python
# app/utils/permission_cache.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # ✅ Siempre al inicio del archivo

async def get_redis_client():
    logger.info("Initializing Redis client")
    # ...
```

---

## 4. Beneficios de Usar `__name__` en Cada Archivo

### Ejemplo Real

```python
# app/routers/tenant_router.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # "app.routers.tenant_router"

@router.post("/tenants")
async def create_tenant(tenant_data: TenantCreate):
    logger.info("Creating tenant", extra_data={"name": tenant_data.name})

    try:
        tenant = await tenant_service.create_tenant_db(tenant_data)
        logger.info("✅ Tenant created", extra_data={"id": tenant.id})
        return tenant
    except Exception as e:
        logger.exception("❌ Failed to create tenant")
        raise
```

```python
# app/services/tenant_service.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # "app.services.tenant_service"

async def create_tenant_db(tenant_data: TenantCreate):
    logger.debug("Inserting tenant into database", only_in=["development", "debug"])

    # ... código de DB ...

    logger.info("Tenant inserted successfully")
    return tenant
```

### Salida de Logs

```
[2026-01-29 16:40:00] INFO | app.routers.tenant_router | Creating tenant
[2026-01-29 16:40:00] DEBUG | app.services.tenant_service | Inserting tenant into database
[2026-01-29 16:40:01] INFO | app.services.tenant_service | Tenant inserted successfully
[2026-01-29 16:40:01] INFO | app.routers.tenant_router | ✅ Tenant created
```

**Beneficios:**
- ✅ Puedes ver el flujo completo de la request
- ✅ Sabes exactamente qué archivo generó cada log
- ✅ Fácil de debuggear (buscas por nombre de módulo)
- ✅ Puedes filtrar logs: `grep "app.services.tenant_service" logs/app.log`

---

## 5. Archivos por Módulo (Opcional)

Si activas `LOG_FILE_SETTINGS__PER_MODULE_FILES=true`:

```bash
# .env
LOG_FILE_SETTINGS__PER_MODULE_FILES=true
```

**Resultado:**
```
logs/
├── app_main_development.log
├── app_routers_tenant_router_development.log
├── app_routers_user_router_development.log
├── app_services_tenant_service_development.log
├── app_services_user_service_development.log
├── app_utils_permission_cache_development.log
├── oauth2fast_fastapi_settings_development.log
└── oauth2fast_fastapi_routers_auth_development.log
```

**Ventajas:**
- ✅ Cada módulo tiene su propio archivo
- ✅ Fácil de revisar logs de un módulo específico
- ✅ Útil para microservicios o módulos grandes

**Desventajas:**
- ❌ Más archivos (puede ser confuso)
- ❌ Difícil seguir el flujo completo de una request

**Recomendación:**
- **Desarrollo:** `PER_MODULE_FILES=false` (un solo archivo, fácil de seguir)
- **Producción con microservicios:** `PER_MODULE_FILES=true` (logs separados)

---

## 6. Resumen de Mejores Prácticas

### ✅ HACER

```python
# En CADA archivo
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # ✅ Usa __name__
```

### ❌ NO HACER

```python
# En __init__.py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # ❌ No compartir logger

# En otros archivos
from app import logger  # ❌ No importar logger compartido
```

### Patrón Completo

```python
# app/routers/tenant_router.py
from fastapi import APIRouter, HTTPException
from log2fast_fastapi import get_logger

from ..services import tenant_service
from ..schemas import TenantCreate, TenantResponse

router = APIRouter()
logger = get_logger(__name__)  # ✅ Al inicio, después de imports


@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(tenant_data: TenantCreate):
    """Create a new tenant."""
    logger.info(
        "Creating new tenant",
        extra_data={"name": tenant_data.name, "admin_email": tenant_data.admin_email}
    )

    try:
        tenant = await tenant_service.create_tenant_db(tenant_data)

        logger.info(
            "✅ Tenant created successfully",
            extra_data={"tenant_id": tenant.id, "name": tenant.name}
        )

        return tenant

    except ValueError as e:
        logger.warning(
            "❌ Invalid tenant data",
            extra_data={"error": str(e), "name": tenant_data.name}
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception(
            "❌ Unexpected error creating tenant",
            extra_data={"name": tenant_data.name}
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 7. Comparación Visual

### ❌ Logger Compartido (Malo)

```python
# app/__init__.py
logger = get_logger(__name__)  # "app"

# Salida:
[INFO] app | Creating tenant
[DEBUG] app | Inserting into DB
[INFO] app | Tenant created
```
↑ No sabes de dónde viene cada log

### ✅ Logger por Archivo (Bueno)

```python
# app/routers/tenant_router.py
logger = get_logger(__name__)  # "app.routers.tenant_router"

# app/services/tenant_service.py
logger = get_logger(__name__)  # "app.services.tenant_service"

# Salida:
[INFO] app.routers.tenant_router | Creating tenant
[DEBUG] app.services.tenant_service | Inserting into DB
[INFO] app.routers.tenant_router | Tenant created
```
↑ Sabes exactamente de dónde viene cada log

---

## Conclusión

**Regla de oro:**
```python
# En CADA archivo .py
from log2fast_fastapi import get_logger

logger = get_logger(__name__)  # ✅ Siempre __name__
```

**NO crear loggers compartidos en `__init__.py`** ❌

Esto te da:
- ✅ Granularidad perfecta
- ✅ Fácil debugging
- ✅ Logs organizados
- ✅ Flexibilidad (archivos por módulo si quieres)
- ✅ Sigue las mejores prácticas de Python
