from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.asset import Asset
from app.models.portfolio_position import PortfolioPosition
from app.models.transaction import Transaction, TransactionSide
from app.models.trade_request import TradeRequest
from app.models.user import User


class TradingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


async def check_idempotency(
    db: AsyncSession, idempotency_key: Optional[str], user_id: str
) -> bool:
    """Returns True if this is a duplicate request (key already used)."""
    if not idempotency_key:
        return False
    result = await db.execute(
        select(TradeRequest).where(
            TradeRequest.idempotency_key == idempotency_key,
            TradeRequest.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None


def _record_trade_request(db: AsyncSession, idempotency_key: str, user_id: str) -> None:
    tr = TradeRequest(idempotency_key=idempotency_key, user_id=user_id)
    db.add(tr)


async def buy(
    db: AsyncSession,
    user: User,
    asset_id: str,
    shares: Decimal,
    idempotency_key: Optional[str] = None,
) -> tuple[PortfolioPosition | None, Decimal]:
    if shares <= 0:
        raise TradingError("Shares must be positive", 400)

    if await check_idempotency(db, idempotency_key, user.id):
        raise TradingError("Duplicate request: idempotency key already used", 409)

    user_result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = user_result.scalar_one()
    if locked_user is None:
        raise TradingError("User not found", 404)

    asset_result = await db.execute(
        select(Asset).where(Asset.id == asset_id).with_for_update()
    )
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise TradingError("Asset not found", 404)

    total_cost = shares * asset.current_price
    if locked_user.cash_balance < total_cost:
        raise TradingError("Insufficient funds", 400)

    position_result = await db.execute(
        select(PortfolioPosition)
        .where(PortfolioPosition.user_id == user.id, PortfolioPosition.asset_id == asset_id)
        .with_for_update()
    )
    position = position_result.scalar_one_or_none()

    if position:
        old_shares = position.shares
        old_avg = position.avg_cost
        new_shares = old_shares + shares
        new_avg = (old_shares * old_avg + shares * asset.current_price) / new_shares
        position.shares = new_shares
        position.avg_cost = new_avg
    else:
        position = PortfolioPosition(
            user_id=user.id,
            asset_id=asset_id,
            shares=shares,
            avg_cost=asset.current_price,
        )
        db.add(position)
        await db.flush()

    locked_user.cash_balance -= total_cost

    transaction = Transaction(
        user_id=user.id,
        asset_id=asset_id,
        side=TransactionSide.BUY,
        shares=shares,
        price_per_share=asset.current_price,
        total_value=total_cost,
    )
    db.add(transaction)

    if idempotency_key:
        _record_trade_request(db, idempotency_key, user.id)

    await db.commit()
    await db.refresh(position)
    await db.refresh(locked_user)
    return position, locked_user.cash_balance


async def sell(
    db: AsyncSession,
    user: User,
    asset_id: str,
    shares: Decimal,
    idempotency_key: Optional[str] = None,
) -> tuple[PortfolioPosition | None, Decimal]:
    if shares <= 0:
        raise TradingError("Shares must be positive", 400)

    if await check_idempotency(db, idempotency_key, user.id):
        raise TradingError("Duplicate request: idempotency key already used", 409)

    user_result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = user_result.scalar_one()
    if locked_user is None:
        raise TradingError("User not found", 404)

    asset_result = await db.execute(
        select(Asset).where(Asset.id == asset_id).with_for_update()
    )
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise TradingError("Asset not found", 404)

    position_result = await db.execute(
        select(PortfolioPosition)
        .where(PortfolioPosition.user_id == user.id, PortfolioPosition.asset_id == asset_id)
        .with_for_update()
    )
    position = position_result.scalar_one_or_none()
    if not position or position.shares < shares:
        raise TradingError("Insufficient shares to sell", 400)

    total_proceeds = shares * asset.current_price
    new_shares = position.shares - shares

    if new_shares <= 0:
        await db.delete(position)
        await db.flush()
        result_position = None
    else:
        position.shares = new_shares
        result_position = position

    locked_user.cash_balance += total_proceeds

    transaction = Transaction(
        user_id=user.id,
        asset_id=asset_id,
        side=TransactionSide.SELL,
        shares=shares,
        price_per_share=asset.current_price,
        total_value=total_proceeds,
    )
    db.add(transaction)

    if idempotency_key:
        _record_trade_request(db, idempotency_key, user.id)

    await db.commit()
    if result_position:
        await db.refresh(result_position)
    await db.refresh(locked_user)
    return result_position, locked_user.cash_balance
