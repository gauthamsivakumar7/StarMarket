from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db, get_idempotency_key
from app.models.asset import Asset
from app.models.portfolio_position import PortfolioPosition
from app.models.user import User
from app.schemas.trade import TradeOrder, TradeResponse
from app.services.trading import TradingError, buy, sell

router = APIRouter(prefix="/trade", tags=["trade"])


def _position_to_dict(
    pos: PortfolioPosition | None, asset_id: str, asset_name: str
) -> dict:
    if pos is None:
        return {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "shares": 0,
            "avg_cost": 0,
        }
    return {
        "asset_id": pos.asset_id,
        "asset_name": asset_name,
        "shares": float(pos.shares),
        "avg_cost": float(pos.avg_cost),
    }


@router.post("/buy", response_model=TradeResponse)
async def trade_buy(
    order: TradeOrder,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    idempotency_key: Optional[str] = get_idempotency_key(request)
    try:
        position, cash_balance = await buy(
            db, current_user, order.asset_id, order.shares, idempotency_key
        )
    except TradingError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.message)

    asset_result = await db.execute(select(Asset).where(Asset.id == order.asset_id))
    asset = asset_result.scalar_one_or_none()
    asset_name = asset.name if asset else ""
    asset_id = order.asset_id

    return TradeResponse(
        message="Buy successful",
        position=_position_to_dict(position, asset_id, asset_name),
        cash_balance=cash_balance,
    )


@router.post("/sell", response_model=TradeResponse)
async def trade_sell(
    order: TradeOrder,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    idempotency_key: Optional[str] = get_idempotency_key(request)
    try:
        position, cash_balance = await sell(
            db, current_user, order.asset_id, order.shares, idempotency_key
        )
    except TradingError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.message)

    asset_result = await db.execute(select(Asset).where(Asset.id == order.asset_id))
    asset = asset_result.scalar_one_or_none()
    asset_name = asset.name if asset else ""
    asset_id = order.asset_id

    return TradeResponse(
        message="Sell successful",
        position=_position_to_dict(position, asset_id, asset_name),
        cash_balance=cash_balance,
    )
