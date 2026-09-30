from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.strategy import Strategy


class SignalRunTrigger(str, Enum):
    ADMIN_SWEEP = "admin_sweep"
    USER_MANUAL = "user_manual"


class SignalRunAction(str, Enum):
    NONE = "none"
    PLAN_GENERATED = "plan_generated"
    PLAN_SKIPPED_EXISTING_PENDING = "plan_skipped_existing_pending"


class StrategySignalRun(Base):
    __tablename__ = "strategy_signal_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    triggered_by: Mapped[SignalRunTrigger] = mapped_column(
        SQLEnum(SignalRunTrigger, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    data_asof: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    signal_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action: Mapped[SignalRunAction] = mapped_column(
        SQLEnum(SignalRunAction, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=SignalRunAction.NONE,
    )
    execution_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="SET NULL"), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="signal_runs")
