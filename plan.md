Fantasy Stock Market MVP Backend Implementation Plan

Final File Tree

StarMarket/
├── app/
│ ├── **init**.py
│ ├── main.py
│ ├── core/
│ │ ├── **init**.py
│ │ ├── config.py
│ │ ├── security.py
│ │ └── deps.py
│ ├── db/
│ │ ├── **init**.py
│ │ ├── base.py
│ │ └── session.py
│ ├── models/
│ │ ├── **init**.py
│ │ ├── user.py
│ │ ├── asset.py
│ │ ├── portfolio_position.py
│ │ ├── transaction.py
│ │ ├── price_history.py
│ │ └── trade_request.py
│ ├── schemas/
│ │ ├── **init**.py
│ │ ├── user.py
│ │ ├── asset.py
│ │ ├── portfolio.py
│ │ ├── trade.py
│ │ └── auth.py
│ ├── api/
│ │ ├── **init**.py
│ │ ├── auth.py
│ │ ├── assets.py
│ │ ├── portfolio.py
│ │ ├── trade.py
│ │ ├── admin.py
│ │ ├── analytics.py
│ │ └── ml.py
│ └── services/
│ ├── **init**.py
│ ├── trading.py
│ ├── analytics_service.py
│ └── pricing_service.py
├── alembic/
│ ├── env.py
│ ├── script.py.mako
│ └── versions/
│ └── 001_initial_schema.py
├── tests/
│ ├── **init**.py
│ ├── conftest.py
│ └── test_trading.py
├── scripts/
│ └── seed.py
├── docker-compose.yml
├── Dockerfile (optional, for app container)
├── .env.example
├── .gitignore
├── pyproject.toml or requirements.txt
├── Makefile
└── README.md

Architecture Overview

flowchart TB
subgraph api [API Layer]
auth[api/auth.py]
assets[api/assets.py]
portfolio[api/portfolio.py]
trade[api/trade.py]
admin[api/admin.py]
analytics[api/analytics.py]
ml[api/ml.py]
end

    subgraph services [Services Layer]
        trading[trading.py]
        analytics_svc[analytics_service.py]
        pricing[pricing_service.py]
    end

    subgraph db [Database]
        models[(SQLAlchemy Models)]
    end

    auth --> models
    assets --> models
    portfolio --> services
    trade --> trading
    admin --> models
    analytics --> analytics_svc
    ml --> analytics_svc

    trading --> models
    analytics_svc --> models
    pricing --> models

1. Core Setup

app/core/config.py

Use pydantic-settings with BaseSettings

Load from .env: DATABASE_URL, JWT_SECRET, JWT_ALGORITHM (default HS256), ACCESS_TOKEN_EXPIRE_MINUTES (default 30), STARTING_CASH (default 10000), ADMIN_ENABLED (bool), SEED_ON_STARTUP (bool)

app/core/security.py

hash_password(plain: str) with passlib bcrypt

verify_password(plain, hashed)

create_access_token(data: dict, expires_delta) with python-jose (JWT)

decode_token(token) -> payload

app/core/deps.py

get_db() async generator yielding AsyncSession (SQLAlchemy 2.0 async)

get_current_user(db, token) -> User or 401

get_current_active_user(...) -> User (optional: check active flag if added)

require_admin(user) -> 403 if not admin and ADMIN_ENABLED

get_idempotency_key(request) -> Optional[str] from Idempotency-Key header

2. Database Layer

Connection Strategy

Sync for Alembic (uses psycopg2 via postgresql://)

Async for app (uses asyncpg via postgresql+asyncpg://)

Alembic env.py will use sync engine; app uses create_async_engine + async_sessionmaker

Models (SQLAlchemy 2.0 declarative style)

Model

Key Fields

User

id (UUID), email (unique), username (nullable), password_hash, is_admin (bool), cash_balance (Numeric), created_at

Asset

id (UUID), name, category (String, e.g. "athlete"), current_price (Numeric), created_at, updated_at

PortfolioPosition

id, user_id, asset_id, shares (Numeric), avg_cost (Numeric), updated_at; unique(user_id, asset_id)

Transaction

id, user_id, asset_id, side (Enum BUY/SELL), shares, price_per_share, total_value, created_at

PriceHistory

id, asset_id, price, created_at

TradeRequest

id, idempotency_key (unique), user_id, created_at (for idempotency guard)

Design decision: NUMERIC for cash_balance, current_price, shares, avg_cost, price_per_share, total_value to avoid float rounding errors in financial calculations.

3. Alembic Migration

alembic/versions/001_initial_schema.py

Create all 6 tables with appropriate indexes

Use sa.Numeric(precision=18, scale=6) for money-like columns

Foreign keys with ON DELETE CASCADE where appropriate (e.g., portfolio_positions -> user)

Enum for transaction.side (BUY, SELL)

alembic/env.py

Import Base.metadata and models so Alembic detects them

Use sync create_engine with postgresql:// for migrations

run_migrations_offline() and run_migrations_online() configured

4. API Routers

Router

Path

Endpoints

Auth

Health

/health

GET

None

Auth

/auth

POST /register, POST /login

None

Me

/me

GET

JWT

Assets

/assets

GET (list), GET /{id} (detail + price history)

JWT

Portfolio

/portfolio

GET (holdings + PnL)

JWT

Trade

/trade

POST /buy, POST /sell

JWT + idempotency

Admin

/admin

POST /seed, POST /assets/{id}/set_price, POST /assets/update_prices_simulated

JWT + admin

Analytics

/analytics/assets/{id}/indicators

GET

JWT

ML

/ml/assets/{id}/forecast

GET

JWT

5. Trading Service (Critical Logic)

app/services/trading.py

BUY flow:

Validate shares > 0

Begin DB transaction

Check idempotency: if Idempotency-Key present, lookup trade_requests; if exists for user, return cached response (409 or stored result)

Lock user row: SELECT ... FOR UPDATE

Lock asset row: SELECT ... FOR UPDATE

Fetch current_price, compute total_cost = shares current_price

Reject with 400 if cash_balance < total_cost

Create/update portfolio position (weighted avg cost)

Decrement user.cash_balance

Insert transaction

Insert price_history (or rely on admin endpoint)

Insert trade_request (idempotency_key, user_id)

Commit

SELL flow:

Validate shares > 0

Begin transaction, check idempotency

Lock user, asset, and portfolio_position (if exists)

Reject if no position or position.shares < shares

total_proceeds = shares current_price

Decrement position.shares; if 0, delete row (cleaner than keeping 0)

Increment user.cash_balance

Insert transaction

Insert trade_request

Commit

Row-level locking: Use with_for_update() on User, Asset, and PortfolioPosition in trading service to prevent race conditions.

6. Analytics & ML Placeholders

app/services/analytics_service.py

get_indicators(asset_id, db): Fetch last N price_history points (e.g., 60), compute:

rolling_mean_7, rolling_mean_30

volatility (stddev of returns)

momentum (price change % over last 7 days)

Use pure Python or numpy; avoid heavy pandas if possible.

app/api/ml.py

GET /ml/assets/{asset_id}/forecast:

Stub: fetch last few price points, simple linear extrapolation

Return {"horizon_days": 7, "predicted_price": <float>, "model": "stub"}

7. Admin Endpoints

POST /admin/seed: If assets count == 0, insert 5-10 athletes (e.g., LeBron James, Steph Curry, Mike Trout, etc.) with initial prices. Requires ADMIN_ENABLED and is_admin user.

POST /admin/assets/{id}/set_price: Body {price}; update asset.current_price and append to price_history.

POST /admin/assets/update_prices_simulated: For each asset, apply random walk: new_price = old_price \* (1 + random.uniform(-0.05, 0.05)); update asset and price_history.

8. Docker & Config

docker-compose.yml

Service db: postgres:15-alpine, env POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, port 5432

Service adminer (optional): adminer image, port 8080, depends_on db

.env.example

All required env vars with placeholders

requirements.txt

fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.6
numpy>=1.26.0
pytest>=7.4.0
pytest-asyncio>=0.23.0
httpx>=0.26.0

9. Tests

tests/conftest.py

Async fixtures: test_db (in-memory SQLite or test Postgres), client (TestClient), auth_headers (register + login, get token), seed_assets

Override get_db and app config for tests

tests/test_trading.py

test_buy_reduces_cash_increases_shares – buy, assert cash decreased, shares increased, avg_cost correct

test_sell_increases_cash_decreases_shares – buy then sell, assert cash back up, shares reduced

test_insufficient_funds_rejects_buy – user with 0 cash, assert 400

test_insufficient_shares_rejects_sell – sell more than owned, assert 400

test_idempotency_prevents_duplicate_trade – same Idempotency-Key twice, second returns cached/same result without double-execution

Use pytest-asyncio with async test functions; httpx.AsyncClient against FastAPI app for integration tests.

10. Seed Script

scripts/seed.py

Standalone script: connect to DB, insert 5-10 athlete assets if empty

Names: e.g., LeBron James, Stephen Curry, Kevin Durant, Mike Trout, Shohei Ohtani, Giannis Antetokounmpo, Luka Doncic, Patrick Mahomes, etc.

Can be run via python scripts/seed.py or invoked from POST /admin/seed

11. Makefile

up: docker compose up -d
down: docker compose down
migrate: alembic upgrade head
seed: python scripts/seed.py # or curl POST /admin/seed
run: uvicorn app.main:app --reload
test: pytest tests/ -v

12. README.md

Setup: Docker, migrations, run server

Env vars table

Endpoints summary (copy from prompt)

How to seed and test

Optional: curl examples for register, login, buy, sell

Key Design Decisions Summary

Topic

Decision

Rationale

Money type

NUMERIC(18,6) in DB, Decimal in Python

Avoids float rounding; financial correctness

Locking

Row-level SELECT ... FOR UPDATE on user, asset, position

Prevents concurrent buy/sell race conditions

Idempotency

trade_requests table with unique idempotency_key

Minimal implementation; reject duplicate requests by key

Zero shares

Delete portfolio_position when shares hit 0

Cleaner schema; no orphan 0-share rows

Category

String "athlete" in assets; extensible to politicians, etc.

No enum constraint; add categories later without migration

Async vs sync

Async app, sync Alembic

Standard pattern; Alembic uses sync driver

Commands to Run

cd ~/Documents/StarMarket
docker compose up -d

# wait for Postgres

alembic upgrade head
uvicorn app.main:app --reload

# Optional: curl -X POST http://localhost:8000/admin/seed -H "Authorization: Bearer <admin_token>"

pytest tests/ -v
