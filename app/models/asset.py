import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.portfolio_position import PortfolioPosition
    from app.models.price_history import PriceHistory
    from app.models.transaction import Transaction


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(
        "PortfolioPosition", back_populates="asset", cascade="all, delete-orphan"
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="asset", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="asset", cascade="all, delete-orphan"
    )
