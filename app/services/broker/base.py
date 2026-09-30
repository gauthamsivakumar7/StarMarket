from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@dataclass
class ProposedOrder:
    asset_id: str
    symbol: str
    side: str  # "BUY" | "SELL"
    shares: Decimal


@dataclass
class OrderResult:
    status: str  # "filled" | "failed"
    shares: Decimal | None = None
    price_per_share: Decimal | None = None
    total_value: Decimal | None = None
    cash_balance: Decimal | None = None
    error_message: str | None = None


class BrokerAdapter(ABC):
    @abstractmethod
    async def submit_order(
        self, db: AsyncSession, user: User, order: ProposedOrder, idempotency_key: str
    ) -> OrderResult: ...
