# Database Schema Overview

Core tables (see SQLAlchemy models in `app/models/`):

- `users`, `user_profiles`
- `rate_calculations`
- `invoices`, `contracts`
- `market_statistics`

## Data Access Layer

Database operations are abstracted through the repository pattern:

- **UserRepository** (`app/repositories/user_repository.py`) - User and profile operations
- **RateRepository** (`app/repositories/rate_repository.py`) - Rate calculation history and management

Repositories provide a clean interface for data access, making it easier to test and maintain the business logic layer.

Migrations are managed by Alembic in `alembic/`.
