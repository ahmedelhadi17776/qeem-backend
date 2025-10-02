# API Overview

- Base: `/api/v1`
- Health: `GET /health`
- Auth: `POST /api/v1/auth/login` (stub)
- Rates:
  - `POST /api/v1/rates/calculate` → RateResponse { minimum_rate, competitive_rate, premium_rate, currency, method }
  - `GET /api/v1/rates/history` → { items: [] } (stub)

Responses are JSON. All inputs validated via Pydantic models in `app/schemas/`.
