from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, ForeignKey, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.user import User


class TransactionSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id", ondelete="CASCADE"))
    side: Mapped[TransactionSide] = mapped_column(
        SQLEnum(TransactionSide), nullable=False
    )
    shares: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price_per_share: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="transactions")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="transactions")
