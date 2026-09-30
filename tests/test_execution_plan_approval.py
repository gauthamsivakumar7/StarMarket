from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest_run import BacktestRun, BacktestStatus
from app.models.execution_plan import ExecutionPlan, ExecutionPlanStatus, ExecutionPlanTrigger
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy_spec import StrategySpec
from app.services import execution_plan_service
from tests.synthetic_data import build_spy_vix_bars


async def _create_resolved_backtested_strategy(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
) -> Strategy:
    bars = build_spy_vix_bars()["SPY"]
    create = await client.post(
        "/api/strategies", headers=auth_headers, json={"thesis_text": "Buy SPY on SMA crossover"}
    )
    strategy_id = create.json()["id"]
    await client.post(f"/api/strategies/{strategy_id}/resolve", headers=auth_headers)
    await client.post(
        f"/api/strategies/{strategy_id}/backtest",
        headers=auth_headers,
        json={
            "start_date": bars[0].date.isoformat(),
            "end_date": bars[-1].date.isoformat(),
            "starting_cash": 10000.0,
        },
    )
    result = await db_session.execute(select(Strategy).where(Strategy.id == strategy_id))
    return result.scalar_one()


async def _generate_pending_plan(db_session: AsyncSession, strategy: Strategy, user: User) -> ExecutionPlan:
    spec = StrategySpec.model_validate(strategy.canonical_spec)
    backtest_result = await db_session.execute(
        select(BacktestRun)
        .where(BacktestRun.strategy_id == strategy.id, BacktestRun.status == BacktestStatus.COMPLETED)
        .order_by(BacktestRun.id.desc())
        .limit(1)
    )
    backtest_run = backtest_result.scalar_one()
    orders = await execution_plan_service.build_proposed_orders(db_session, user, spec, "entry")
    assert orders, "expected a non-empty proposed order for this test's fixture data"
    return await execution_plan_service.generate_plan(
        db_session, strategy, backtest_run, user, spec, orders, ExecutionPlanTrigger.USER_MANUAL
    )


@pytest.mark.asyncio
async def test_approve_plan_executes_through_real_trading_engine(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mock_llm, mock_market_data
):
    strategy = await _create_resolved_backtested_strategy(client, db_session, auth_headers)
    user_result = await db_session.execute(select(User).where(User.id == strategy.user_id))
    user = user_result.scalar_one()
    cash_before = user.cash_balance

    plan = await _generate_pending_plan(db_session, strategy, user)
    assert plan.status == ExecutionPlanStatus.PENDING_APPROVAL

    approve = await client.post(f"/api/plans/{plan.id}/approve", headers=auth_headers)
    assert approve.status_code == 200, approve.text
    body = approve.json()
    assert body["status"] == "executed"
    assert body["fills"][0]["status"] == "filled"

    portfolio = await client.get("/api/portfolio", headers=auth_headers)
    holdings = portfolio.json()["holdings"]
    assert len(holdings) == 1
    assert float(holdings[0]["shares"]) > 0

    me = await client.get("/api/me", headers=auth_headers)
    assert float(me.json()["cash_balance"]) < float(cash_before)


@pytest.mark.asyncio
async def test_double_approve_does_not_double_execute(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mock_llm, mock_market_data
):
    strategy = await _create_resolved_backtested_strategy(client, db_session, auth_headers)
    user_result = await db_session.execute(select(User).where(User.id == strategy.user_id))
    user = user_result.scalar_one()

    plan = await _generate_pending_plan(db_session, strategy, user)

    first = await client.post(f"/api/plans/{plan.id}/approve", headers=auth_headers)
    assert first.status_code == 200

    second = await client.post(f"/api/plans/{plan.id}/approve", headers=auth_headers)
    assert second.status_code == 409

    portfolio = await client.get("/api/portfolio", headers=auth_headers)
    assert len(portfolio.json()["holdings"]) == 1  # not doubled


@pytest.mark.asyncio
async def test_expired_plan_cannot_be_approved(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mock_llm, mock_market_data
):
    strategy = await _create_resolved_backtested_strategy(client, db_session, auth_headers)
    user_result = await db_session.execute(select(User).where(User.id == strategy.user_id))
    user = user_result.scalar_one()

    plan = await _generate_pending_plan(db_session, strategy, user)
    plan.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db_session.flush()

    approve = await client.post(f"/api/plans/{plan.id}/approve", headers=auth_headers)
    assert approve.status_code == 422
    assert "expired" in approve.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reject_plan(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mock_llm, mock_market_data
):
    strategy = await _create_resolved_backtested_strategy(client, db_session, auth_headers)
    user_result = await db_session.execute(select(User).where(User.id == strategy.user_id))
    user = user_result.scalar_one()

    plan = await _generate_pending_plan(db_session, strategy, user)

    reject = await client.post(f"/api/plans/{plan.id}/reject", headers=auth_headers)
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"

    portfolio = await client.get("/api/portfolio", headers=auth_headers)
    assert portfolio.json()["holdings"] == []


@pytest.mark.asyncio
async def test_plan_ownership_is_enforced(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mock_llm, mock_market_data
):
    strategy = await _create_resolved_backtested_strategy(client, db_session, auth_headers)
    user_result = await db_session.execute(select(User).where(User.id == strategy.user_id))
    user = user_result.scalar_one()
    plan = await _generate_pending_plan(db_session, strategy, user)

    await client.post("/api/auth/register", json={"email": "other2@test.com", "password": "secret123"})
    login = await client.post("/api/auth/login", json={"email": "other2@test.com", "password": "secret123"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    approve = await client.post(f"/api/plans/{plan.id}/approve", headers=other_headers)
    assert approve.status_code == 404
