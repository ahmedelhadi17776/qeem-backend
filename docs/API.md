# API Overview

- Base: `/api/v1`
- Health: `GET /health`
- Auth: `POST /api/v1/auth/login` (stub)
- Rates:
  - `POST /api/v1/rates/calculate` → RateResponse { minimum_rate, competitive_rate, premium_rate, currency, method }
  - `GET /api/v1/rates/history` → { items: [] } (stub)

## Architecture

The API follows a clean architecture pattern with thin controllers:

- **Routers** (`app/api/v1/`) - Handle HTTP requests/responses only
- **Dependencies** (`app/api/deps.py`) - Shared FastAPI dependencies (DB sessions, auth)
- **Services** (`app/services/`) - Business logic and rules
- **Repositories** (`app/repositories/`) - Data access layer
- **Models** (`app/models/`) - SQLAlchemy database models
- **Schemas** (`app/schemas/`) - Pydantic request/response models

All inputs validated via Pydantic models in `app/schemas/`.
