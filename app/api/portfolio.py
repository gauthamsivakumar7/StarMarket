from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_active_user, get_db
from app.models.asset import Asset
from app.models.portfolio_position import PortfolioPosition
from app.models.user import User
from app.schemas.portfolio import PortfolioPositionResponse, PortfolioResponse

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(
        select(PortfolioPosition)
        .where(PortfolioPosition.user_id == current_user.id)
        .options(selectinload(PortfolioPosition.asset))
    )
    positions = result.scalars().all()
    holdings: list[PortfolioPositionResponse] = []
    total_mv = Decimal("0")
    total_cb = Decimal("0")

    for pos in positions:
        current_price = pos.asset.current_price
        market_value = pos.shares * current_price
        cost_basis = pos.shares * pos.avg_cost
        unrealized_pnl = market_value - cost_basis
        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else None

        holdings.append(
            PortfolioPositionResponse(
                asset_id=pos.asset_id,
                asset_name=pos.asset.name,
                shares=pos.shares,
                avg_cost=pos.avg_cost,
                current_price=current_price,
                market_value=market_value,
                cost_basis=cost_basis,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
            )
        )
        total_mv += market_value
        total_cb += cost_basis

    total_unrealized_pnl = total_mv - total_cb
    total_unrealized_pnl_pct = (
        (total_unrealized_pnl / total_cb * 100) if total_cb > 0 else None
    )

    return PortfolioResponse(
        holdings=holdings,
        total_market_value=total_mv,
        total_cost_basis=total_cb,
        total_unrealized_pnl=total_unrealized_pnl,
        total_unrealized_pnl_pct=total_unrealized_pnl_pct,
    )
