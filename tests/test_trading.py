import pytest
from decimal import Decimal

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_buy_reduces_cash_increases_shares(
    client: AsyncClient, auth_headers: dict, seed_assets: list
):
    """Buying reduces cash and increases shares; avg_cost is correct."""
    asset = seed_assets[0]
    asset_id = asset.id

    # Initial balance
    me_before = await client.get("/api/me", headers=auth_headers)
    cash_before = me_before.json()["cash_balance"]

    # Buy 10 shares at 100
    r = await client.post(
        "/api/trade/buy",
        headers=auth_headers,
        json={"asset_id": asset_id, "shares": 10},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["position"]["shares"] == 10
    assert data["position"]["avg_cost"] == 100
    assert float(data["cash_balance"]) == float(cash_before) - 1000

    # Portfolio shows position
    port = await client.get("/api/portfolio", headers=auth_headers)
    assert len(port.json()["holdings"]) == 1
    assert float(port.json()["holdings"][0]["shares"]) == 10
    assert float(port.json()["holdings"][0]["avg_cost"]) == 100


@pytest.mark.asyncio
async def test_sell_increases_cash_decreases_shares(
    client: AsyncClient, auth_headers: dict, seed_assets: list
):
    """Selling increases cash and reduces shares."""
    asset = seed_assets[0]
    asset_id = asset.id

    await client.post(
        "/api/trade/buy",
        headers=auth_headers,
        json={"asset_id": asset_id, "shares": 10},
    )
    me_after_buy = await client.get("/api/me", headers=auth_headers)
    cash_after_buy = me_after_buy.json()["cash_balance"]

    r = await client.post(
        "/api/trade/sell",
        headers=auth_headers,
        json={"asset_id": asset_id, "shares": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["position"]["shares"] == 5
    assert float(data["cash_balance"]) > float(cash_after_buy)

    port = await client.get("/api/portfolio", headers=auth_headers)
    assert float(port.json()["holdings"][0]["shares"]) == 5


@pytest.mark.asyncio
async def test_insufficient_funds_rejects_buy(
    client: AsyncClient, auth_headers: dict, seed_assets: list
):
    """User with insufficient cash cannot buy."""
    asset = seed_assets[0]
    asset_id = asset.id
    # Try to buy more than we have (STARTING_CASH is 10000, so buy 10000 shares at 100 = 1M)
    r = await client.post(
        "/api/trade/buy",
        headers=auth_headers,
        json={"asset_id": asset_id, "shares": 10001},
    )
    assert r.status_code == 400
    assert "insufficient" in r.json()["detail"].lower() or "funds" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_insufficient_shares_rejects_sell(
    client: AsyncClient, auth_headers: dict, seed_assets: list
):
    """Selling more shares than owned is rejected."""
    asset = seed_assets[0]
    asset_id = asset.id
    await client.post(
        "/api/trade/buy",
        headers=auth_headers,
        json={"asset_id": asset_id, "shares": 5},
    )
    r = await client.post(
        "/api/trade/sell",
        headers=auth_headers,
        json={"asset_id": asset_id, "shares": 10},
    )
    assert r.status_code == 400
    assert "insufficient" in r.json()["detail"].lower() or "shares" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate_trade(
    client: AsyncClient, auth_headers: dict, seed_assets: list
):
    """Same Idempotency-Key sent twice: second request is rejected or returns same result."""
    asset = seed_assets[0]
    asset_id = asset.id
    key = "idem-key-12345"
    headers = {**auth_headers, "Idempotency-Key": key}

    r1 = await client.post(
        "/api/trade/buy",
        headers=headers,
        json={"asset_id": asset_id, "shares": 5},
    )
    assert r1.status_code == 200
    cash1 = r1.json()["cash_balance"]

    r2 = await client.post(
        "/api/trade/buy",
        headers=headers,
        json={"asset_id": asset_id, "shares": 5},
    )
    assert r2.status_code == 409

    # Verify only one buy was executed (cash should not have decreased twice)
    me = await client.get("/api/me", headers=auth_headers)
    assert me.json()["cash_balance"] == cash1
    port = await client.get("/api/portfolio", headers=auth_headers)
    assert float(port.json()["holdings"][0]["shares"]) == 5
