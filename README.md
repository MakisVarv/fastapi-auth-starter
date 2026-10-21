# FastAPI Authentication & Authorization Starter

[![CI](https://github.com/MakisVarv/fastapi-auth-starter/actions/workflows/ci.yml/badge.svg)](https://github.com/MakisVarv/fastapi-auth-starter/actions/workflows/ci.yml)

A reusable **FastAPI backend foundation** for authentication, authorization, and user administration, built with **Clean Architecture** principles. The project separates business rules from HTTP handling, persistence, and external services so that authentication and permission workflows remain maintainable and testable.

**Status:** Core functionality implemented and CI-verified. Designed as a production-oriented starter and learning/reference project—not a publicly deployed, production-operated service.

## Features

### Authentication and account security

- Registration, login, and current-user profile retrieval and updates.
- JWT access tokens with refresh tokens stored in `HttpOnly` cookies.
- Server-side authentication sessions, refresh-token rotation, and replay detection.
- Logout and logout from all sessions.
- Reauthentication and fresh-authentication checks for sensitive operations.
- Password and email changes.
- Forgot-password and reset-password workflows with SMTP email delivery.
- CSRF protection for cookie-based refresh and logout operations.
- Argon2 password hashing.
- Rate limiting backed by Redis, including IP-based limits and normalized-email limits on login and forgot-password requests.

### Authorization and administration

- Role-based access control (RBAC) with a developer-defined permission registry.
- Role hierarchy and target-aware authorization rules.
- Role management, permission assignment/removal, and protection for built-in roles.
- Permission synchronization against the application registry.
- User creation, retrieval, updating, deletion, activation/deactivation, and role assignment.
- User listing with pagination, filtering, searching, and sorting.
- Centralized HTTP error handling and request validation.

## Architecture

The codebase follows Clean Architecture: application use cases coordinate behavior through contracts, while infrastructure provides concrete implementations.

```text
                  HTTP requests
                        |
                        v
             API / FastAPI routes
             schemas + dependencies
                        |
                        v
                Application layer
                use cases + ports
                        |
                        v
                  Domain layer
                entities + rules
                        ^
                        |
        Infrastructure implements application ports
        (SQLAlchemy, JWT, Argon2, SMTP, etc.)
```

At runtime, FastAPI dependencies assemble use cases with their infrastructure adapters. The **dependency direction** stays inward: domain and application rules do not depend on FastAPI routes or SQLAlchemy models.

| Directory             | Responsibility                                                                       |
| --------------------- | ------------------------------------------------------------------------------------ |
| `app/domain/`         | Core entities and business concepts                                                  |
| `app/application/`    | Use cases, ports, and application-level rules                                        |
| `app/infrastructure/` | Database, repositories, Unit of Work, tokens, hashing, mail, and configuration       |
| `app/api/`            | Routes, request/response schemas, dependency composition, and HTTP error translation |
| `alembic/`            | Database schema migrations                                                           |
| `scripts/`            | Database initialization, seeding, and permission synchronization                     |
| `tests/`              | Unit, API, and integration tests                                                     |
| `nginx/`              | Local reverse-proxy configuration                                                    |
| `.github/workflows/`  | Continuous integration                                                               |

**Patterns used:** Dependency Inversion, Repository, Unit of Work, application use cases, explicit dependency composition, and centralized exception translation.

## Technology stack

| Area                | Tools                                       |
| ------------------- | ------------------------------------------- |
| API                 | Python 3.14, FastAPI, Pydantic              |
| Persistence         | PostgreSQL 17, SQLAlchemy, Alembic, psycopg |
| Security            | PyJWT, Argon2, SlowAPI, Redis               |
| Email               | SMTP; Mailpit for local testing             |
| Runtime             | Docker, Docker Compose, Nginx, Uvicorn      |
| Development quality | Pipenv, pytest, Ruff, Black, GitHub Actions |

## Getting started (Docker Compose)

### Prerequisites

- Docker with Docker Compose support.
- An available local port **8000** for the API and **8026** for Mailpit.

### 1. Clone and configure

```bash
git clone https://github.com/MakisVarv/fastapi-auth-starter.git
cd fastapi-auth-starter
cp .env.example .env
```

Edit `.env` before starting. In particular:

- Replace `JWT_SECRET_KEY` and `CSRF_SECRET_KEY` with strong, distinct random values.
- Change `POSTGRES_PASSWORD` from the example value.
- Set a secure `ADMIN_PASSWORD` (at least eight characters) and review `ADMIN_EMAIL`.
- Keep `COOKIE_SECURE=false` **only for local HTTP development**.
- Review `FRONTEND_ORIGIN` and `FRONTEND_RESET_URL` for your environment. This repository does not include a frontend.

`compose.yaml` overrides the database, Redis, and SMTP hosts with their internal service names, so the example `localhost` settings do not need to be changed for the Docker Compose setup.

### 2. Start the services

```bash
docker compose up --build -d
```

Compose starts **PostgreSQL**, **Redis**, **Mailpit**, the **FastAPI application**, and **Nginx**. A one-off initialization service runs Alembic migrations, seeds the built-in roles and administrator, and synchronizes permissions before the API becomes available.

### 3. Open the application

| Service                           | Local URL                          |
| --------------------------------- | ---------------------------------- |
| Interactive API docs (Swagger UI) | http://localhost:8000/docs         |
| OpenAPI schema                    | http://localhost:8000/openapi.json |
| Mailpit inbox                     | http://localhost:8026              |

The API is served through Nginx on `127.0.0.1:8000`. Application routes are under `/api`, including `/api/auth`, `/api/users`, `/api/roles`, and `/api/permissions`.

Use the configured administrator credentials to log in. For password-reset testing, Mailpit captures outgoing email locally; the reset link uses `FRONTEND_RESET_URL`, so a separate frontend would be needed to follow that link through a UI.

### 4. Inspect logs or stop

```bash
docker compose logs -f api
docker compose down
```

`docker compose down` stops and removes containers but keeps the PostgreSQL named volume. To reset database data intentionally, use `docker compose down -v` **with care**, since it removes volumes.

## API and authentication notes

- Pass access tokens to protected endpoints using `Authorization: Bearer <access_token>`.
- Refresh tokens are managed through cookies rather than returned for client-side JavaScript storage.
- Cookie-based refresh and logout requests require the `X-CSRF-TOKEN` header associated with the refresh cookie.
- Permission-protected endpoints enforce both permission requirements and application-level authorization rules.
- See **`/docs`** for the current endpoint schemas, request formats, and responses.

For example, login requests go to `POST /api/auth/login`; user administration routes are under `/api/users`.

## Development, tests, and CI

Install the locked development dependencies with **Python 3.14.4** and Pipenv:

```bash
python -m pip install pipenv
pipenv sync --dev
```

Run quality checks:

```bash
pipenv run ruff check .
pipenv run black --check .
```

Run tests:

```bash
pipenv run pytest
```

**Local test prerequisites:** The application reads its normal settings from `.env`; integration tests read `TEST_DATABASE_URL` from the environment or an optional `.env.test` file. For host-side test execution, supply a **separate, reachable PostgreSQL test database**. The default Docker Compose configuration does **not** publish PostgreSQL's port to the host. Redis should also be available for realistic rate-limiting behavior. Never point integration tests at a database containing data you need to keep.

With an accessible test database and `TEST_DATABASE_URL` configured, migrations can be applied using:

```bash
pipenv run python -m scripts.upgrade_test_db
```

GitHub Actions runs on pushes and pull requests. Its workflow provisions temporary PostgreSQL and Redis services, installs dependencies from `Pipfile.lock`, applies migrations, checks Ruff and Black, and runs pytest. CI supplies configuration through environment variables rather than committing `.env` files.

## Security and deployment scope

This is a **production-oriented foundation**, not a guarantee of production readiness in an arbitrary environment.

- The supplied Compose setup is intended for local development; public deployment requires HTTPS/TLS, secure cookies, appropriate reverse-proxy and network configuration, and properly managed secrets.
- Production operation also needs environment-specific logging/monitoring, backups, availability planning, and deployment procedures.
- Local Mailpit delivery is for development; configure a real SMTP service for deployment.
- Features such as email verification, security audit logging, and a session-management dashboard are intentionally outside this starter's scope.
- The included configuration and permissions should be reviewed against the requirements of any application that reuses this foundation.

## Project purpose

This project demonstrates how to build and test authentication and authorization workflows while keeping business logic independent of frameworks and infrastructure. It is intended to be reused or adapted as a starting point for backend applications—not as a one-size-fits-all identity service.
