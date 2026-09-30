You are an expert senior backend engineer. Build the initial MVP backend for a “fantasy stock market for people” app using Python + FastAPI + PostgreSQL. The goal is to scaffold a production-leaning codebase with clean architecture, migrations, seed data, and core endpoints.

IMPORTANT: This is an MVP. Use VIRTUAL currency only (no real money). Start with ONE category (athletes) but design the schema so other categories (politicians, celebrities, influencers) can be added later without refactoring. Keep the pricing logic simple for now, but design the services layer so that analytics and ML-based pricing can be added later.

Deliverables:

- Create full repo structure, code files, configuration, and documentation.
- Use FastAPI, SQLAlchemy 2.0 style, Alembic migrations, Pydantic v2, python-dotenv or pydantic-settings.
- Provide Docker Compose for Postgres (and optionally adminer/pgadmin).
- Provide simple seed script.
- Provide working API endpoints: health, assets list/detail, portfolio, buy/sell, basic price updates placeholder.
- Build the minimal auth needed for MVP: a simple email+password authentication with hashed passwords (e.g., passlib bcrypt) and JWT auth (python-jose). Keep it simple but real. Protect trading endpoints.
- Include unit tests (minimal but real) for the trading logic (insufficient funds, insufficient shares, idempotency guard).
- Do NOT include any frontend code. Backend only.

High-level concept / requirements:

1. App concept:
   - A fantasy stock market where users trade virtual shares in real-world entities.
   - MVP scope: Athletes only, virtual credits only. Other categories later.

2. Core entities and behaviors:
   - Users have a virtual cash balance (starting balance configurable via env).
   - Assets represent “stocks of people” (start with athletes).
   - Assets have a current price (float/decimal).
   - Users can buy/sell shares of assets.
   - The system tracks:
     - portfolio holdings (shares, avg_cost)
     - transactions (buy/sell events with timestamp and price)
     - price history (timestamped prices)
   - Pricing: for MVP, keep prices static except for a placeholder “update price” endpoint and/or a scheduled simulation method.
   - Later: pricing will be driven by performance stats and sentiment ML—design code to support plugging in analytics.

3. API endpoints required:
   Public:
   - GET /health -> {"status":"ok"}
   - POST /auth/register
   - POST /auth/login -> returns JWT
     Authenticated:
   - GET /me -> user profile + cash balance
   - GET /assets -> list assets with id, name, category, current_price
   - GET /assets/{asset_id} -> detail includes recent price history (last N points)
   - GET /portfolio -> holdings + computed PnL (unrealized) using current prices
   - POST /trade/buy -> body: {asset_id, shares} ; returns updated portfolio position and new cash balance
   - POST /trade/sell -> body: {asset_id, shares} ; returns updated portfolio position and new cash balance
     Admin/dev-only (guard with ENV flag or simple admin user boolean):
   - POST /admin/seed -> seeds a few athletes if DB empty
   - POST /admin/assets/{asset_id}/set_price -> body: {price}
   - POST /admin/assets/update_prices_simulated -> bumps prices using simple random walk (for testing)
     Analytics placeholder:
   - GET /analytics/assets/{asset_id}/indicators -> returns basic computed indicators from price history: - rolling mean (7, 30) - volatility (stddev) - momentum (price change % over window)
     Use pure python/numpy/pandas if needed, but keep it lightweight; it’s OK to implement manually.
     ML placeholder:
   - GET /ml/assets/{asset_id}/forecast -> returns a stub response (later will load a model). For now return:
     {"horizon_days": 7, "predicted_price": <simple extrapolation>, "model": "stub"}
     NOTE: Don’t overbuild. Keep these endpoints functional but minimal.

4. Database schema requirements (Postgres):
   Use Alembic migrations. Tables:
   - users: id (uuid or int), email (unique), username (optional), password_hash, is_admin, cash_balance, created_at
   - assets: id, name, category (enum-like string), current_price, created_at, updated_at
   - portfolio_positions: id, user_id, asset_id, shares (numeric), avg_cost (numeric), updated_at
     unique constraint (user_id, asset_id)
   - transactions: id, user_id, asset_id, side (BUY/SELL), shares, price_per_share, total_value, created_at
   - price_history: id, asset_id, price, created_at (timestamp)
     Consider using NUMERIC for money-like values; if you choose float, be consistent and justify. Prefer Decimal/NUMERIC for correctness.

5. Trading rules (must implement):
   - BUY:
     - total_cost = shares \* current_price
     - reject if shares <= 0
     - reject if user.cash_balance < total_cost
     - update portfolio position:
       - new_shares = old_shares + shares
       - new_avg_cost = weighted average (old_shares*old_avg_cost + shares*current_price) / new_shares
     - decrement user.cash_balance by total_cost
     - create transaction row
   - SELL:
     - reject if shares <= 0
     - reject if no position or position.shares < shares
     - total_proceeds = shares \* current_price
     - decrement position shares; if it becomes 0, delete position or keep with 0 (choose one approach)
     - increment user.cash_balance by total_proceeds
     - create transaction row
   - Must be done in a DB transaction with row-level locking to avoid race conditions.
   - Add a simple idempotency key option:
     - client may send header: Idempotency-Key; store recent keys in a table (trade_requests) to prevent double execution (minimal implementation OK).

6. Analytics:
   - Implement computed fields for portfolio:
     - market_value = shares \* current_price
     - cost_basis = shares \* avg_cost
     - unrealized_pnl = market_value - cost_basis
     - unrealized_pnl_pct = (unrealized_pnl / cost_basis) if cost_basis > 0
   - Add /analytics/assets/{asset_id}/indicators using price_history points.

7. Code quality & architecture:
   - Organize into modules:
     app/
     main.py
     core/ (config, security, logging)
     db/ (session, base)
     models/ (sqlalchemy models)
     schemas/ (pydantic models)
     api/ (routers)
     services/ (business logic: trading, pricing, analytics)
   - Use dependency injection for DB sessions.
   - Include clear error handling with appropriate HTTP codes.
   - Include a README with:
     - setup steps (docker compose, migrations, run server)
     - environment variables
     - how to seed and test
     - endpoints summary
   - Provide a Makefile or simple scripts for common commands (optional but helpful).

8. Environment variables:
   - DATABASE_URL
   - JWT_SECRET, JWT_ALG
   - ACCESS_TOKEN_EXPIRE_MINUTES
   - STARTING_CASH (e.g., 10000)
   - ADMIN_ENABLED (true/false)
   - SEED_ON_STARTUP (optional)
     Use pydantic-settings.

9. Tests:
   - Use pytest.
   - Add tests for:
     - buying reduces cash and increases shares + avg_cost correct
     - selling increases cash and reduces shares
     - insufficient funds prevents buy
     - insufficient shares prevents sell
     - idempotency prevents duplicate trades

Implementation instructions:

- Generate the complete file tree and implement all code.
- Include Alembic config and a first migration that creates tables.
- Ensure everything runs with:
  docker compose up -d
  alembic upgrade head
  uvicorn app.main:app --reload
- Provide a seed method that inserts 5–10 athlete assets (NBA/MLB names ok).
- Don’t add frontend.
- Don’t add real-money payments.
- Keep it easy to extend later for politicians/celebrities and ML pricing.

Output format:

1. Show the final file tree.
2. Provide the content of every created file (code blocks).
3. Provide exact commands to run.
4. Provide brief notes on key design decisions (money numeric type, locking, idempotency).
