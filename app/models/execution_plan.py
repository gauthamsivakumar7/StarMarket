from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.strategy import Strategy


class ExecutionPlanStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"
    FAILED = "failed"
    PARTIALLY_FILLED = "partially_filled"


class ExecutionPlanTrigger(str, Enum):
    USER_MANUAL = "user_manual"
    MONITORING_SWEEP = "monitoring_sweep"


class ExecutionPlan(Base):
    __tablename__ = "execution_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    backtest_run_id: Mapped[int] = mapped_column(
        ForeignKey("backtest_runs.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[ExecutionPlanStatus] = mapped_column(
        SQLEnum(ExecutionPlanStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ExecutionPlanStatus.PENDING_APPROVAL,
    )
    triggered_by: Mapped[ExecutionPlanTrigger] = mapped_column(
        SQLEnum(ExecutionPlanTrigger, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    proposed_orders: Mapped[list] = mapped_column(JSONB, nullable=False)
    risk_assessment: Mapped[dict] = mapped_column(JSONB, nullable=False)
    approval_risk_recheck: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    fills: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="execution_plans")
