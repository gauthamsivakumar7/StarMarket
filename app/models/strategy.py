import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.backtest_run import BacktestRun
    from app.models.execution_plan import ExecutionPlan
    from app.models.strategy_signal_run import StrategySignalRun
    from app.models.user import User


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    INVALID = "invalid"
    RESOLVED = "resolved"
    BACKTESTED = "backtested"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    thesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False)
    canonical_spec: Mapped[dict] = mapped_column(JSONB, nullable=False)
    validation_issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    resolved_universe: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    context_symbols: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[StrategyStatus] = mapped_column(
        SQLEnum(StrategyStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StrategyStatus.DRAFT,
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="strategies")
    backtest_runs: Mapped[list["BacktestRun"]] = relationship(
        "BacktestRun", back_populates="strategy", cascade="all, delete-orphan"
    )
    execution_plans: Mapped[list["ExecutionPlan"]] = relationship(
        "ExecutionPlan", back_populates="strategy", cascade="all, delete-orphan"
    )
    signal_runs: Mapped[list["StrategySignalRun"]] = relationship(
        "StrategySignalRun", back_populates="strategy", cascade="all, delete-orphan"
    )
