# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OrderRun-BE is a FastAPI-based matching platform backend for errand/delivery services. The system follows a **document-first engineering methodology** (Harness Engineering) where documentation drives code changes, not the other way around.

**Core Flow**: User creates Proposal → Runners submit Offers → Orderer accepts Offer → Mission execution → Payment settlement

## Critical: Document-First Workflow

**BEFORE writing any code, you MUST:**
1. Check `ARCHITECTURE.md` for system overview
2. Look for related design docs in `docs/design-docs/`
3. Look for product specs in `docs/product-specs/`
4. Check active execution plans in `docs/exec-plans/active/`
5. If making structural changes, create a plan document FIRST in `docs/exec-plans/active/`

**File naming**: Execution plans use `YYYY-MM-DD-short-title.md` format

**Key principle**: Documentation → Plan → Code → Verification → Update docs

See `docs/HARNESS_ENGINEERING.md` for complete methodology.

## Technology Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI
- **Database**: MySQL 8.x
- **ORM**: SQLAlchemy 2.x
- **Validation**: Pydantic 2.x
- **Auth**: JWT with phone verification (migrated from OAuth)
- **Migration**: Alembic migrations in `alembic/`

## Development Commands

### Environment Setup

```bash
# First time setup
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

# Re-entering environment
source .venv/bin/activate
```

**Note**: This project uses `pyproject.toml` for dependency management, not `requirements.txt`.

### Running the Application

```bash
# Development server with auto-reload
python -m app.main

# Or via uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode (via settings)
# Set APP_DEBUG=false in .env first
python -m app.main
```

**Environment**: Copy `.env.example` to `.env` and configure required variables (database, JWT secret, etc.)

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_user_auth_integration.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test function
pytest tests/test_user_auth_integration.py::test_phone_verification_flow
```

**Test structure**: Integration tests are in `tests/` directory using pytest-asyncio. Tests use `conftest.py` for shared fixtures.

### Database

```bash
# This project uses Alembic migrations for FastAPI schema changes

# Initialize database (using docker-compose)
docker-compose up -d

# Existing staging databases should be baselined once
alembic stamp 0001_baseline

# Apply new migrations
alembic upgrade head
```

**Important**: `flyway_schema_history` may exist from the legacy Java stack, but FastAPI uses Alembic's `alembic_version`.

### Code Quality

```bash
# This project does not currently have linting/formatting configured
# No pytest-cov, ruff, black, or mypy setup yet
```

## Architecture Overview

### Directory Structure

```
app/
├── main.py              # FastAPI app entry point
├── core/
│   ├── config.py        # Pydantic Settings from environment
│   ├── database.py      # SQLAlchemy session management
│   ├── security.py      # JWT token generation/validation
│   ├── phone.py         # Phone verification utilities
│   └── exceptions.py    # Custom exception handlers
├── models/              # SQLAlchemy ORM models (domain entities)
├── schemas/             # Pydantic request/response schemas
├── api/v1/              # FastAPI routers (endpoints)
├── services/            # Business logic layer
└── templates/           # HTML email templates (Jinja2)
```

**Dependency flow**: `api → services → models` with `schemas` for data validation

### Core Domain Entities

The system has 5 main aggregates:

1. **User**: Authentication via phone verification, profile, admin status
2. **Proposal**: Errand request with budget, category, status (`draft`, `open`, `matched`, `closed`, `cancelled`)
3. **Offer**: Runner's proposal for a Proposal with price, ETA
4. **Mission**: Accepted offer execution (not fully implemented yet)
5. **Payment**: Payment tracking for proposals/missions (partially implemented)

**Key relationships**:
- One User can create many Proposals (as Orderer)
- One User can submit many Offers (as Runner)
- One Proposal has many Offers
- One accepted Offer becomes one Mission

See `docs/architecture/orderrun-domain-model.md` for detailed domain model.

### API Structure

All API routes are under `/api/v1/` prefix:

- `/api/v1/auth/*` - Phone verification, SMS code, login, refresh
- `/api/v1/users/*` - User profile management
- `/api/v1/terms/*` - Terms agreement tracking
- `/api/v1/proposals/*` - Proposal CRUD and listing
- `/api/v1/offers/*` - Offer submission and management
- `/api/v1/notifications/*` - Push notification management
- `/api/v1/admin/*` - Admin-only endpoints

**API docs**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

### Authentication & Authorization

**Current implementation**: Phone-based verification
- User registers with phone number → receives SMS code → verifies code → gets JWT tokens
- Access token: 60 min expiration
- Refresh token: 7 days expiration
- Previous OAuth (Kakao/Apple) code may still exist but is deprecated

**Admin endpoints**: Require `is_admin=true` flag on User model

### Configuration Management

All config is loaded via Pydantic Settings from environment variables:
- Database connection: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`
- JWT: `JWT_SECRET`, `JWT_ALGORITHM`
- Server: `SERVER_HOST`, `SERVER_PORT`
- Optional: SMTP, FCM, OAuth credentials

See `app/core/config.py` for all available settings.

## Common Patterns

### Database Sessions

```python
from app.core.database import get_db

# In API endpoints, use dependency injection
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

### Authentication

```python
from app.core.security import get_current_user

@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user
```

### Error Handling

Custom exceptions are defined in `app/core/exceptions.py`. Use standard FastAPI `HTTPException` or custom handlers registered in `main.py`.

## Working with This Codebase

### Before Making Changes

1. **Check existing documentation**:
   - `ARCHITECTURE.md` - System map
   - `docs/design-docs/` - Technical decisions
   - `docs/product-specs/` - Feature requirements
   - `docs/exec-plans/tech-debt-tracker.md` - Known issues

2. **For new features**:
   - Create product spec in `docs/product-specs/`
   - Create execution plan in `docs/exec-plans/active/`
   - Include verification criteria
   - Then implement code

3. **For structural changes**:
   - Write design doc in `docs/design-docs/`
   - Update `ARCHITECTURE.md` if needed
   - Create execution plan
   - Implement incrementally

### After Making Changes

1. Update related documentation:
   - Execution plan status
   - Design docs if architecture changed
   - `docs/generated/db-schema.md` if models changed

2. Verify changes:
   - Run relevant tests
   - Manual testing if no test coverage
   - Document verification method in exec plan

3. Move completed plans:
   - From `docs/exec-plans/active/` to `docs/exec-plans/completed/`
   - Record any follow-up work in tech debt tracker

### Testing Guidelines

- Write integration tests for API endpoints in `tests/`
- Use `conftest.py` fixtures for test database and client
- Test both success and error cases
- Currently no requirement for 100% coverage

## Important Constraints

1. **Alembic migrations**: Use Alembic for FastAPI schema changes
2. **Phone verification only**: OAuth code exists but is deprecated
3. **MySQL only**: Tests, staging, and production all use MySQL
4. **Baseline first**: Existing staging databases should be stamped to `0001_baseline` before new migrations
5. **Document first**: Code changes without documentation will be rejected
6. **No MySQL ENUM types**: DB 컬럼에 MySQL ENUM 타입을 사용하지 않는다. 대신 `VARCHAR`를 사용한다. SQLAlchemy 모델에서도 `Enum(PythonEnum)`을 컬럼 타입으로 사용하지 않고 `String(n)`을 사용한다. Python 열거형은 애플리케이션 레이어에서만 사용한다. (이유: ENUM은 값 추가 시 ALTER TABLE이 필요하고, 마이그레이션이 복잡해지며, MySQL 버전별 동작 차이가 있다.)

## Git Workflow

- Main branch: `main`
- Current feature branch: `feat/user-api`
- Create feature branches from `main`
- Use descriptive commit messages linking to execution plans when applicable

## Common Tasks

### Adding a new API endpoint

1. Create schema in `app/schemas/`
2. Create service logic in `app/services/`
3. Create router in `app/api/v1/`
4. Register router in `app/main.py`
5. Write integration test in `tests/`

### Adding a new domain model

1. Create SQLAlchemy model in `app/models/`
2. Create an Alembic revision
3. Run `alembic upgrade head`
4. Update `docs/generated/db-schema.md`
5. Create corresponding Pydantic schemas

### Debugging

- Check logs from uvicorn output
- Use FastAPI's automatic `/docs` for API testing
- Set `APP_DEBUG=true` in `.env` for detailed error messages
- Test database connection with provided `scripts/init-db.sql`

## Key Documentation Files

Must read before major work:
- `AGENTS.md` - Agent working principles
- `ARCHITECTURE.md` - System map
- `docs/HARNESS_ENGINEERING.md` - Document-driven methodology
- `docs/DIRECTORY_STRUCTURE.md` - Where things belong
- `docs/QUALITY_SCORE.md` - Quality standards
- `docs/SECURITY.md` - Security requirements
- `docs/RELIABILITY.md` - Reliability requirements

## Notes for Future Claude Instances

- This project follows a **strict document-first approach** - always check docs before coding
- Execution plans are temporary and move to `completed/` when done
- Design docs and product specs are permanent reference material
- When uncertain, ask the user rather than making assumptions
- Small, verifiable changes are preferred over large refactors
- Reuse existing patterns before creating new abstractions
- Link code changes to documentation when committing
