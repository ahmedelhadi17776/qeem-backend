# 🔌 API Overview

> **Complete API documentation for Qeem Backend**

## 🌟 Quick Reference

- **Base URL**: `/api/v1`
- **Authentication**: JWT Bearer tokens required for protected endpoints
- **Documentation**: [Complete Authentication API](../qeem-meta/docs/api/auth-endpoints.md)

## 🔑 Authentication Endpoints

### **User Management**

- `POST /auth/register` - Register new user ✅
- `POST /auth/login` - User authentication ✅ (returns access token; refresh flow is planned)
- `GET /auth/me` - Get current user ✅

### **User Profile**

- `PUT /users/profile` - Update user profile ✅

## 🧮 Rate Calculator Endpoints

### **Rate Calculation**

- `POST /rates/calculate` → RateResponse ✅
  ```json
  {
    "minimum_rate": 75.0,
    "competitive_rate": 100.0,
    "premium_rate": 125.0,
    "currency": "EGP",
    "method": "rule_based",
    "rationale": "Based on your experience and project complexity"
  }
  ```

### **Rate History**

- `GET /rates/history` → RateHistoryResponse ✅
  ```json
  {
    "items": [
      {
        "minimum_rate": 75.0,
        "competitive_rate": 100.0,
        "premium_rate": 125.0,
        "currency": "EGP",
        "method": "rule_based",
        "rationale": "Based on your experience and project complexity"
      }
    ]
  }
  ```

## 🏥 Health Check

- `GET /health` - API health status ✅

## 🏗️ Architecture

The API follows a clean architecture pattern with thin controllers:

- **Routers** (`app/api/v1/`) - Handle HTTP requests/responses only
- **Dependencies** (`app/api/deps.py`) - Shared FastAPI dependencies (DB sessions, auth)
- **Services** (`app/services/`) - Business logic and rules
- **Repositories** (`app/repositories/`) - Data access layer
- **Models** (`app/models/`) - SQLAlchemy database models
- **Schemas** (`app/schemas/`) - Pydantic request/response models

All inputs validated via Pydantic models in `app/schemas/`.

## 📈 Market Data Endpoints

- `GET /market/statistics` → Paginated statistics (Redis cached, TTL configurable via `MARKET_CACHE_TTL`) ✅
- `GET /market/trends` → Trend points over a window (Redis cached) ✅

## 🔐 Authentication

All endpoints except registration, login, and health check require JWT authentication:

```http
Authorization: Bearer <your-jwt-token>
```

## 📚 Related Documentation

- [Complete Authentication Documentation](AUTHENTICATION.md)
- [Database Schema](DB_SCHEMA.md)
- [Frontend Integration Guide](../qeem-meta/docs/development/frontend-backend-integration.md)
