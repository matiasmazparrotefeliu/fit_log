# Arquitectura — FitLog / RunTracker

Documento técnico de la arquitectura de la aplicación. Complementa a `README.md`.

---

## 1. Estilo arquitectónico

**Arquitectura en Capas Decoplada (Layered / Clean Architecture)** bajo **API-First**,
implementada como **Monolito Modular (Modular Monolith)** con patrón **BFF**
(Backend-For-Frontend) en el módulo `analytics`.

Se descarta el enfoque de microservicios en esta etapa para evitar sobreingeniería, pero se
mantiene una **separación estricta por módulos de dominio**, de modo que cada uno pueda
extraerse a un microservicio en el futuro sin reescribir la lógica de negocio.

### Capacidades transversales de la capa de API
- CORS
- Autenticación (JWT)
- Rate limiting
- Manejo uniforme de errores

---

## 2. Diagrama de arquitectura global

```
                                  [ CLIENTES ]
            ┌─────────────────────────────────────────────────────┐
            │   Mobile First Web App (React / Next.js + PWA)      │
            └──────────────────────────┬──────────────────────────┘
                                       │ HTTPS / JSON (JWT)
                                       ▼
                             [ CAPA DE API / GATEWAY ]
            ┌─────────────────────────────────────────────────────┐
            │           CORS / Auth Middleware / Rate Limit       │
            └──────────────────────────┬──────────────────────────┘
                                       │
                                       ▼
                         [ MONOLITO MODULAR BACKEND ]
            ┌─────────────────────────────────────────────────────┐
            │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
            │  │ Auth & User  │  │   Workouts   │  │   Gear    │  │
            │  └──────────────┘  └──────────────┘  └───────────┘  │
            │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
            │  │    Events    │  │  Nutrition   │  │ Analytics │  │
            │  └──────────────┘  └──────────────┘  └───────────┘  │
            └──────────────────────────┬──────────────────────────┘
                                       │
                                       ▼
                       [ CAPA DE PERSISTENCIA Y CACHE ]
            ┌──────────────────────────┬──────────────────────────┐
            │ PostgreSQL (Relacional)  │ Redis (Sesiones/Cache)   │
            └──────────────────────────┴──────────────────────────┘
```

> En esta iteración el cache arranca **en memoria** detrás de `CachePort`; Redis se conecta
> luego tras el mismo puerto, sin cambios en el dominio.

### Convenciones de repositorio, configuración y empaquetado

- **Layout:** el backend vive en `backend/`; los artefactos de infraestructura
  (`docker-compose.yml`, `.env.example`, `.gitignore`, documentación) viven en la **raíz**.
- **Configuración:** el `.env` reside **siempre en la raíz** del repositorio. `core/config.py`
  lo resuelve con ruta absoluta (`PROJECT_ROOT = parents[3]`), independiente del cwd.
- **Empaquetado:** `backend/Dockerfile` (+ `backend/.dockerignore`) construye la imagen de la API;
  `docker-compose.yml` (raíz) define los servicios `db` (PostgreSQL) y `api` (build `./backend`).
  Dentro de la red de Docker, la API apunta a la DB con host `db` (no `localhost`).
- **Módulos:** cada módulo de dominio se crea **únicamente al llegar a su fase**.

---

## 3. Regla de dependencia (obligatoria)

```
presentation  ──►  application  ──►  domain  ◄──  infrastructure
(routers,           (casos de         (entidades,      (SQLAlchemy, repos,
 schemas/pydantic)   uso/servicios)    ports)           cache, JWT)
```

| Capa | Contenido | Permitido importar |
|---|---|---|
| `domain` | Entidades, reglas de negocio puras, interfaces (**ports**), errores de dominio | Nada de FastAPI/SQLAlchemy |
| `application` | Casos de uso que orquestan el dominio | Solo `domain` |
| `infrastructure` | Implementa los ports (repositorios SQLAlchemy, cache, JWT) | `domain` (+ `core`) |
| `presentation` | Routers FastAPI + schemas Pydantic; traduce HTTP ↔ casos de uso | `application`, `domain` |

**Reglas clave:**
- El flujo es unidireccional: `presentation → application → domain`.
- `infrastructure` **implementa** las interfaces definidas en `domain` (inversión de dependencias).
- **No hay joins cruzados entre módulos**: la comunicación entre módulos se hace a través de
  interfaces de `application`, nunca accediendo directamente a las tablas de otro módulo.

---

## 4. Módulos de dominio

| Módulo | Responsabilidad | Reqs. funcionales |
|---|---|---|
| `auth` | Registro, login (JWT), perfil, RBAC (`runner`/`admin`/`super_admin`) | RF-01 |
| `activity_types` | Catálogo de tipos de actividad | — |
| `gear` | Calzado, desgaste acumulado y alertas de reemplazo | RF-02 |
| `workouts` | Sesiones de entrenamiento; pace y RPE | RF-03 |
| `events` | Catálogo global de eventos y distancias (**solo admin** escribe) | RF-04 (catálogo) |
| `participations` | `user_events`: inscripción, estado y resultados del atleta | RF-04 |
| `dailylogs` | Check-in diario de recuperación | RF-05 |
| `nutrition` | Comidas y resumen de macronutrientes | RF-06 |
| `goals` | Metas y objetivos del usuario | — |
| `analytics` | **BFF**: dashboard agregado para el frontend | Transversal |

Cada módulo contiene las 4 capas: `domain/`, `application/`, `infrastructure/`, `presentation/`.

---

## 5. Modelo de datos (PostgreSQL, 3FN)

Tipos nativos usados: **UUID** (PK), **TIMESTAMPTZ**, **DATE**, **TIME**, **INTERVAL**, **NUMERIC**.
Mapeo SQLAlchemy: `UUID(as_uuid=True)`, `DateTime(timezone=True)`, `Interval`, `Numeric(p,s)`.
`gen_random_uuid()` como default (built-in en PostgreSQL 13+).

### Principios
- **RBAC**: `users.role` (`runner` | `admin`) habilita la gestión del catálogo global.
- **Separación catálogo / participación**: `events` + `event_distances` (global) vs `user_events` (individual).
- **Aislamiento multi-tenant**: salvo el catálogo público (`events`, `event_distances`, `activity_types`),
  todas las tablas se asocian y aíslan por `user_id`.
- **Integridad referencial**: PK UUID no predecible; `ON DELETE CASCADE` / `SET NULL` según corresponda.

### DER conceptual

```
                       ┌─────────────────┐
                       │      USERS      │ (role: admin / runner)
                       └────────┬────────┘
                                │
   ┌────────────────┬───────────┼───────────┬────────────────┬────────────────┐
   │ (1)            │ (1)       │ (1)       │ (1)            │ (1)            │ (1)
   ▼ (N)            ▼ (N)       ▼ (N)       ▼ (N)            ▼ (N)            ▼ (N)
┌───────┐      ┌──────────┐  ┌─────────┐  ┌────────────┐   ┌─────────┐      ┌────────┐
│ GEAR  │      │ WORKOUTS │  │ EVENTS  │  │ DAILY_LOGS │   │  MEALS  │      │  GOALS │
└───┬───┘      └────▲─────┘  └────┬────┘  └────────────┘   └─────────┘      └────────┘
    │               │             │ (1)
    │               │             ▼ (N)
    │               │     ┌─────────────────┐
    │               │     │ EVENT_DISTANCES │
    │               │     └────────┬────────┘
    │ (0..N)        │              │ (1)
    └───────┐       │ (0..N)       ▼ (N)
            ▼       │       ┌─────────────┐
          ┌─────────┴───────┤ USER_EVENTS │
          │ (0..1)   (0..1) └─────────────┘
```

### Tablas

#### `users`
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK, `gen_random_uuid()` |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(100) | NOT NULL |
| role | VARCHAR(20) | NOT NULL, default `runner`, CHECK (`runner`,`admin`) |
| birth_date | DATE | Nullable |
| weight_kg | NUMERIC(5,2) | Nullable |
| created_at | TIMESTAMPTZ | default `CURRENT_TIMESTAMP` |

#### `gear`
`id` UUID PK · `user_id` UUID NOT NULL → users CASCADE · `brand` VARCHAR(50) NOT NULL ·
`model` VARCHAR(100) NOT NULL · `purchase_date` DATE · `initial_distance_km` NUMERIC(6,2) default 0.00 ·
`max_distance_km` NUMERIC(6,2) default 800.00 · `is_active` BOOLEAN default TRUE · `created_at` TIMESTAMPTZ.

#### `activity_types`
`id` SERIAL PK · `name` VARCHAR(50) NOT NULL UNIQUE · `category` VARCHAR(30) NOT NULL.
Seed: Rodaje Suave, Intervalos / Pasadas, Tempo / Umbral, Tirada Larga (Running);
Gimnasio / Fuerza (Fuerza); Movilidad / Estiramientos (Movilidad).

#### `workouts`
`id` UUID PK · `user_id` UUID NOT NULL → users CASCADE · `workout_date` DATE NOT NULL ·
`activity_type_id` INT NOT NULL → activity_types · `gear_id` UUID → gear SET NULL ·
`distance_km` NUMERIC(6,2) · `duration_interval` INTERVAL NOT NULL · `avg_pace_sec_km` INT ·
`elevation_gain_m` INT default 0 · `avg_hr` INT · `cadence` INT · `rpe` INT CHECK (1..10) ·
`weather_summary` VARCHAR(50) · `notes` TEXT · `created_at` TIMESTAMPTZ.

#### `events`
`id` UUID PK · `created_by_user_id` UUID → users SET NULL · `name` VARCHAR(150) NOT NULL ·
`event_type` VARCHAR(50) NOT NULL CHECK (`race`,`group_workout`,`training_camp`,`virtual_race`) ·
`category` VARCHAR(50) · `city` VARCHAR(100) · `country` VARCHAR(100) default 'Argentina' ·
`location_details` TEXT · `event_date` DATE NOT NULL · `start_time` TIME · `official_website_url` TEXT ·
`registration_open_date` DATE · `registration_close_date` DATE · `is_active` BOOLEAN default TRUE ·
`created_at` TIMESTAMPTZ.

#### `event_distances`
`id` SERIAL PK · `event_id` UUID NOT NULL → events CASCADE · `distance_km` NUMERIC(5,2) NOT NULL ·
`name` VARCHAR(50).

#### `user_events`
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL → users CASCADE |
| event_id | UUID | NOT NULL → events CASCADE |
| event_distance_id | INT | → event_distances SET NULL |
| status | VARCHAR(20) | default `planned`, CHECK (`planned`,`registered`,`completed`,`dns`,`dnf`) |
| registration_status | VARCHAR(30) | default `pendiente` |
| registration_fee | NUMERIC(10,2) | Nullable |
| bib_number | VARCHAR(30) | Nullable |
| target_time | INTERVAL | Nullable |
| official_time | INTERVAL | Nullable |
| chip_time | INTERVAL | Nullable |
| overall_rank | INT | Nullable |
| category_rank | INT | Nullable |
| gear_id | UUID | → gear SET NULL |
| workout_id | UUID | → workouts SET NULL |
| notes | TEXT | Nullable |
| created_at | TIMESTAMPTZ | default CURRENT_TIMESTAMP |
| — | UNIQUE | `(user_id, event_id, event_distance_id)` |

#### `daily_logs`
`id` UUID PK · `user_id` UUID NOT NULL → users CASCADE · `log_date` DATE NOT NULL ·
`sleep_hours` NUMERIC(4,2) · `sleep_quality` INT CHECK (1..5) · `resting_hr` INT ·
`fatigue_level` INT CHECK (1..10) · `water_intake_ml` INT default 0 ·
`stretching_completed` BOOLEAN default FALSE · `notes` TEXT · **UNIQUE (`user_id`,`log_date`)**.

#### `meals`
`id` UUID PK · `user_id` UUID NOT NULL → users CASCADE · `meal_date` DATE NOT NULL ·
`meal_type` VARCHAR(30) NOT NULL CHECK (`Pre-workout`,`Desayuno`,`Almuerzo`,`Post-workout`,`Cena`,`Snack`) ·
`time_of_day` TIME · `description` TEXT NOT NULL · `calories` INT · `carbs_g` NUMERIC(6,2) ·
`protein_g` NUMERIC(6,2) · `fat_g` NUMERIC(6,2) · `created_at` TIMESTAMPTZ.

#### `goals`
`id` UUID PK · `user_id` UUID NOT NULL → users CASCADE · `title` VARCHAR(100) NOT NULL ·
`target_date` DATE · `target_distance_km` NUMERIC(6,2) · `is_completed` BOOLEAN default FALSE ·
`created_at` TIMESTAMPTZ.

### Índices estratégicos

```sql
CREATE INDEX idx_events_date_city      ON events (event_date ASC, city);
CREATE INDEX idx_events_active         ON events (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_user_events_user      ON user_events (user_id, status);
CREATE INDEX idx_user_events_event     ON user_events (event_id);
CREATE INDEX idx_workouts_user_date    ON workouts (user_id, workout_date DESC);
CREATE INDEX idx_workouts_gear         ON workouts (gear_id) WHERE gear_id IS NOT NULL;
CREATE INDEX idx_daily_logs_user_date  ON daily_logs (user_id, log_date DESC);
CREATE INDEX idx_meals_user_date       ON meals (user_id, meal_date DESC);
```

### Vistas y triggers — POSTERGADOS

No se implementan por ahora:
- `v_gear_usage` → reemplazada por cálculo en `gear/application` (suma de workouts; carreras vía port).
- `trg_calculate_pace` → reemplazado por cálculo de `avg_pace_sec_km` en `workouts/application`.

---

## 6. Reglas de negocio y su ubicación

| Regla | Módulo | Capa |
|---|---|---|
| Hash de contraseña | auth | infrastructure |
| Emisión / validación JWT | auth | infrastructure / core |
| RBAC `require_role` | core/rbac | presentation |
| Pace (seg/km) | workouts | application |
| Desgaste de calzado | gear | application |
| Alerta de reemplazo (80% / 100%) | gear | domain |
| Countdown a evento | participations | domain |
| Unicidad de check-in diario | dailylogs | application |
| Unicidad de inscripción | participations | application |
| Resumen nutricional | nutrition | application |
| Cumplimiento de metas | goals | domain |
| Volumen semanal / mensual | analytics | application |

---

## 7. API (prefijo `/api/v1`)

```
POST   /auth/register                 POST /auth/login  → JWT
GET    /users/me                      PATCH /users/me
GET    /users                         (super_admin)
POST   /users                         (super_admin; crea admin/runner)

GET/POST/PATCH/DELETE  /gear          (+ GET /gear/{id}/wear)
GET/POST/PATCH/DELETE  /workouts
GET                    /activity-types
GET/POST/PATCH/DELETE  /events         (escritura: admin)  (+ /events/{id}/distances)
GET/POST/PATCH/DELETE  /participations (user_events)
GET/POST/PATCH         /daily-logs
GET/POST/PATCH/DELETE  /meals          (+ GET /meals/summary?date=)
GET/POST/PATCH/DELETE  /goals
GET                    /dashboard      (BFF Analytics)
```

- Los endpoints privados resuelven `current_user` desde el JWT y filtran por `user_id`.
- **Roles:** `runner` (registro público), `admin` (creado por `super_admin`, escritura de
  catálogos como `/events`) y `super_admin` (gestiona usuarios vía `/users`). El registro
  público **nunca** permite elegir rol. El primer `super_admin` se crea con
  `python -m scripts.create_super_admin` (bootstrap idempotente).
- Las mutaciones de `/events` exigen rol **`admin`** (o superior).
- Todos los endpoints declaran `response_model` de éxito y esquemas Pydantic de request;
  los errores usan el formato uniforme `{"detail": "..."}` con códigos 401/403/409/422.
- Documentación OpenAPI/Swagger en `/docs`.

---

## 8. Requerimientos no funcionales

- **Seguridad:** aislamiento estricto por `user_id` decodificado del JWT; RBAC verificado en mutaciones de catálogo.
- **Rendimiento:** dashboard y resúmenes < 500 ms (índices + `CachePort`).
- **Integridad:** UUID no predecible; cascadas `CASCADE`/`SET NULL` según spec; restricciones UNIQUE.
- **Evolución:** ports por módulo permiten migrar a microservicios y a Redis sin tocar el dominio.
- **Mobile-first:** el frontend (Fase 11) prioriza la carga rápida de entrenamiento/comida.

---

## 9. Fases de desarrollo

### Reglas del proceso por fases
- **Una fase por módulo de dominio.** No se agrupan varios módulos en una misma fase.
- **Cada módulo se crea únicamente al llegar a su fase.** Está prohibido pre-crear carpetas de módulos futuros.
- La **base transversal** (inicialización + `core` + `shared`) se construye antes que cualquier módulo.
- `requirements.txt` **crece por fase** (solo se declara lo que cada fase necesita).
- La **primera fase funcional es F2 (auth/users)**.
- `security`, `rbac` y `middleware` se implementan **junto con login/users/auth (F2)**.
- El cache (`CachePort`) se implementa en **fases posteriores**.
- El **manejo de errores es incremental**: se crea a medida que avanza la aplicación.

### Base transversal

| Fase | Alcance | Estado |
|---|---|---|
| **F0** | **Inicialización de la app**: `main.py`, `requirements.txt`, `.env.example` (raíz), limpieza legacy (Django). Sin `core`, `shared`, Alembic, seed, docker ni módulos. | ✅ |
| **F1** | `core/` (`config`, `database`) + `shared/` (base_entity, unit_of_work, pagination) + `docker-compose.yml` (db+api) + `backend/Dockerfile` | ✅ |
| **F2** | `auth` (users + JWT + RBAC) + `security`/`rbac`/`middleware` + Alembic (migración `0001_create_users`) + bootstrap `super_admin` + tests de integración | ✅ |

### Detalle de la Fase 2 (`auth`)

- **Capas:** `domain` (entidad `User`, `UserRole`, puerto `UserRepository`, errores),
  `application` (DTOs `dataclass` + casos de uso), `infrastructure` (`UserModel` +
  `SqlAlchemyUserRepository`, único punto con SQLAlchemy) y `presentation` (schemas
  Pydantic + routers). La capa `application` no importa FastAPI.
- **Seguridad:** contraseñas con **bcrypt** (`passlib`); JWT firmado con
  `SECRET_KEY`/`ALGORITHM` que incluye `sub`, `role`, `iat` y `exp`.
- **RBAC:** `get_current_principal` (claim-based) y `require_role(...)` en `core/rbac.py`.
  La resolución del usuario completo contra la BD vive en `auth/presentation/dependencies.py`.
- **CORS:** configurado en `core/middleware.py` desde `CORS_ORIGINS`; el rate limit
  queda para una fase posterior (junto con `CachePort`).
- **Roles:** `runner`, `admin`, **`super_admin`** (desvío aprobado de la spec original).
  Registro público → siempre `runner`; `super_admin` crea `admin`/`runner` vía `POST /users`;
  el primer `super_admin` se crea con `scripts/create_super_admin.py` (idempotente).
- **Errores:** incrementales por módulo (`auth/domain/errors.py`), traducidos a HTTP en
  `presentation`; formato uniforme `{"detail": "..."}`.
- **Tests:** suite de integración autorizada para F2 (`backend/tests`) contra PostgreSQL
  de test (`TEST_DATABASE_URL`), ejecutable en Docker con `docker-compose.test.yml`.
  La Fase 13 (tests generales) sigue diferida.

### Una fase por módulo

| Fase | Módulo | Extra de la fase |
|---|---|---|
| **F3** | `activity_types` | Seed del catálogo |
| **F4** | `gear` | — |
| **F5** | `workouts` | — |
| **F6** | `events` | incluye `event_distances` (admin) |
| **F7** | `participations` | `user_events` |
| **F8** | `dailylogs` | — |
| **F9** | `nutrition` | `meals` |
| **F10** | `goals` | — |
| **F11** | `analytics` | BFF / dashboard |

### Posteriores

| Fase | Alcance |
|---|---|
| **F12** | Frontend Next.js + PWA |
| **F13** | Tests (**diferida**, no bloquea ninguna fase) |

### Orden de dependencias

```
F0 Init ──► F1 Core+Shared ──► F2 Auth (RBAC) ──► F3 ActivityTypes ──► F4 Gear
                                                                          │
   F12 Frontend ◄── F11 Analytics ──┬────────────────────────────────► F5 Workouts
                                    │                                       │
                                    │                                       ▼
                                    │                                F6 Events
                                    │                                       │
                                    │                                       ▼
                                    │                             F7 Participations
                                    │                                       │
                                    └── F10 Goals ◄── F9 Nutrition ◄── F8 DailyLogs
```

- **F2 (users/auth) es la primera fase funcional** y habilita el RBAC para la fase de eventos.
- F13 (tests) está **diferida** y no bloquea ninguna fase.
