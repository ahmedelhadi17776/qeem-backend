# === Builder stage: compile dependencies, build wheels ===
FROM python:3.12-alpine3.22 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install build tools & libraries needed for compiling dependencies
RUN apk add --no-cache \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    musl-dev \
    linux-headers \
    postgresql-dev

COPY requirements.txt ./

# Build wheels for dependencies so runtime stage doesn't need compilers
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

COPY app ./app

# === Runtime / final stage ===
FROM python:3.12-alpine3.22 AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Runtime libraries required by compiled dependencies (e.g., psycopg2)
RUN apk add --no-cache \
    postgresql-libs \
    libstdc++ \
    libffi \
    openssl \
    curl

# Copy built wheels & install production dependencies only
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt

# Copy only application code into runtime image
COPY --from=builder /app/app ./app

ENV UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

EXPOSE 8000

RUN adduser -D -g '' appuser \
    && chown -R appuser:appuser /app

USER appuser

# Basic container healthcheck hitting the health endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${UVICORN_PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${UVICORN_HOST} --port ${UVICORN_PORT} --proxy-headers"]
