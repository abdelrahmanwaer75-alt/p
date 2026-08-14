# Database migrations

The migration source of truth remains `backend/alembic/versions/`. This package-level directory exists as the database architecture boundary; repositories and application startup must not create schema objects directly in production. Run Alembic migrations from the backend directory before starting production services.
