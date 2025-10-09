# ML Setup for Docker

## Why ML Libraries Are Excluded from Docker Build

The main Docker image excludes ML libraries (XGBoost, LightGBM, scikit-learn) because:

1. **Alpine Linux Compatibility**: XGBoost 2.0.3 fails to compile on Alpine due to `mmap64` not being available in musl libc
2. **Image Size**: ML libraries significantly increase image size (500MB+)
3. **Optional Feature**: Backend works perfectly without ML using rule-based calculations
4. **Separation of Concerns**: ML model serving can be done separately

## Options for ML-Enabled Deployment

### Option 1: Install ML Libraries After Container Start (Development)

```bash
docker exec -it your-container-name /bin/sh
pip install -r requirements-ml.txt
```

### Option 2: Use Debian-Based Image (Production)

Create `Dockerfile.ml`:

```dockerfile
# Use Debian instead of Alpine for ML support
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./

# Build all wheels including ML
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements-ml.txt

# Runtime stage
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY --from=builder /wheels /wheels
COPY requirements.txt requirements-ml.txt /app/
RUN pip install --no-cache-dir --find-links=/wheels \
    -r /app/requirements.txt \
    -r /app/requirements-ml.txt

# Copy app
COPY app ./app

ENV UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_WORKERS=1

EXPOSE 8000

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${UVICORN_PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${UVICORN_HOST} --port ${UVICORN_PORT} --workers ${UVICORN_WORKERS} --proxy-headers --log-level info"]
```

Build with:

```bash
docker build -f Dockerfile.ml -t qeem-backend:ml .
```

### Option 3: Separate ML Service (Microservices Architecture)

Run ML predictions in a separate container:

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    build: .
    image: qeem-backend:latest
    environment:
      - ENABLE_ML_PREDICTIONS=false
    # ... other config

  ml-service:
    build:
      context: ../qeem-ml
    image: qeem-ml:latest
    # Expose ML API for backend to call
```

### Option 4: Pre-trained Model Only (Lightweight)

If you have a pre-trained model, you can use `joblib` to load it without XGBoost:

```dockerfile
# Add only joblib and numpy (much smaller)
RUN pip install joblib numpy
```

Then modify `ml_prediction.py` to use ONNX runtime or a lighter format.

## Recommended Approach

For **development**: Use default Dockerfile (no ML), backend uses rule-based calculations

For **production**:

- **Option 2** (Debian-based image) if you need ML in the same container
- **Option 3** (Separate ML service) for better scalability

## Testing Without ML

The backend gracefully falls back to rule-based calculations:

```python
# In app/services/rates.py
if use_ml and settings.enable_ml_predictions:
    ml_service = get_ml_service()
    if ml_service and ml_service.is_available():
        try:
            result = ml_service.predict_rate(payload)
        except Exception:
            # Falls back to rule-based
            pass

# Always has a fallback
if not result:
    # Rule-based calculation
    result = calculate_tiers(...)
```

## Current Docker Build

The current `Dockerfile` builds successfully **without** ML libraries:

- ✅ Fast build (~2 minutes)
- ✅ Small image size (~150MB)
- ✅ All core features work
- ✅ Rule-based rate calculations
- ⚠️ No ML predictions (gracefully disabled)

---

**Status**: Docker builds successfully. ML is optional. Use `requirements-ml.txt` if needed.
