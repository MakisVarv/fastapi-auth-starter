# FastAPI Auth Starter

A reusable FastAPI authentication and RBAC backend starter built with a pragmatic Clean/Hexagonal architecture.

The project reimplements the same mature authentication, authorization, session, and role-management behavior as a previous Flask backend, while focusing on stronger dependency boundaries and framework-independent application logic.

## Planned Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- Psycopg
- Pytest
- Pipenv

## Architecture Goals

- Clean/Hexagonal dependency boundaries
- Framework-independent domain and application layers
- Repository ports with SQLAlchemy adapters
- Unit of Work transaction management
- Dependency Injection
- JWT authentication with secure refresh-token handling
- RBAC and role hierarchy
- Compatibility with the existing React Auth/Admin frontend starter

## Status

Initial project setup and architecture foundation in progress.
