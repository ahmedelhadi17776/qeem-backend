# 🚀 Qeem Backend

> **AI-Powered Freelance Rate Calculator for Egyptian Freelancers**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

## 🌟 Overview

Qeem Backend is the powerful API engine behind Egypt's first AI-powered freelance rate calculator. Built with **FastAPI** and **Python 3.12+**, it provides intelligent rate calculations, market insights, and negotiation assistance for Egyptian freelancers.

### 🎯 Key Features

- **🧮 Rule-Based Rate Calculator** - ✅ Smart algorithms considering experience, skills, location, and project complexity
- **🔐 Secure Authentication** - ✅ JWT-based authentication with user registration, login, and profile management
- **👤 User Management** - ✅ Complete user profiles with experience tracking and skill management
- **📊 Rate History** - ✅ Personal calculation history and tracking
- **⚡ High Performance** - ✅ Redis caching, connection pooling, async operations
- **🧪 Comprehensive Testing** - ✅ Unit tests, integration tests, and CI/CD pipeline
- **🤖 ML-Powered Predictions** - 🚧 XGBoost/LightGBM models (planned)
- **💬 AI Negotiation Assistant** - 🚧 GPT-4 powered client negotiation strategies (planned)
- **📊 Market Intelligence** - 🚧 Real-time market data aggregation (planned)
- **📄 Invoice & Contract Management** - 🚧 Complete freelancer business toolkit (planned)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   ML Pipeline   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Scrapy/ML)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌──────┴──────┐
                       │             │
                  ┌────▼────┐   ┌────▼────┐
                  │PostgreSQL│   │ MongoDB │
                  │(Main DB) │   │(ML Data)│
                  └─────────┘   └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **PostgreSQL 14+**
- **Redis 6+**
- **Docker** (optional)

### Installation

1. **Clone and Setup**

   ```bash
   git clone https://github.com/your-org/qeem-backend.git
   cd qeem-backend

   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment**

   ```bash
   # Copy configuration templates
   cp env.example .env
   cp alembic.ini.example alembic.ini

   # Edit configuration files with your values
   ```

3. **Database Setup**

   ```bash
   # Create database and user
   psql -U postgres
   CREATE DATABASE qeem;
   CREATE USER elhadi WITH ENCRYPTED PASSWORD 'test123';
   GRANT ALL PRIVILEGES ON DATABASE qeem TO elhadi;
   \q

   # Prepare Alembic (ensure versions folder exists)
   if not exist alembic\versions mkdir alembic\versions

   # Generate and apply initial schema from models (first-time setup)
   alembic stamp base
   alembic revision --autogenerate -m "initial schema from models"
   alembic upgrade head
   ```

   **Note**: Tables are created via Alembic migrations only. No auto-creation on startup.

4. **Environment Configuration**

   ```bash
   # Copy example environment
   cp example.env .env

   # Edit .env with your settings
   DATABASE_URL=postgresql://elhadi:test123@localhost:5432/qeem
   REDIS_URL=redis://localhost:6379
   JWT_SECRET=your-super-secret-jwt-key-here
   ```

5. **Run the Server**

   ```bash
   # Development
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Production
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### 🐳 Docker Setup

```bash
# Using Docker Compose (recommended)
docker-compose up -d postgres redis
docker-compose up backend

# Or build and run manually
docker build -t qeem-backend .
docker run -p 8000:8000 qeem-backend
```

## 📚 API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 🔑 Key Endpoints

```http
# ✅ Rate Calculation (Implemented)
POST /api/v1/rates/calculate
GET  /api/v1/rates/history

# ✅ Authentication (Implemented)
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me

# ✅ User Management (Implemented)
GET  /api/v1/users/profile
PUT  /api/v1/users/profile

# ✅ Market Data (Implemented - cached via Redis, TTL via MARKET_CACHE_TTL)
GET  /api/v1/market/statistics
GET  /api/v1/market/trends

# 🚧 Negotiation Assistant (Planned)
POST /api/v1/negotiations/analyze
POST /api/v1/negotiations/suggest
```

#### Market Data Examples

```bash
# Statistics (paginated)
curl "http://localhost:8000/api/v1/market/statistics?project_type=web_development&location=Cairo&period_type=weekly&limit=10&offset=0"

# Trends (last 12 weeks)
curl "http://localhost:8000/api/v1/market/trends?project_type=web_development&location=Cairo&period_type=weekly&window=12"
```

Caching: responses are cached using Redis (cache-aside) for 1 hour by default.

## 🔐 Authentication

The API uses JWT-based authentication. Here's how to use it:

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 3. Use Token in Requests

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Calculate Rates (Protected Endpoint)

```bash
curl -X POST "http://localhost:8000/api/v1/rates/calculate" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "web_development",
    "project_complexity": "moderate",
    "estimated_hours": 40,
    "experience_years": 2,
    "skills_count": 3,
    "location": "Cairo, Egypt",
    "client_region": "egypt",
    "urgency": "normal"
  }'
```

## 🌱 Seed Data

Create sample users and rate calculations for development:

```bash
# Run seed data script
python -m scripts.seed_data

# Or use the shell script (Unix/Linux/Mac)
./scripts/seed.sh
```

This creates:

- 3 sample users with different experience levels
- 6 sample rate calculations
- Login credentials: `junior@example.com`, `midlevel@example.com`, `senior@example.com` (password: `password123`)

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -q

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run authentication tests
pytest tests/test_auth.py -v
```

## 🗄️ Database Schema

### Core Models

- **`users`** - ✅ User authentication and basic info
- **`user_profiles`** - ✅ Extended user profile data (experience, skills, bio)
- **`rate_calculations`** - ✅ Rate calculation history and results
- **`market_statistics`** - 🚧 Aggregated market data for ML (planned)
- **`invoices`** - 🚧 Freelancer billing and invoicing (planned)
- **`contracts`** - 🚧 Client agreements and contracts (planned)

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current revision
alembic current
```

## 🔧 Development

### Project Structure

```
qeem-backend/
├── app/
│   ├── api/             # ✅ API layer
│   │   ├── deps.py      # ✅ FastAPI dependencies (DB, auth)
│   │   └── v1/          # ✅ API routes and endpoints
│   │       ├── auth.py  # ✅ Authentication endpoints
│   │       ├── rates.py # ✅ Rate calculation endpoints
│   │       └── users.py # ✅ User management endpoints
│   ├── core/            # ✅ Core application components
│   │   ├── config.py    # ✅ Application configuration
│   │   ├── security.py  # ✅ JWT and password utilities
│   │   └── logging.py   # ✅ Logging configuration
│   ├── db/              # ✅ Database layer
│   │   └── database.py  # ✅ Database session management
│   ├── infra/           # ✅ Infrastructure components
│   │   └── redis.py     # ✅ Redis client factory
│   ├── models/          # ✅ SQLAlchemy database models
│   │   ├── user.py      # ✅ User and profile models
│   │   └── rate_calculation.py # ✅ Rate calculation model
│   ├── repositories/    # ✅ Data access layer
│   │   ├── user_repository.py
│   │   └── rate_repository.py
│   ├── schemas/         # ✅ Pydantic request/response schemas
│   │   ├── auth.py      # ✅ Authentication schemas
│   │   └── rates.py     # ✅ Rate calculation schemas
│   ├── services/        # ✅ Business logic layer
│   │   ├── user_service.py # ✅ User management service
│   │   └── rates.py     # ✅ Rate calculation service
│   └── main.py          # ✅ FastAPI application entry point
├── alembic/             # ✅ Database migrations
├── tests/               # ✅ Comprehensive test suite
│   ├── test_auth.py     # ✅ Authentication tests
│   ├── test_rates_service.py # ✅ Rate service tests
│   └── test_database.py # ✅ Database tests
├── scripts/             # ✅ Development scripts
│   └── seed_data.py     # ✅ Database seeding
├── requirements.txt     # ✅ Python dependencies
└── Dockerfile          # ✅ Container configuration
```

### Code Quality

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint code
flake8 app/ tests/
mypy app/

# Security check
bandit -r app/
```

## 🚀 Deployment

### Production Checklist

- [ ] Set strong JWT secrets (required in non-dev environments)
- [ ] Configure CORS properly
- [ ] Enable HTTPS
- [ ] Set up monitoring (Sentry)
- [ ] Configure rate limiting (optional - requires Redis)
- [ ] Set up database backups
- [ ] Enable connection pooling
- [ ] Configure logging
- [ ] Redis is optional - app works without it (caching/rate limiting disabled)

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
JWT_SECRET=your-secret-key

# Optional
MONGODB_URL=mongodb+srv://...
SENTRY_DSN=https://...
OPENAI_API_KEY=sk-...
```

## 📊 Performance

- **Response Time**: < 100ms for cached calculations
- **Throughput**: 1000+ requests/second
- **Uptime**: 99.9% SLA target
- **Cache Hit Rate**: > 90% for rate calculations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Use conventional commits
- Ensure CI passes

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
