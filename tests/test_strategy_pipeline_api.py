import pytest
from httpx import AsyncClient

from app.services.market_data import registry as market_data_registry
from tests.synthetic_data import FakeMarketDataAdapter, build_spy_vix_bars, build_spy_vix_bars_at_crossover


@pytest.mark.asyncio
async def test_full_pipeline_create_resolve_backtest(
    client: AsyncClient, auth_headers: dict, mock_llm, mock_market_data
):
    create = await client.post(
        "/api/strategies",
        headers=auth_headers,
        json={"thesis_text": "Buy SPY when SMA(5) crosses above SMA(10) and VIX is below 20"},
    )
    assert create.status_code == 200, create.text
    strategy = create.json()
    assert strategy["status"] == "draft"
    assert strategy["canonical_spec"]["universe"] == ["SPY"]
    assert strategy["canonical_spec"]["asset_class"] == "equity"
    strategy_id = strategy["id"]

    resolve = await client.post(f"/api/strategies/{strategy_id}/resolve", headers=auth_headers)
    assert resolve.status_code == 200, resolve.text
    resolved = resolve.json()
    assert resolved["status"] == "resolved"
    assert "SPY" in resolved["resolved_universe"]
    assert "^VIX" in resolved["context_symbols"]

    bars = build_spy_vix_bars()["SPY"]
    backtest = await client.post(
        f"/api/strategies/{strategy_id}/backtest",
        headers=auth_headers,
        json={
            "start_date": bars[0].date.isoformat(),
            "end_date": bars[-1].date.isoformat(),
            "starting_cash": 10000.0,
        },
    )
    assert backtest.status_code == 200, backtest.text
    run = backtest.json()
    assert run["status"] == "completed"
    assert run["metrics"]["num_trades"] >= 1

    # cannot activate without... well it IS backtested now, so activation should succeed
    activate = await client.post(f"/api/strategies/{strategy_id}/activate", headers=auth_headers)
    assert activate.status_code == 200
    assert activate.json()["status"] == "active"


@pytest.mark.asyncio
async def test_activate_without_backtest_is_rejected(client: AsyncClient, auth_headers: dict, mock_llm, mock_market_data):
    create = await client.post(
        "/api/strategies", headers=auth_headers, json={"thesis_text": "Buy SPY on SMA crossover"}
    )
    strategy_id = create.json()["id"]
    await client.post(f"/api/strategies/{strategy_id}/resolve", headers=auth_headers)

    activate = await client.post(f"/api/strategies/{strategy_id}/activate", headers=auth_headers)
    assert activate.status_code == 409


@pytest.mark.asyncio
async def test_evaluate_signal_firing_without_backtest_returns_422(
    client: AsyncClient, auth_headers: dict, mock_llm, monkeypatch
):
    """Guardrail: a live signal must never produce an execution plan for a
    strategy that has never been backtested — /evaluate must fail loudly."""
    fake_adapter = FakeMarketDataAdapter(build_spy_vix_bars_at_crossover())
    monkeypatch.setattr(market_data_registry, "get_adapter", lambda asset_class: fake_adapter)

    create = await client.post(
        "/api/strategies", headers=auth_headers, json={"thesis_text": "Buy SPY on SMA crossover"}
    )
    strategy_id = create.json()["id"]
    resolve = await client.post(f"/api/strategies/{strategy_id}/resolve", headers=auth_headers)
    assert resolve.status_code == 200

    evaluate = await client.post(f"/api/strategies/{strategy_id}/evaluate", headers=auth_headers)
    assert evaluate.status_code == 422
    assert "backtest" in evaluate.json()["detail"].lower()


@pytest.mark.asyncio
async def test_strategy_endpoints_are_owner_scoped(client: AsyncClient, auth_headers: dict, mock_llm, mock_market_data):
    create = await client.post(
        "/api/strategies", headers=auth_headers, json={"thesis_text": "Buy SPY on SMA crossover"}
    )
    strategy_id = create.json()["id"]

    await client.post("/api/auth/register", json={"email": "other@test.com", "password": "secret123"})
    login = await client.post("/api/auth/login", json={"email": "other@test.com", "password": "secret123"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(f"/api/strategies/{strategy_id}", headers=other_headers)
    assert resp.status_code == 404
