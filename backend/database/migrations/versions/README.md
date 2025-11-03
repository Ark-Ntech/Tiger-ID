# Database Migrations

This directory contains Alembic migration scripts for the Tiger ID database schema.

## Creating Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

## Running Migrations

```bash
cd backend
alembic upgrade head
```

## Rolling Back Migrations

```bash
cd backend
alembic downgrade -1  # Roll back one version
alembic downgrade base  # Roll back to initial state
```

