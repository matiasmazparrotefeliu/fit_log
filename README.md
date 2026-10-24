# FitLog / RunTracker

Plataforma web multi-usuario para atletas y deportistas de resistencia: registro de
entrenamientos, calendario de competencias, control de desgaste de calzado, rutina diaria
de recuperación y seguimiento nutricional.

> **Estado:** Fase 2 completada — módulo `auth` (registro, login JWT, perfil y RBAC
> `runner`/`admin`/`super_admin`), Alembic con la migración inicial de `users`, script de
> bootstrap del primer `super_admin` y suite de tests de integración contra PostgreSQL.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | **FastAPI** (Python) |
| Arquitectura | **Layered / Clean Architecture** + **Monolito Modular** + **BFF** |
| Persistencia | **PostgreSQL** (SQLAlchemy 2.0 + Alembic) |
| Cache | `CachePort` (fases posteriores) |
| Autenticación | **JWT** + **RBAC** (`runner` / `admin` / `super_admin`) — Fase 2 |
| Contenedores | Docker / docker-compose |
| Frontend | Next.js + PWA (fase posterior) |

---

## Estructura del repositorio

> La estructura crece **fase por fase**. Cada módulo de dominio nace recién cuando llega su fase.

```
fit_log/
├── .env.example                 # variables de entorno (SIEMPRE en la raíz)
├── docker-compose.yml           # stack: db (PostgreSQL) + api (build ./backend)
├── docker-compose.test.yml      # override para ejecutar la suite de tests en Docker
├── .gitignore
├── README.md
├── architecture.md
├── AGENTS.md
└── backend/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py              # composition root (settings + CORS + /api/v1)
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py        # Settings (lee .env de la raíz)
    │   │   ├── database.py      # engine + Base + get_db
    │   │   ├── security.py      # bcrypt + JWT (F2)
    │   │   ├── rbac.py          # Principal + require_role (F2)
    │   │   └── middleware.py    # CORS (F2)
    │   ├── shared/
    │   │   ├── __init__.py
    │   │   ├── base_entity.py   # mixin UUID PK + created_at
    │   │   ├── unit_of_work.py
    │   │   └── pagination.py
    │   └── modules/
    │       └── auth/            # F2
    │           ├── domain/      # entidades, puertos, errores
    │           ├── application/ # DTOs (dataclass) + casos de uso
    │           ├── infrastructure/  # modelo ORM + repositorio SQLAlchemy
    │           └── presentation/    # schemas Pydantic + routers
    ├── alembic/                 # migraciones (F2)
    │   ├── env.py
    │   └── versions/0001_create_users.py
    ├── alembic.ini
    ├── scripts/
    │   └── create_super_admin.py  # bootstrap idempotente
    ├── tests/                   # F2 (integración)
    │   ├── conftest.py
    │   └── integration/
    ├── pytest.ini
    ├── requirements.txt
    ├── Dockerfile
    └── .dockerignore
```

Las fases siguientes agregan `app/modules/<módulo>/{domain,application,infrastructure,presentation}`.
El módulo `auth` ya incluye las cuatro capas y sirve de referencia para los demás.

---

## Puesta en marcha (desarrollo)

### 1. Requisitos
- Python 3.11+ (compatible con 3.10)
- Docker + Docker Compose

### 2. Variables de entorno (raíz del repo)
```bash
cp .env.example .env      # ajustar valores si hace falta
```

### 3. Opción A — Stack completo con Docker (db + api)
```bash
# desde la raíz del repositorio
docker compose up -d --build
```
- API: http://localhost:8000/docs
- PostgreSQL: puerto `${POSTGRES_PORT:-5432}`

### 4. Opción B — API local + PostgreSQL en Docker
```bash
# desde la raíz: solo la base de datos
docker compose up -d db

cd backend
pip install -r requirements.txt
alembic upgrade head          # crea el esquema (F2+)
uvicorn app.main:app --reload
```

### 5. Migraciones (Alembic)
```bash
cd backend
alembic upgrade head                              # aplicar migraciones
alembic revision --autogenerate -m "descripcion"  # nueva migración
alembic check                                     # verificar que modelos y BD coinciden
```

La primera migración es `0001_create_users` y crea la tabla `users` con:
PK UUID (`gen_random_uuid()`), `email` único, `password_hash`, `full_name`,
`role` con `CHECK (role IN ('runner','admin','super_admin'))`, `birth_date`,
`weight_kg` y `created_at` (`TIMESTAMPTZ`).

### 6. Bootstrap del primer `super_admin`
El registro público **siempre** crea `runner`. Los usuarios `admin`/`runner` los crea un
`super_admin` vía `POST /api/v1/users`. El primer `super_admin` se crea con el script:

```bash
cd backend
python -m scripts.create_super_admin \
  --email superadmin@fitlog.local \
  --password 'ChangeMe123!' \
  --full-name 'Super Admin'
```

También acepta `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD` y `SUPER_ADMIN_FULL_NAME`.
Es **idempotente**: si el email ya existe no lo duplica (y lo promueve a `super_admin` si hacía falta).

### 7. Tests (F2)
La suite usa una base PostgreSQL separada (`TEST_DATABASE_URL`, por defecto `fitlog_test`)
que se crea automáticamente si no existe.

```bash
# Opción recomendada (no requiere entorno Python local):
# desde la raíz, con la db levantada
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api

# Opción local (si ya tenés las dependencias instaladas):
cd backend
pytest -v
```

Cobertura actual: registro, login/JWT, `/users/me` (GET/PATCH), RBAC de `/users`
(`runner`/`admin` → 403, `super_admin` → 200/201), duplicados y validaciones.

---

## Endpoints disponibles (Fase 2)

### Sistema
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/` | Información de la API |
| GET | `/docs` | Swagger UI |

### Auth / Users (`/api/v1`)
| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | `/auth/register` | Público | Registro; crea siempre `runner` → **201** |
| POST | `/auth/login` | Público | Login `{email, password}` → JWT → **200** |
| GET | `/users/me` | Autenticado | Perfil propio → **200** |
| PATCH | `/users/me` | Autenticado | Actualiza `full_name`, `birth_date`, `weight_kg` → **200** |
| GET | `/users` | `super_admin` | Lista paginada (`page`, `size`) → **200** |
| POST | `/users` | `super_admin` | Crea `admin`/`runner` → **201** |

Códigos de error: **401** credenciales/token inválidos, **403** permisos insuficientes,
**409** email duplicado, **422** validación. Todos los endpoints declaran `response_model`
y esquemas de request; los errores usan `{"detail": "..."}`.

Los endpoints de dominio restantes se incorporan bajo `/api/v1` en las fases siguientes.

---

## Roadmap por fases

### Base transversal

| Fase | Alcance | Estado |
|---|---|---|
| **F0** | Inicialización de la app + limpieza legacy (Django) | ✅ Completada |
| **F1** | `core` (config, database) + `shared` + PostgreSQL (Docker) + `Dockerfile` | ✅ Completada |
| **F2** | `auth` (users + JWT + RBAC) + Alembic + tests de integración | ✅ Completada |

### Una fase por módulo de dominio

| Fase | Módulo | Extra | Estado |
|---|---|---|---|
| **F3** | `activity_types` | Seed del catálogo | ⏳ Pendiente |
| **F4** | `gear` | — | ⏳ Pendiente |
| **F5** | `workouts` | — | ⏳ Pendiente |
| **F6** | `events` | Catálogo global + `event_distances` (admin) | ⏳ Pendiente |
| **F7** | `participations` | `user_events` | ⏳ Pendiente |
| **F8** | `dailylogs` | — | ⏳ Pendiente |
| **F9** | `nutrition` | `meals` | ⏳ Pendiente |
| **F10** | `goals` | — | ⏳ Pendiente |
| **F11** | `analytics` | BFF / dashboard (+ `CachePort`) | ⏳ Pendiente |

### Posteriores

| Fase | Alcance | Estado |
|---|---|---|
| **F12** | Frontend Next.js + PWA | ⏳ Pendiente |
| **F13** | Tests | ⛔ Diferida |

Ver `architecture.md` para capas, modelo de datos y reglas de negocio.
Ver `AGENTS.md` para las reglas de trabajo del proyecto.
