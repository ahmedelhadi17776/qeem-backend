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

## Migrations (Alembic)

- Migrations are managed by Alembic in `alembic/`.
- Initial schema migration has been generated and applied, creating all core tables above.
- Indexes created include:
  - `ix_market_stats_pt_loc_period_date` on `market_statistics(project_type, location, period_type, date)`
  - Standard primary key and helpful single-column indexes (e.g., `users.email`, `contracts.contract_number`, `invoices.invoice_number`).

### Common commands

```bash
# Generate migration from current models
alembic revision --autogenerate -m "initial schema from models"

# Apply latest migration(s)
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Show current DB revision
alembic current
```
