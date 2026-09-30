# StarMarket

A fantasy stock market where users trade virtual shares in real-world entities (athletes, and
now real equities/indices), plus an AI-assisted pipeline that turns a plain-language trading
thesis into a backtested, risk-checked, human-approved paper trade. Built with FastAPI,
SQLAlchemy 2.0, PostgreSQL, JWT auth, and a React frontend.

**Everything trades against virtual cash. No real money, no real brokerage, ever.**

## The strategy pipeline

The headline feature: describe a trading thesis in plain language and walk it through a full
pipeline before anything executes.

```
Natural language thesis
  → canonical strategy spec (LLM, via OpenRouter/DeepSeek — always re-validated, never trusted as-is)
  → semantic validation (risk bounds, indicator sanity, rule-tree size limits)
  → instrument resolution (real market data via yfinance for equities)
  → compiler (indicator math + rule-tree evaluation, pure Python, no pandas)
  → backtest (historical simulation — required before anything can go live)
  → risk engine (checked at plan generation, re-checked again at approval time)
  → execution plan (proposed order + risk summary, expires after 24h)
  → human approval  ←── nothing executes without this
  → paper broker (fills through the same row-locked, idempotent trading engine as manual buy/sell)
  → monitoring (every live signal check is logged, approved or not)
```

Example thesis, taken directly from the pipeline's own test fixtures:

> Universe: SPY. Entry: SMA(close,20) crosses_above SMA(close,50) AND VIX < 20.
> Risk: max_portfolio_risk=1%, stop_loss=2%. Execution: MARKET.

Only equities are backed by real data today (via `yfinance`); crypto, prediction markets,
commodities, and yield are wired into the same adapter interface but raise a clear
"not yet supported" error rather than fabricate data — the seam is there for real integrations
later. A strategy can't be activated without a completed backtest on file, and every generated
execution plan sits in `pending_approval` until a human clicks approve or reject — that gate is
never automatic, even for stop-loss/take-profit exits.

## Setup

### 1. Start PostgreSQL

```bash
docker compose up -d
```

Wait a few seconds for Postgres to be ready.

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work with docker-compose)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Seed the database (optional)

```bash
python scripts/seed.py
```

Or use the admin endpoint after creating an admin user (see below).

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

API available at [http://localhost:8000](http://localhost:8000). Docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Environment Variables

| Variable                      | Description                                                                    | Default                                                      |
| ----------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| DATABASE_URL                  | PostgreSQL URL (sync)                                                          | postgresql://postgres:postgres@localhost:5432/starmarket     |
| DATABASE_URL_ASYNC            | Async URL (optional; auto-derived from DATABASE_URL)                           | -                                                            |
| JWT_SECRET                    | Secret for JWT signing                                                         | change-me-in-production                                      |
| JWT_ALGORITHM                 | JWT algorithm                                                                  | HS256                                                        |
| ACCESS_TOKEN_EXPIRE_MINUTES   | Token expiry                                                                   | 30                                                           |
| STARTING_CASH                 | New user cash balance                                                          | 10000                                                        |
| ADMIN_ENABLED                 | Require admin for admin endpoints                                              | true                                                         |
| SEED_ON_STARTUP               | Auto-seed if DB empty                                                          | false                                                        |
| OPENROUTER_API_KEY            | OpenRouter key — **required** for `POST /api/strategies` (NL→spec translation) | -                                                            |
| OPENROUTER_MODEL              | Chat-completions model, non-reasoning mode                                     | deepseek/deepseek-v4-flash-0731                              |
| OPENROUTER_BASE_URL           | OpenRouter API base URL                                                        | [https://openrouter.ai/api/v1](https://openrouter.ai/api/v1) |
| OPENROUTER_TIMEOUT_SECONDS    | LLM request timeout                                                            | 30.0                                                         |
| MARKET_DATA_CACHE_TTL_SECONDS | In-process cache TTL for market data lookups                                   | 60                                                           |

Everything downstream of strategy creation (resolve, backtest, evaluate) only needs real market
data (`yfinance`, no key required) — `OPENROUTER_API_KEY` is the one variable you must set
yourself for the pipeline's first step to work; the rest have working defaults.

## Endpoints

All routes below (except `/health`) are namespaced under `/api` (e.g. `/api/auth/login`) —
this leaves the root path free for the React frontend's client-side routes.

### Public

- `GET /health` - Health check
- `POST /api/auth/register` - Register (email, password, optional username)
- `POST /api/auth/login` - Login, returns JWT

### Authenticated

- `GET /api/me` - User profile + cash balance
- `GET /api/assets` - List assets (id, name, category, current_price)
- `GET /api/assets/{id}` - Asset detail + recent price history
- `GET /api/portfolio` - Holdings + unrealized PnL
- `POST /api/trade/buy` - Body: `{asset_id, shares}`; optional header: `Idempotency-Key`
- `POST /api/trade/sell` - Body: `{asset_id, shares}`; optional header: `Idempotency-Key`
- `POST /api/strategies` - Body: `{thesis_text, name?}`; translates a plain-language trading thesis into a
  strategy spec via an LLM, validates it, and persists it
- `GET /api/strategies`, `GET /api/strategies/{id}` - List/detail (owner-scoped)
- `POST /api/strategies/{id}/resolve` - Resolve universe symbols to real market instruments
- `POST /api/strategies/{id}/backtest` - Body: `{start_date?, end_date?, starting_cash}`
- `POST /api/strategies/{id}/activate`, `POST /api/strategies/{id}/pause`
- `POST /api/strategies/{id}/evaluate` - Check the live signal now; may generate a pending execution plan
- `GET /api/strategies/{id}/execution_plans`, `GET /api/strategies/{id}/runs`
- `POST /api/plans/{id}/approve` - Re-checks risk, then executes a real (paper) trade
- `POST /api/plans/{id}/reject`

### Admin (requires is_admin user + ADMIN_ENABLED)

- `POST /api/admin/seed` - Seed athlete assets if DB empty
- `POST /api/admin/assets/{id}/set_price` - Body: `{price}`
- `POST /api/admin/assets/update_prices_simulated` - Random walk price bumps
- `POST /api/admin/market-data/sync` - Refresh equity prices from live market data
- `POST /api/admin/strategies/monitoring/run` - Evaluate every active strategy's live signal

There is no promote-to-admin endpoint — `is_admin` is only ever set via a manual DB write
(see "Creating an Admin User" below).

### Analytics

- `GET /api/analytics/assets/{id}/indicators` - Rolling mean, volatility, momentum

### ML (stub)

- `GET /api/ml/assets/{id}/forecast` - Stub forecast (linear extrapolation)

## Frontend

A React + Vite + TypeScript + Tailwind app lives in `frontend/`. It needs Node 20.19+ or
22.12+ (Vite 8's Rolldown bundler doesn't support the Node 21.x line).

### Dev mode (fast iteration, two terminals)

```bash
# terminal 1
uvicorn app.main:app --reload

# terminal 2
cd frontend && npm install && npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — Vite's dev server proxies `/api` requests to the backend on
port 8000, so there's no CORS to configure.

### Single-URL demo mode

Build the frontend once, then run only the backend — it serves the built SPA itself:

```bash
cd frontend && npm install && npm run build
cd ..
uvicorn app.main:app
```

Open [http://localhost:8000](http://localhost:8000) — both the app and its API are served from one origin.

## Quick Test

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"secret123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"secret123"}'

# Use the access_token from the response
export TOKEN="<access_token>"

# List assets
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/assets

# Buy shares (use asset_id from list)
curl -X POST http://localhost:8000/api/trade/buy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"<asset_id>","shares":10}'

# Portfolio
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/portfolio
```

### Try the strategy pipeline

Requires `OPENROUTER_API_KEY` set in `.env`. Using the `$TOKEN` from above:

```bash
# Create a strategy from a plain-language thesis
STRATEGY=$(curl -s -X POST http://localhost:8000/api/strategies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"thesis_text":"Universe: SPY. Entry: SMA(close,20) crosses_above SMA(close,50) AND VIX < 20. Risk: max_portfolio_risk=1%, stop_loss=2%. Execution: MARKET."}')
STRATEGY_ID=$(echo "$STRATEGY" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

# Resolve SPY/^VIX to real Asset rows (pulls a live price via yfinance)
curl -s -X POST http://localhost:8000/api/strategies/$STRATEGY_ID/resolve -H "Authorization: Bearer $TOKEN"

# Backtest against real historical data
curl -s -X POST http://localhost:8000/api/strategies/$STRATEGY_ID/backtest \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"start_date":"2024-01-01","end_date":"2025-12-01","starting_cash":10000}'

# Only after a completed backtest:
curl -s -X POST http://localhost:8000/api/strategies/$STRATEGY_ID/activate -H "Authorization: Bearer $TOKEN"

# Check the live signal right now (may generate a pending execution plan)
curl -s -X POST http://localhost:8000/api/strategies/$STRATEGY_ID/evaluate -H "Authorization: Bearer $TOKEN"

# If a plan was generated, list it and approve it (this is what actually places the paper trade)
curl -s http://localhost:8000/api/strategies/$STRATEGY_ID/execution_plans -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/api/plans/<plan_id>/approve -H "Authorization: Bearer $TOKEN"
```

Or just do all of this through the frontend — see [Frontend](#frontend) below.

## Creating an Admin User

Admin users need `is_admin=true`. After registering, update the DB:

```sql
UPDATE users SET is_admin = true WHERE email = 'admin@test.com';
```

Then `POST /api/admin/seed` will work with that user's token, and the Admin page will
appear in the frontend nav for that account.

## Tests

Tests require PostgreSQL to be running (e.g. `docker compose up -d`) and migrations applied:

```bash
docker compose up -d
alembic upgrade head
pytest tests/ -v
```

Tests use the same database with transaction rollback for isolation. Strategy-pipeline tests
mock the LLM client and market-data adapter (deterministic synthetic OHLCV data with a known
SMA crossover) — no test ever calls real OpenRouter or yfinance, so `OPENROUTER_API_KEY` isn't
needed to run the suite.
