import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, Boolean, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.portfolio_position import PortfolioPosition
    from app.models.transaction import Transaction
    from app.models.trade_request import TradeRequest
    from app.models.strategy import Strategy


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=0, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(
        "PortfolioPosition", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    trade_requests: Mapped[list["TradeRequest"]] = relationship(
        "TradeRequest", back_populates="user", cascade="all, delete-orphan"
    )
    strategies: Mapped[list["Strategy"]] = relationship(
        "Strategy", back_populates="user", cascade="all, delete-orphan"
    )
