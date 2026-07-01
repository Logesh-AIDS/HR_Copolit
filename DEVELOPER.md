# AI Interview Platform - Developer Guide & System Architecture (Stage 2)

Welcome to the AI-powered Interview Platform developer guide. This document details the infrastructure, design decisions, database architecture, microservices setup, container orchestration, code styling, and run instructions compiled in Stage 2.

---

## 1. System Architecture & Folder Layout

The platform uses a modular **Domain-Driven Design (DDD)** and **Clean Architecture** layout. Shared utilities are factored into `services/common` to avoid code duplication across services while keeping modules decoupled.

### Folder Structure

```
HR_Copolit/
├── database/                   # Seed and Raw SQL Schema
│   ├── schema.sql              # Postgres database setup script
│   └── seed.sql                # Dev database seed values
├── migrations/                 # Alembic migration scripts
│   ├── versions/               # Automated schema versions
│   └── env.py                  # Migration runner configuration
├── services/
│   ├── common/                 # Shared infrastructure library
│   │   ├── config.py           # Shared settings loader (Pydantic)
│   │   ├── database.py         # SQLAlchemy pooled engine and repos
│   │   ├── redis_client.py     # Caching utility with resilience fallbacks
│   │   ├── exceptions.py       # Centered exceptions and global handlers
│   │   ├── responses.py        # Envelope formatting & pagination models
│   │   ├── middleware.py       # CORS & rate limiting middlewares
│   │   └── logging_config.py   # Structured logging configuration
│   ├── candidate-service/      # Candidate profile ingestion microservice
│   │   ├── app/
│   │   │   ├── adapter/        # DB, parsing, and vector adapters
│   │   │   ├── delivery/       # HTTP controllers and endpoints
│   │   │   ├── domain/         # Pure domain models (Pydantic validation)
│   │   │   └── main.py         # App setup, logs, and routing
│   │   └── Dockerfile          # Production container setup
│   ├── interview-engine/       # Live WebSocket interview conductor
│   │   ├── app/
│   │   │   ├── main.py         # Websocket connection management
│   │   │   ├── state_machine.py# Redis-backed interview session controller
│   │   │   └── prompt_orchestrator.py # AI/mock evaluators wrapper
│   │   └── Dockerfile
│   ├── grading-service/        # Stateless report generator
│   │   ├── app/
│   │   │   └── main.py         # PDF score card construction engine
│   │   └── Dockerfile
│   └── sandbox-runner/         # Code execution sandboxed engine (Rust)
│       ├── Cargo.toml          # Rust dependencies config
│       ├── src/
│       │   └── main.rs         # Subprocess runner with limits
│       └── Dockerfile          # Multi-stage compile with Python runtime
├── tests/                      # Global pytest verification test suites
├── pyproject.toml              # Code formatting rules (Black, Mypy, Isort)
├── .flake8                     # Flake8 style checker rules
├── .pre-commit-config.yaml     # Pre-commit hook pipeline rules
├── docker-compose.yml          # Local container orchestration manifest
└── DEVELOPER.md                # Developer guide
```

---

## 2. Infrastructure Setup & Connection Management

### Database Connection Pooling (`services/common/database.py`)
SQLAlchemy connection pooling is configured with:
- **Pool Size (`DB_POOL_SIZE` = 10)**: Keeps up to 10 persistent connections per process.
- **Max Overflow (`DB_MAX_OVERFLOW` = 10)**: Allows up to 10 additional temporary connections under load.
- **Recycle Time (`DB_POOL_RECYCLE` = 1800s)**: Automatically closes and recreates connections older than 30 minutes to prevent socket timeout exceptions.
- **Get DB Context Generator (`get_db`)**: Implements safe request-scoped lifecycle mapping via FastAPI's dependency injection (`Depends(get_db)`).

### Cache Management (`services/common/redis_client.py`)
- Thread-safe Redis connection pool (`RedisCacheClient`).
- Support for JSON serialization/deserialization on GET/SET.
- **Resilience Fallback**: If Redis crashes or goes offline, operations catch the error, log a warning, and bypass cache checks, keeping the API fully online.

### Database Migrations (Alembic)
The DB uses Alembic for tracking version changes.
- **Create a new migration**:
  ```bash
  python3 -m alembic revision --autogenerate -m "Description of changes"
  ```
- **Apply migrations**:
  ```bash
  python3 -m alembic upgrade head
  ```
- **Rollback a migration**:
  ```bash
  python3 -m alembic downgrade -1
  ```

---

## 3. Configuration & Environment Variables

All settings load dynamically from the environment or `.env` files via Pydantic Settings.

| Variable Name | Default Value | Description |
|---|---|---|
| `ENV` | `development` | App env (`development` / `production` / `testing`) |
| `DEBUG` | `True` | Activates debug log details and tracebacks |
| `DATABASE_URL` | `postgresql://hr_user:hr_password@127.0.0.1:5432/hr_copilot` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis caching connection URL |
| `RATE_LIMIT_RPM` | `60` | Request rate limits per IP per minute |
| `DB_POOL_SIZE` | `10` | SQLAlchemy persistent connection limit |

---

## 4. API Standards & Middleware

### Standard Response Envelope (`services/common/responses.py`)
All API endpoints follow a consistent structure.

**Success Response:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Paginated Listing Response:**
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "total": 120,
    "skip": 0,
    "limit": 10,
    "has_next": true
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": { "client_ip": "127.0.0.1", "rpm_limit": 60 }
  }
}
```

### System Health Probes
Each microservice exposes standard endpoints:
- `GET /health` and `GET /live`: Confirm the process is alive.
- `GET /ready`: Performs resource validations (e.g. tests Postgres/Redis connection and returns `503 Service Unavailable` if down).
- `GET /version`: Returns the build version (`{"version": "1.0.0"}`).

---

## 5. Coding Standards & Local Verification

To maintain code quality, the project uses formatting checks before checking in code.

### 1. Code Formatting & Linting
- **Black**: Format Python code (enforced at 120 characters line-limit).
- **Flake8**: Style guide enforcement.
- **Mypy**: Strict type-checking rules.

To run checks locally:
```bash
# Format code
black .
isort .

# Run linter
flake8 .

# Check types
mypy .
```

### 2. Pre-commit Hooks
Register the pre-commit hooks to automate formatting validation:
```bash
pip install pre-commit
pre-commit install
```

### 3. Run Automated Tests
Execute tests locally with Pytest:
```bash
python3 -m pytest tests/
```

---

## 6. How to Run with Docker Compose

To spin up all databases and microservices locally:

```bash
# Build and launch containers
docker compose up --build -d

# Check running containers
docker compose ps

# Check logs for a specific service
docker compose logs -f candidate-service
```

### Exposed Service Ports
- `candidate-service`: [http://localhost:8000](http://localhost:8000) (Swagger Docs at `/docs`)
- `grading-service`: [http://localhost:8002](http://localhost:8002) (Swagger Docs at `/docs`)
- `interview-engine`: [http://localhost:8003](http://localhost:8003) (Swagger Docs at `/docs`, WS at `/api/v1/interview/ws`)
- `sandbox-runner` (Rust): [http://localhost:8001](http://localhost:8001)
- `qdrant`: [http://localhost:6333](http://localhost:6333) (Dashboard at `/dashboard`)
- `postgres`: port `5432`
- `redis`: port `6379`
