# 🚀 Qeem Backend

> **AI-Powered Freelance Rate Calculator for Egyptian Freelancers**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

## 🌟 Overview

Qeem Backend is the powerful API engine behind Egypt's first AI-powered freelance rate calculator. Built with **FastAPI** and **Python 3.12+**, it provides intelligent rate calculations, market insights, and negotiation assistance for Egyptian freelancers.

### 🎯 Key Features

- **🧮 Rule-Based Rate Calculator** - Smart algorithms considering experience, skills, location, and project complexity
- **🤖 ML-Powered Predictions** - XGBoost/LightGBM models trained on real market data
- **💬 AI Negotiation Assistant** - GPT-4 powered client negotiation strategies
- **📊 Market Intelligence** - Real-time market data aggregation and analysis
- **📄 Invoice & Contract Management** - Complete freelancer business toolkit
- **🔐 Secure Authentication** - JWT-based auth with OAuth integration
- **⚡ High Performance** - Redis caching, connection pooling, async operations

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

   # Run migrations
   alembic upgrade head
   ```

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
# Rate Calculation
POST /api/v1/rates/calculate
GET  /api/v1/rates/history

# Authentication
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh

# User Management
GET  /api/v1/users/profile
PUT  /api/v1/users/profile

# Market Data
GET  /api/v1/market/statistics
GET  /api/v1/market/trends

# Negotiation Assistant
POST /api/v1/negotiations/analyze
POST /api/v1/negotiations/suggest
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -q

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

## 🗄️ Database Schema

### Core Models

- **`users`** - User authentication and basic info
- **`user_profiles`** - Extended user profile data
- **`rate_calculations`** - Rate calculation history and results
- **`market_statistics`** - Aggregated market data for ML
- **`invoices`** - Freelancer billing and invoicing
- **`contracts`** - Client agreements and contracts

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🔧 Development

### Project Structure

```
qeem-backend/
├── app/
│   ├── api/             # API layer
│   │   ├── deps.py      # FastAPI dependencies (DB, auth)
│   │   └── v1/          # API routes and endpoints
│   ├── core/            # Core application components
│   │   ├── config.py    # Application configuration
│   │   ├── security.py  # JWT and password utilities
│   │   └── logging.py   # Logging configuration
│   ├── db/              # Database layer
│   │   └── database.py  # Database session management
│   ├── infra/           # Infrastructure components
│   │   └── redis.py     # Redis client factory
│   ├── models/          # SQLAlchemy database models
│   ├── repositories/    # Data access layer
│   │   ├── user_repository.py
│   │   └── rate_repository.py
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic layer
│   └── main.py          # FastAPI application entry point
├── alembic/             # Database migrations
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── Dockerfile          # Container configuration
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

- [ ] Set strong JWT secrets
- [ ] Configure CORS properly
- [ ] Enable HTTPS
- [ ] Set up monitoring (Sentry)
- [ ] Configure rate limiting
- [ ] Set up database backups
- [ ] Enable connection pooling
- [ ] Configure logging

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
