FROM python:3.14-slim

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN pip install --no-cache-dir pipenv \
    && pipenv sync --system

# Create a dedicated non-root user
RUN groupadd --system app \
    && useradd --system --gid app --create-home app

# Copy application files with appropriate ownership
COPY --chown=app:app . .

# Run the application without root privileges
USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]