import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.deps import get_db
from app.db.session import async_session_maker
from app.models.asset import Asset
from app.models.price_history import PriceHistory
from app.services import llm_client
from app.services.market_data import registry as market_data_registry
from tests.synthetic_data import CANNED_STRATEGY_SPEC, FakeMarketDataAdapter, build_spy_vix_bars


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_session():
    """Provide a session. commit() is patched to flush only; we rollback after test."""
    async with async_session_maker() as session:
        real_commit = session.commit
        async def fake_commit():
            await session.flush()
        session.commit = fake_commit
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client):
    """Register a user, login, return auth headers."""
    await client.post(
        "/api/auth/register",
        json={"email": "test@test.com", "password": "secret123"},
    )
    r = await client.post(
        "/api/auth/login",
        json={"email": "test@test.com", "password": "secret123"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seed_assets(client, auth_headers, db_session):
    """Seed assets via direct DB insert (transaction will be rolled back)."""
    assets_data = [
        ("LeBron James", 100),
        ("Stephen Curry", 80),
    ]
    assets = []
    for name, price in assets_data:
        a = Asset(name=name, category="athlete", current_price=Decimal(str(price)))
        db_session.add(a)
    await db_session.flush()
    result = await db_session.execute(select(Asset))
    assets = list(result.scalars().all())
    for asset in assets:
        ph = PriceHistory(asset_id=asset.id, price=asset.current_price)
        db_session.add(ph)
    await db_session.flush()
    return assets


@pytest.fixture
def mock_llm(monkeypatch):
    """Patches llm_client.generate_structured so strategy tests never hit real
    OpenRouter. Must patch the module attribute (not a `from...import`-bound
    name) since strategy_service.py calls it as `llm_client.generate_structured(...)`."""

    async def fake_generate_structured(system_prompt, user_prompt, json_schema, schema_name="response"):
        return CANNED_STRATEGY_SPEC

    monkeypatch.setattr(llm_client, "generate_structured", fake_generate_structured)
    return CANNED_STRATEGY_SPEC


@pytest.fixture
def mock_market_data(monkeypatch):
    """Patches market_data.registry.get_adapter with a fake adapter serving a
    deterministic, hand-built OHLCV series with a known SMA crossover — no
    network calls, no yfinance/flakiness."""
    fake_adapter = FakeMarketDataAdapter(build_spy_vix_bars())
    monkeypatch.setattr(market_data_registry, "get_adapter", lambda asset_class: fake_adapter)
    return fake_adapter
