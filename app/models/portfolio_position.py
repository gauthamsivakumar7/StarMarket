from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.user import User


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"
    __table_args__ = (UniqueConstraint("user_id", "asset_id", name="uq_portfolio_user_asset"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id", ondelete="CASCADE"))
    shares: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="portfolio_positions")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="portfolio_positions")
