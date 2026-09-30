from datetime import date, datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest_run import BacktestRun, BacktestStatus
from app.models.execution_plan import ExecutionPlan, ExecutionPlanStatus, ExecutionPlanTrigger
from app.models.portfolio_position import PortfolioPosition
from app.models.strategy import Strategy, StrategyStatus
from app.models.strategy_signal_run import SignalRunAction, SignalRunTrigger, StrategySignalRun
from app.models.user import User
from app.schemas.strategy_spec import StrategySpec
from app.services import execution_plan_service
from app.services.backtest_service import LOOKBACK_BUFFER_DAYS, align_bars
from app.services.market_data import registry
from app.services.strategy_compiler_service import compile_strategy


async def evaluate_strategy(
    db: AsyncSession, strategy: Strategy, triggered_by: SignalRunTrigger
) -> StrategySignalRun:
    run = StrategySignalRun(strategy_id=strategy.id, triggered_by=triggered_by)

    try:
        spec = StrategySpec.model_validate(strategy.canonical_spec)
        compiled = compile_strategy(spec)
        adapter = registry.get_adapter(spec.asset_class)

        end = date.today()
        start = end - timedelta(days=LOOKBACK_BUFFER_DAYS)
        raw_bars = {symbol: await adapter.get_ohlcv(symbol, start, end) for symbol in compiled.required_symbols}

        primary_symbol = spec.universe[0]
        primary_bars = raw_bars.get(primary_symbol) or []
        if not primary_bars:
            raise ValueError(f"No recent bar data for '{primary_symbol}'")

        aligned = align_bars(primary_bars, raw_bars)
        ctx = compiled.prepare(aligned)
        i = len(primary_bars) - 1

        entry_signal = compiled.evaluate_entry(ctx, i)
        exit_signal = compiled.evaluate_exit(ctx, i)
        run.data_asof = datetime.combine(primary_bars[i].date, datetime.min.time(), tzinfo=timezone.utc)
        run.signal_snapshot = {
            "entry_signal": entry_signal,
            "exit_signal": exit_signal,
            "close_prices": {s: float(bars[i].close) for s, bars in aligned.items()},
        }

        user_result = await db.execute(select(User).where(User.id == strategy.user_id))
        user = user_result.scalar_one()

        action = await _determine_action(db, user, strategy, spec, entry_signal, exit_signal)
        run.triggered = action is not None

        if action is not None:
            await _handle_triggered(db, run, strategy, spec, user, action)

    except Exception as e:  # noqa: BLE001 - one strategy's failure must not break the whole sweep
        run.error_message = str(e)[:1000]

    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def _determine_action(
    db: AsyncSession,
    user: User,
    strategy: Strategy,
    spec: StrategySpec,
    entry_signal: bool | None,
    exit_signal: bool | None,
) -> str | None:
    symbol = spec.universe[0]
    asset_id = (strategy.resolved_universe or {}).get(symbol)
    holds_position = False
    if asset_id:
        pos_result = await db.execute(
            select(PortfolioPosition).where(
                PortfolioPosition.user_id == user.id, PortfolioPosition.asset_id == asset_id
            )
        )
        position = pos_result.scalar_one_or_none()
        holds_position = bool(position and position.shares > 0)

    if holds_position and exit_signal:
        return "exit"
    if not holds_position and entry_signal:
        return "entry"
    return None


async def _handle_triggered(
    db: AsyncSession,
    run: StrategySignalRun,
    strategy: Strategy,
    spec: StrategySpec,
    user: User,
    action: str,
) -> None:
    existing = await db.execute(
        select(ExecutionPlan).where(
            ExecutionPlan.strategy_id == strategy.id,
            ExecutionPlan.status == ExecutionPlanStatus.PENDING_APPROVAL,
        )
    )
    if existing.scalar_one_or_none() is not None:
        run.action = SignalRunAction.PLAN_SKIPPED_EXISTING_PENDING
        return

    backtest_result = await db.execute(
        select(BacktestRun)
        .where(BacktestRun.strategy_id == strategy.id, BacktestRun.status == BacktestStatus.COMPLETED)
        .order_by(desc(BacktestRun.id))
        .limit(1)
    )
    backtest_run = backtest_result.scalar_one_or_none()
    if backtest_run is None:
        run.error_message = "signal fired but no completed backtest exists; cannot generate a plan"
        return

    proposed_orders = await execution_plan_service.build_proposed_orders(db, user, spec, action)
    if not proposed_orders:
        run.action = SignalRunAction.NONE
        return

    plan = await execution_plan_service.generate_plan(
        db, strategy, backtest_run, user, spec, proposed_orders, ExecutionPlanTrigger.MONITORING_SWEEP
    )
    run.action = SignalRunAction.PLAN_GENERATED
    run.execution_plan_id = plan.id


async def run_monitoring_sweep(db: AsyncSession) -> list[StrategySignalRun]:
    result = await db.execute(select(Strategy).where(Strategy.status == StrategyStatus.ACTIVE))
    strategies = result.scalars().all()
    return [await evaluate_strategy(db, s, SignalRunTrigger.ADMIN_SWEEP) for s in strategies]
