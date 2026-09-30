from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.strategy import Strategy


class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[BacktestStatus] = mapped_column(
        SQLEnum(BacktestStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=BacktestStatus.PENDING,
    )
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    starting_cash: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    equity_curve: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    trades: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="backtest_runs")
