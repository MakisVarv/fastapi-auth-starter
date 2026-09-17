# FastAPI Authentication & Authorization Backend

> **Status:** In progress

A reusable backend-focused authentication and authorization system built with **FastAPI** to practice production-oriented application structure, explicit dependency boundaries, and maintainable security workflows.

The project is intentionally designed around **Clean Architecture principles** rather than framework-first organization, keeping domain and application logic independent from FastAPI, SQLAlchemy, and other infrastructure concerns.

---

## Overview

This project implements a reusable authentication and authorization backend with a strong emphasis on architecture and separation of concerns.

The current implementation includes:

- User registration
- Login
- Refresh-token flow
- Current-user authentication
- Role and permission domain modeling
- Application-level permission checks
- FastAPI dependency-based authorization infrastructure
- Repository abstractions
- Unit of Work pattern
- SQLAlchemy persistence
- JWT-based token handling
- Centralized application error handling

Authorization is designed so that business rules remain in the application/domain layers while FastAPI is responsible only for request-time composition.

---

## Architecture

The project follows a Clean Architecture style with dependencies pointing inward:

```text
Presentation / FastAPI
        ↓
Application / Use Cases
        ↓
Domain
        ↑
Infrastructure / SQLAlchemy, JWT, Persistence
```

### Domain

Contains framework-independent business concepts such as users, roles, permissions, and repository contracts.

### Application

Contains use cases that coordinate application behavior.

Examples currently include authentication workflows and permission authorization.

### Infrastructure

Contains concrete implementations for external concerns such as:

- SQLAlchemy repositories
- Database sessions
- Unit of Work implementation
- JWT token handling

### Presentation

Contains FastAPI routes and dependency wiring.

FastAPI dependencies are used as adapters between HTTP requests and application use cases rather than as a place for business logic.

---

## Authentication Flow

The authentication layer currently supports the main token lifecycle:

```text
Login
  ↓
credentials validated
  ↓
access token + refresh session
  ↓
authenticated requests
  ↓
access token resolved to current user
  ↓
refresh flow when required
```

The current-user dependency is responsible for request authentication, while application use cases remain independent of FastAPI.

---

## Authorization / RBAC

The project includes a role-based authorization model using users, roles, and permissions.

The authorization flow is separated into two parts:

```text
Authentication
get_current_user
      ↓
Authenticated User
      ↓
Authorization
require_permission(...)
      ↓
RequirePermission use case
      ↓
Role / Permission domain logic
```

A configurable FastAPI dependency factory has been added so future protected endpoints can declare required permissions without embedding RBAC logic inside route functions.

Conceptually:

```python
dependencies=[Depends(require_permission("users:update"))]
```

The permission dependency is implemented, while route-level permission usage will be introduced when management endpoints requiring RBAC are added.

---

## Architectural Patterns

This project currently applies:

- **Clean Architecture principles**
- **Dependency Inversion**
- **Repository Pattern**
- **Unit of Work Pattern**
- **Dependency Injection / composition through FastAPI**
- **Application Use Cases**
- **Domain-oriented entities and contracts**
- **Centralized error handling**

The goal is not to introduce patterns for their own sake, but to keep business rules testable and independent from persistence and framework details.

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- PyJWT
- Alembic

### Architecture

- Clean Architecture
- Repository Pattern
- Unit of Work
- Dependency Inversion
- FastAPI dependency composition

---

## Current Project Focus

The project is still under active development.

Current work is focused on completing the reusable authentication/authorization foundation and keeping the implementation consistent across:

- authentication
- refresh-session handling
- role and permission modeling
- authorization boundaries
- persistence
- API error behavior
- framework-to-application composition

Only implemented or actively integrated functionality is documented here. The README will be expanded further as the backend reaches a stable completion milestone.

---

## Purpose

This project is primarily a backend architecture and engineering exercise.

Its purpose is to demonstrate how authentication and authorization logic can be implemented while keeping:

- domain rules independent from FastAPI
- persistence behind abstractions
- database transactions explicit
- authentication separate from authorization
- route handlers thin
- infrastructure replaceable
- application behavior organized around use cases

The same frontend-facing authentication contract can later be consumed by a React/TypeScript client without coupling the frontend to the internal backend architecture.

---
