from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.execution_plan import ExecutionPlan
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.execution_plan import ExecutionPlanResponse
from app.services import execution_plan_service
from app.services.execution_plan_service import ExecutionPlanError

router = APIRouter(prefix="/plans", tags=["execution_plans"])


async def _get_owned_plan(db: AsyncSession, plan_id: int, user: User) -> ExecutionPlan:
    result = await db.execute(
        select(ExecutionPlan)
        .join(Strategy, Strategy.id == ExecutionPlan.strategy_id)
        .where(ExecutionPlan.id == plan_id, Strategy.user_id == user.id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Execution plan not found")
    return plan


@router.get("/{plan_id}", response_model=ExecutionPlanResponse)
async def get_plan(
    plan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return await _get_owned_plan(db, plan_id, current_user)


@router.post("/{plan_id}/approve", response_model=ExecutionPlanResponse)
async def approve_plan(
    plan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    plan = await _get_owned_plan(db, plan_id, current_user)
    try:
        return await execution_plan_service.approve_plan(db, plan, current_user)
    except ExecutionPlanError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{plan_id}/reject", response_model=ExecutionPlanResponse)
async def reject_plan(
    plan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    plan = await _get_owned_plan(db, plan_id, current_user)
    try:
        return await execution_plan_service.reject_plan(db, plan)
    except ExecutionPlanError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
