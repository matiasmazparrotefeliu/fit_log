# Reglas del agente — FitLog / RunTracker

Este archivo define **cómo debe trabajar el agente** en este repositorio. Es un documento
**vivo**: se actualiza cada vez que el responsable del proyecto indique una regla nueva.
Las reglas se agregan en la sección **«Registro de reglas»** (§ 9) con fecha y origen.

---

## 1. Fuente de verdad

- **Arquitectura:** `architecture.md` es la referencia técnica obligatoria.
- **Estado y ejecución:** `README.md`.
- **Documentación funcional:** los requisitos de negocio provistos por el responsable
  (módulos RF-01 a RF-06 y documentación de persistencia).
- Si hay conflicto entre una instrucción puntual y estos documentos, **prevalece la
  instrucción puntual del responsable** y se actualiza la documentación en el mismo cambio.

---

## 2. Reglas de arquitectura (no negociables)

1. Respetar **Clean / Layered Architecture** y la regla de dependencia:
   `presentation → application → domain`, con `infrastructure` implementando los *ports* de `domain`.
2. **`domain` no importa FastAPI ni SQLAlchemy.** Debe ser lógica pura y testeable.
3. **`application` solo depende de `domain`** (y utilidades de `core`/`shared`).
4. **`infrastructure` implementa los ports**; contiene SQLAlchemy, repositorios, cache y JWT.
5. **`presentation`** solo traduce HTTP ↔ casos de uso (routers + schemas Pydantic).
6. **Prohibido el acceso cruzado entre módulos**: un módulo no consulta tablas de otro módulo.
   La comunicación es vía interfaces de `application`.
7. Mantener el estilo **Monolito Modular + BFF**. `analytics` es el BFF del dashboard.
8. Todo el código de dominio vive dentro de `backend/app/modules/<modulo>/`.

---

## 3. Reglas de persistencia

1. Respetar **exactamente** el modelo de datos de `architecture.md` § 5
   (nombres de tabla/columna, tipos y restricciones). No inventar ni renombrar columnas.
2. PK **UUID** con `gen_random_uuid()`, `created_at` **TIMESTAMPTZ**, duraciones **INTERVAL**,
   montos/precisión **NUMERIC**.
3. Cascadas: `user → *` con `ON DELETE CASCADE`; `gear`/`workout` referenciados con `SET NULL`.
4. Respetar las restricciones `UNIQUE` y `CHECK` indicadas (p. ej. `runner`/`admin`,
   `unique_user_event_distance`, `unique_user_daily_log`).
5. **Aislamiento por `user_id`** en todas las tablas no-catálogo.
6. **No crear vistas ni triggers** por ahora: `v_gear_usage` y el trigger de pace se calculan
   en la capa `application`/`domain`.
7. Todo cambio de esquema pasa por **Alembic** (desde F2), nunca alterando la base a mano.
8. **PostgreSQL** es el motor objetivo (no SQLite).

---

## 4. Reglas de código

1. Lenguaje del backend: **Python 3.11+** (compatible con 3.10), tipado estático en firmas y modelos Pydantic.
2. Formato: **PEP 8**; imports ordenados; nombres en inglés para código, docstrings/comentarios
   en español (consistente con el proyecto).
3. Configuración **solo** vía `app.core.config.settings` (desde F1); nunca `os.environ` directo.
4. Autenticación: **JWT**; RBAC mediante `require_role(...)`. El catálogo de eventos exige `admin`.
5. Cache **solo** a través de `CachePort` (implementación in-memory; Redis luego, sin tocar dominio).
6. Errores: usar el manejo centralizado de `core/errors.py` con formato de respuesta uniforme.
7. No introducir dependencias nuevas sin justificarlo y registrarlo en `requirements.txt`.

---

## 5. Reglas de proceso (fases)

1. Seguir **estrictamente el orden de fases** definido en `architecture.md` § 9 y `README.md`.
2. **Una fase por módulo de dominio.** No agrupar varios módulos en una fase.
3. **Cada módulo se crea únicamente al llegar a su fase.** Prohibido pre-crear la estructura
   de módulos futuros.
4. La **base transversal** (inicialización, `core`, `shared`) se construye antes que cualquier módulo.
5. **La primera fase funcional es F2 (auth/users)**.
6. `requirements.txt` **crece por fase**: declarar solo lo que cada fase necesita.
7. Cerrar una fase = código + documentación actualizada + entregable verificable.
8. Registrar SIEMPRE el avance en `README.md` y, si aplica, en `architecture.md`.
9. No mezclar cambios de fases distintas en un mismo commit.
10. `security`, `rbac` y `middleware` se implementan **junto con login/users/auth (F2)**, no antes.
11. El cache (`CachePort`) se implementa en **fases posteriores** (primer consumidor: analytics).
12. El manejo de errores se crea **incrementalmente** con cada módulo; no se crea un `errors.py` adelantado.

---

## 6. Restricciones vigentes (activas ahora)

1. ⛔ **Fase 0 = solo inicialización de la app.** No incluir `core/`, `shared/`, Alembic, seed,
   `docker-compose.yml` ni carpetas de módulos.
2. ⛔ **NO crear tests sin autorización explícita** (ni `pytest`, ni `httpx`, ni `tests/`,
   ni `conftest.py`). La Fase 13 está **diferida** y requiere permiso puntual.
   **Excepción vigente:** los tests de integración de F2 (registro, login y RBAC de
   `auth`) están autorizados explícitamente; el resto sigue diferido.
3. ⛔ **NO crear entornos virtuales.** El agente nunca ejecuta `python -m venv` ni crea
   `.venv`/`venv`/`env`. La gestión del entorno de Python es del responsable.
4. ⛔ **NO crear vistas ni triggers** de base de datos.
5. ⛔ **NO reintroducir código Django** (eliminado en Fase 0).
6. ⛔ **NO implementar módulos futuros** antes de su fase.
7. ⛔ **NO comittear secretos**: `.env` está en `.gitignore`; usar `.env.example`.
8. ⛔ **El `.env` reside SIEMPRE en la raíz del repositorio.** El agente nunca crea ni escribe
   el `.env` real; solo mantiene `.env.example`.

---

## 7. Flujo de trabajo

- Implementar → ejecutar/verificar → **explicar detalladamente** los cambios al responsable.
- Escribir los cambios de esquema como migraciones Alembic (desde F2).
- Mantener la documentación sincronizada con el código en el mismo PR/commit.
- Ante ambigüedad, **preguntar** antes de asumir decisiones que afecten arquitectura o datos.

---

## 8. Comandos de referencia

```bash
# Variables de entorno (raíz del repo)
cp .env.example .env

# Dependencias (el entorno de Python lo gestiona el responsable)
cd backend && pip install -r requirements.txt

# Servidor de desarrollo
cd backend && uvicorn app.main:app --reload

# Stack completo (db + api) — desde la RAÍZ
docker compose up -d

# Migraciones (desde Fase 2, dentro de backend/)
cd backend && alembic upgrade head
cd backend && alembic revision --autogenerate -m "descripcion"
```

---

## 9. Registro de reglas

| # | Regla | Fase | Origen |
|---|---|---|---|
| 1 | Documentar cada fase en `README.md` y `architecture.md`; explicar detalladamente los cambios al finalizar | — | Instrucción directa |
| 2 | Mantener este archivo y agregar reglas según las vaya indicando el responsable | — | Instrucción directa |
| 3 | No agregar tests sin autorización explícita (Fase 13 diferida) | — | Instrucción directa |
| 4 | Ignorar vistas/triggers; cálculos de pace y desgaste en la capa application/domain | — | Documentación de persistencia |
| 5 | Comenzar por la capa users/autenticación (F2) | — | Instrucción directa |
| 6 | Una fase por módulo de dominio | — | Instrucción directa |
| 7 | Cada módulo se crea recién en su fase (no pre-crear carpetas) | — | Instrucción directa |
| 8 | Fase 0 = solo inicialización: sin `core/`, sin `shared/` | F0 | Instrucción directa |
| 9 | Alembic se incorpora al desarrollar el primer modelo (F2) | F0 | Instrucción directa |
| 10 | El seed se incorpora con su catálogo (F3 activity_types) | F0 | Instrucción directa |
| 11 | `docker-compose.yml` (PostgreSQL) entra en F1, junto con `core/database` | F0 | Instrucción directa |
| 12 | `requirements.txt` crece por fase (declarar solo lo necesario) | F0 | Instrucción directa |
| 13 | `shared/` entra en F1 (core transversal) | F1 | Instrucción directa |
| 14 | No crear entornos virtuales (`.venv`/`venv`/`env`); el entorno lo gestiona el responsable | — | Instrucción directa |
| 15 | No crear tests sin autorización explícita (endurece la regla 3) | — | Instrucción directa |
| 16 | El `.env` reside siempre en la raíz del repositorio | — | Instrucción directa |
| 17 | El módulo `backend/` incluye su propio `Dockerfile` y `.dockerignore` | F1 | Instrucción directa |
| 18 | `security`, `rbac` y `middleware` se implementan junto con login/users/auth (F2) | F2 | Instrucción directa |
| 19 | El cache (`CachePort`) se implementa en fases posteriores | — | Instrucción directa |
| 20 | El manejo de errores se crea incrementalmente con cada módulo | — | Instrucción directa |
| 21 | Roles `runner`, `admin` y `super_admin`: el registro público crea siempre `runner`; `super_admin` crea `admin`/`runner`; el primer `super_admin` se crea con `scripts/create_super_admin.py` | F2 | Instrucción directa |
| 22 | Todo endpoint declara `response_model` y schema de request; los errores usan el formato uniforme `{"detail": "..."}` | F2 | Instrucción directa |
| 23 | Los DTOs de `application` son `dataclass`; Pydantic se usa solo en `presentation` | F2 | Instrucción directa |
| 24 | Tests de F2 autorizados (registro/login/RBAC) contra PostgreSQL de test (`TEST_DATABASE_URL`); F13 sigue diferida | F2 | Instrucción directa |
| 25 | Los tests se ejecutan con `docker-compose.test.yml` para no crear entornos virtuales locales | F2 | Instrucción directa |
