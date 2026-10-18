#!/bin/sh

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding initial roles and administrator..."
python -m scripts.seed

echo "Synchronizing permissions..."
python -m scripts.sync_permissions

echo "Database initialization completed successfully."