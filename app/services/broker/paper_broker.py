from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.user import User
from app.services import trading
from app.services.broker.base import BrokerAdapter, OrderResult, ProposedOrder


class PaperBrokerAdapter(BrokerAdapter):
    """Fills orders against the existing virtual cash_balance ledger by calling
    directly into trading.buy/sell — the same row-locked, idempotent engine
    that backs the app's manual /trade endpoints. This file intentionally
    contains zero money-movement logic of its own."""

    async def submit_order(
        self, db: AsyncSession, user: User, order: ProposedOrder, idempotency_key: str
    ) -> OrderResult:
        fn = trading.buy if order.side == "BUY" else trading.sell
        try:
            _, cash_balance = await fn(db, user, order.asset_id, order.shares, idempotency_key)
        except trading.TradingError as e:
            return OrderResult(status="failed", error_message=e.message)

        # buy/sell don't return the Transaction row; fetch the one they just
        # committed to report the actual executed fill price (never assumed).
        txn_result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id, Transaction.asset_id == order.asset_id)
            .order_by(desc(Transaction.id))
            .limit(1)
        )
        txn = txn_result.scalar_one_or_none()

        return OrderResult(
            status="filled",
            shares=txn.shares if txn else order.shares,
            price_per_share=txn.price_per_share if txn else None,
            total_value=txn.total_value if txn else None,
            cash_balance=cash_balance,
        )
