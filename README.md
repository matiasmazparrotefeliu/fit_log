# FitLog / RunTracker

Plataforma web multi-usuario para atletas y deportistas de resistencia: registro de
entrenamientos, calendario de competencias, control de desgaste de calzado, rutina diaria
de recuperación y seguimiento nutricional.

> **Estado:** Fase 0 completada — inicialización de la aplicación y limpieza del proyecto legacy (Django).

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | **FastAPI** (Python) |
| Arquitectura | **Layered / Clean Architecture** + **Monolito Modular** + **BFF** |
| Persistencia | **PostgreSQL** (SQLAlchemy 2.0 + Alembic) — desde Fase 2 |
| Cache | `CachePort` con implementación in-memory (Redis detrás del mismo puerto, futuro) |
| Autenticación | **JWT** (python-jose) + bcrypt (passlib) + **RBAC** (`runner` / `admin`) |
| Frontend | Next.js + PWA (fase posterior) |

---

## Estructura del repositorio

> En esta fase la aplicación es mínima. La estructura crece **fase por fase**; cada módulo
> de dominio nace recién cuando llega su fase correspondiente.

```
fit_log/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI mínima: GET /health y GET /
│   ├── requirements.txt
│   └── .env.example
├── README.md
├── architecture.md
└── AGENTS.md
```

Fases posteriores incorporan:
- **F1:** `app/core/` (config, database, security, rbac, cache, middleware, errors) + `app/shared/` + `docker-compose.yml`.
- **F2+:** `app/modules/<módulo>/{domain,application,infrastructure,presentation}`.

---

## Puesta en marcha (desarrollo)

### 1. Requisitos
- Python 3.11+ (compatible con 3.10)
- Docker (se usa a partir de la Fase 1, para PostgreSQL)

### 2. Entorno virtual y dependencias
```bash
cd backend
python -m venv .venv
# Windows (Git Bash):
source .venv/Scripts/activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Variables de entorno
```bash
cd backend
cp .env.example .env      # ajustar valores si hace falta
```

### 4. Levantar la API
```bash
cd backend
uvicorn app.main:app --reload
```
- Documentación interactiva: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Endpoints disponibles (Fase 0)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/` | Información de la API |
| GET | `/docs` | Swagger UI |

Los endpoints de dominio se incorporan en las fases siguientes bajo `/api/v1`.

---

## Roadmap por fases

### Base transversal

| Fase | Alcance | Estado |
|---|---|---|
| **F0** | Inicialización de la app: `main.py`, requirements, `.env.example`, limpieza legacy (Django) | ✅ Completada |
| **F1** | `core/` (config, database, security, rbac, cache, middleware, errors) + `shared/` + PostgreSQL (`docker-compose.yml`) | ⏳ Pendiente |

### Una fase por módulo de dominio

| Fase | Módulo | Extra | Estado |
|---|---|---|---|
| **F2** | `auth` (users + RBAC) | Alembic (primer modelo) | ⏳ Pendiente |
| **F3** | `activity_types` | Seed del catálogo | ⏳ Pendiente |
| **F4** | `gear` | — | ⏳ Pendiente |
| **F5** | `workouts` | — | ⏳ Pendiente |
| **F6** | `events` | Catálogo global + `event_distances` (admin) | ⏳ Pendiente |
| **F7** | `participations` | `user_events` | ⏳ Pendiente |
| **F8** | `dailylogs` | — | ⏳ Pendiente |
| **F9** | `nutrition` | `meals` | ⏳ Pendiente |
| **F10** | `goals` | — | ⏳ Pendiente |
| **F11** | `analytics` | BFF / dashboard | ⏳ Pendiente |

### Posteriores

| Fase | Alcance | Estado |
|---|---|---|
| **F12** | Frontend Next.js + PWA | ⏳ Pendiente |
| **F13** | Tests | ⛔ Diferida |

Ver `architecture.md` para capas, modelo de datos y reglas de negocio.
Ver `AGENTS.md` para las reglas de trabajo del proyecto.
