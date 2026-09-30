from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.backtest_run import BacktestRun
from app.models.execution_plan import ExecutionPlan
from app.models.strategy import Strategy
from app.models.strategy_signal_run import SignalRunTrigger, StrategySignalRun
from app.models.user import User
from app.schemas.backtest import BacktestRequest, BacktestRunResponse
from app.schemas.execution_plan import ExecutionPlanResponse, SignalRunResponse
from app.schemas.strategy import StrategyCreateRequest, StrategyResponse
from app.services import monitoring_service, strategy_service
from app.services.strategy_service import StrategyServiceError

router = APIRouter(prefix="/strategies", tags=["strategies"])


async def _get_owned_strategy(db: AsyncSession, strategy_id: str, user: User) -> Strategy:
    result = await db.execute(
        select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user.id)
    )
    strategy = result.scalar_one_or_none()
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.post("", response_model=StrategyResponse)
async def create_strategy(
    body: StrategyCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        strategy = await strategy_service.create_strategy_from_thesis(
            db, current_user, body.thesis_text, body.name
        )
    except StrategyServiceError as e:
        raise HTTPException(status_code=e.status_code, detail={"message": e.message, "issues": e.issues})
    return strategy


@router.get("", response_model=list[StrategyResponse])
async def list_strategies(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(
        select(Strategy).where(Strategy.user_id == current_user.id).order_by(desc(Strategy.created_at))
    )
    return list(result.scalars().all())


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return await _get_owned_strategy(db, strategy_id, current_user)


@router.post("/{strategy_id}/resolve", response_model=StrategyResponse)
async def resolve_strategy(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    try:
        return await strategy_service.resolve_strategy(db, strategy)
    except StrategyServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{strategy_id}/backtest", response_model=BacktestRunResponse)
async def backtest_strategy(
    strategy_id: str,
    body: BacktestRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    try:
        return await strategy_service.backtest_strategy(
            db, strategy, body.start_date, body.end_date, body.starting_cash
        )
    except StrategyServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{strategy_id}/backtests", response_model=list[BacktestRunResponse])
async def list_backtests(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    result = await db.execute(
        select(BacktestRun).where(BacktestRun.strategy_id == strategy.id).order_by(desc(BacktestRun.id))
    )
    return list(result.scalars().all())


@router.post("/{strategy_id}/activate", response_model=StrategyResponse)
async def activate_strategy(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    try:
        return await strategy_service.activate_strategy(db, strategy)
    except StrategyServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{strategy_id}/pause", response_model=StrategyResponse)
async def pause_strategy(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    return await strategy_service.pause_strategy(db, strategy)


@router.post("/{strategy_id}/evaluate", response_model=SignalRunResponse)
async def evaluate_strategy(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    run = await monitoring_service.evaluate_strategy(db, strategy, SignalRunTrigger.USER_MANUAL)
    if run.error_message:
        raise HTTPException(status_code=422, detail=run.error_message)
    return run


@router.get("/{strategy_id}/execution_plans", response_model=list[ExecutionPlanResponse])
async def list_execution_plans(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    result = await db.execute(
        select(ExecutionPlan)
        .where(ExecutionPlan.strategy_id == strategy.id)
        .order_by(desc(ExecutionPlan.created_at))
    )
    return list(result.scalars().all())


@router.get("/{strategy_id}/runs", response_model=list[SignalRunResponse])
async def list_signal_runs(
    strategy_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    strategy = await _get_owned_strategy(db, strategy_id, current_user)
    result = await db.execute(
        select(StrategySignalRun)
        .where(StrategySignalRun.strategy_id == strategy.id)
        .order_by(desc(StrategySignalRun.created_at))
    )
    return list(result.scalars().all())
