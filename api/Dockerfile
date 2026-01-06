# Python Agenta Service Dockerfile
# Evaluation and tracing backend (FastAPI)
# Build context should be upstream/agenta/api/

FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl gnupg2 lsb-release && \
    echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
    gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg && \
    apt-get update && \
    apt-get install -y postgresql-client-16 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install pip and poetry
RUN pip install --upgrade pip && pip install poetry

# Copy pyproject.toml and install dependencies
COPY ./pyproject.toml /app/

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# Copy application code
COPY ./oss /app/oss/
COPY ./entrypoints /app/entrypoints/

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Cloud Run expects PORT env var, default to 8000
ENV PORT=8000

EXPOSE 8000

# Start FastAPI server using uvicorn
# The app is defined in entrypoints/routers.py, not oss/src/main.py
CMD ["sh", "-c", "uvicorn entrypoints.routers:app --host 0.0.0.0 --port ${PORT:-8000}"]
