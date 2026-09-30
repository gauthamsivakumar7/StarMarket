from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.backtest_run import BacktestRun
from app.models.execution_plan import ExecutionPlan, ExecutionPlanStatus, ExecutionPlanTrigger
from app.models.portfolio_position import PortfolioPosition
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy_spec import StrategySpec
from app.services import position_sizing, risk_engine
from app.services.broker.base import BrokerAdapter, ProposedOrder
from app.services.broker.paper_broker import PaperBrokerAdapter

EXECUTION_PLAN_TTL_HOURS = 24


class ExecutionPlanError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


async def build_proposed_orders(
    db: AsyncSession, user: User, spec: StrategySpec, action: Literal["entry", "exit"]
) -> list[dict]:
    symbol = spec.universe[0]
    asset_result = await db.execute(select(Asset).where(Asset.symbol == symbol))
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise ExecutionPlanError(f"Asset for symbol '{symbol}' is not resolved yet")

    if action == "entry":
        shares = position_sizing.size_position(user.cash_balance, asset.current_price, spec.risk)
        if shares <= 0:
            return []
        estimated_cost = shares * asset.current_price
        return [
            {
                "symbol": symbol,
                "asset_id": asset.id,
                "side": "BUY",
                "order_type": spec.execution.order_type,
                "shares": float(shares),
                "estimated_price": float(asset.current_price),
                "estimated_cost": float(estimated_cost),
                "rationale": "entry_rule triggered",
            }
        ]

    pos_result = await db.execute(
        select(PortfolioPosition).where(
            PortfolioPosition.user_id == user.id, PortfolioPosition.asset_id == asset.id
        )
    )
    position = pos_result.scalar_one_or_none()
    if position is None or position.shares <= 0:
        return []
    return [
        {
            "symbol": symbol,
            "asset_id": asset.id,
            "side": "SELL",
            "order_type": spec.execution.order_type,
            "shares": float(position.shares),
            "estimated_price": float(asset.current_price),
            "estimated_cost": 0.0,
            "rationale": "exit_rule/stop-loss/take-profit triggered",
        }
    ]


async def generate_plan(
    db: AsyncSession,
    strategy: Strategy,
    backtest_run: BacktestRun,
    user: User,
    spec: StrategySpec,
    proposed_orders: list[dict],
    triggered_by: ExecutionPlanTrigger,
) -> ExecutionPlan:
    assessment = risk_engine.assess(spec, backtest_run, user, proposed_orders)
    status = ExecutionPlanStatus.PENDING_APPROVAL if assessment.passed else ExecutionPlanStatus.REJECTED
    plan = ExecutionPlan(
        strategy_id=strategy.id,
        backtest_run_id=backtest_run.id,
        status=status,
        triggered_by=triggered_by,
        proposed_orders=proposed_orders,
        risk_assessment=assessment.to_dict(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=EXECUTION_PLAN_TTL_HOURS),
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


async def approve_plan(
    db: AsyncSession, plan: ExecutionPlan, user: User, broker: BrokerAdapter | None = None
) -> ExecutionPlan:
    if plan.status != ExecutionPlanStatus.PENDING_APPROVAL:
        raise ExecutionPlanError(f"plan is '{plan.status.value}', not pending approval", 409)

    recheck = await risk_engine.re_check_at_approval(db, plan, user)
    plan.approval_risk_recheck = recheck.to_dict()
    if not recheck.passed:
        expired = any("expired" in b for b in recheck.blocking_issues)
        plan.status = ExecutionPlanStatus.EXPIRED if expired else ExecutionPlanStatus.REJECTED
        await db.commit()
        raise ExecutionPlanError("; ".join(recheck.blocking_issues), 422)

    broker = broker or PaperBrokerAdapter()
    fills: list[dict] = []
    any_failed = False
    any_filled = False

    for idx, order in enumerate(plan.proposed_orders):
        # Refresh current_price for just this asset right before execution,
        # closing the plan-generation-to-approval staleness gap deterministically.
        await _refresh_price(db, order["asset_id"])

        idem_key = f"execplan:{plan.id}:{idx}"
        proposed = ProposedOrder(
            asset_id=order["asset_id"],
            symbol=order["symbol"],
            side=order["side"],
            shares=Decimal(str(order["shares"])),
        )
        result = await broker.submit_order(db, user, proposed, idem_key)
        fills.append(
            {
                "order_index": idx,
                "status": result.status,
                "price_per_share": float(result.price_per_share) if result.price_per_share is not None else None,
                "shares": float(result.shares) if result.shares is not None else None,
                "total_value": float(result.total_value) if result.total_value is not None else None,
                "filled_at": datetime.now(timezone.utc).isoformat(),
                "error_message": result.error_message,
            }
        )
        if result.status == "filled":
            any_filled = True
        else:
            any_failed = True

    plan.fills = fills
    now = datetime.now(timezone.utc)
    plan.executed_at = now
    if any_filled and not any_failed:
        plan.status = ExecutionPlanStatus.EXECUTED
        plan.approved_at = now
    elif any_filled and any_failed:
        plan.status = ExecutionPlanStatus.PARTIALLY_FILLED
        plan.approved_at = now
    else:
        plan.status = ExecutionPlanStatus.FAILED

    await db.commit()
    await db.refresh(plan)
    return plan


async def reject_plan(db: AsyncSession, plan: ExecutionPlan) -> ExecutionPlan:
    if plan.status != ExecutionPlanStatus.PENDING_APPROVAL:
        raise ExecutionPlanError(f"plan is '{plan.status.value}', not pending approval", 409)
    plan.status = ExecutionPlanStatus.REJECTED
    plan.rejected_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(plan)
    return plan


async def _refresh_price(db: AsyncSession, asset_id: str) -> None:
    from app.models.price_history import PriceHistory
    from app.services.market_data import registry

    asset_result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = asset_result.scalar_one_or_none()
    if asset is None or asset.symbol is None:
        return
    try:
        adapter = registry.get_adapter(asset.category)
        latest_price = await adapter.get_latest_price(asset.symbol)
    except Exception:  # noqa: BLE001 - price refresh is best-effort; stale price is safer than a hard failure here
        return
    asset.current_price = latest_price
    db.add(PriceHistory(asset_id=asset.id, price=latest_price))
    # autoflush is disabled on this session (see db/session.py) — flush explicitly
    # so trading.buy/sell's subsequent SELECT...FOR UPDATE reads the refreshed price.
    await db.flush()
