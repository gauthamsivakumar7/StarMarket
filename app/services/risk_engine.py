from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.backtest_run import BacktestRun, BacktestStatus
from app.models.execution_plan import ExecutionPlan
from app.models.user import User
from app.schemas.strategy_spec import StrategySpec
from app.services import strategy_validation_service as validation

MAX_DRAWDOWN_REJECT_PCT = 50.0
MIN_BACKTEST_TRADES = 1


@dataclass
class RiskAssessment:
    passed: bool
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "blocking_issues": self.blocking_issues,
            "warnings": self.warnings,
            "checked_at": self.checked_at,
        }


def assess(
    spec: StrategySpec,
    backtest_run: BacktestRun,
    user: User,
    proposed_orders: list[dict],
) -> RiskAssessment:
    """Checkpoint A: run at plan-generation time. Informational/defense-in-depth
    only — the sole financial authority remains trading.py's row-locked buy/sell,
    which independently re-checks affordability at the instant of execution."""
    blocking: list[str] = []
    warnings: list[str] = []

    issues = validation.validate_spec(spec)
    for issue in issues:
        if issue.severity == "error":
            blocking.append(f"validation: {issue.message}")
        else:
            warnings.append(f"validation: {issue.message}")

    if backtest_run.status != BacktestStatus.COMPLETED or not backtest_run.metrics:
        blocking.append("no completed backtest on file for this strategy")
    else:
        metrics = backtest_run.metrics
        if metrics.get("num_trades", 0) < MIN_BACKTEST_TRADES:
            blocking.append(
                f"backtest produced {metrics.get('num_trades', 0)} trades; "
                f"at least {MIN_BACKTEST_TRADES} required before going live"
            )
        if metrics.get("max_drawdown_pct", 0) > MAX_DRAWDOWN_REJECT_PCT:
            blocking.append(
                f"backtest max drawdown {metrics.get('max_drawdown_pct'):.1f}% exceeds "
                f"{MAX_DRAWDOWN_REJECT_PCT}% hard limit"
            )
        if metrics.get("sharpe_ratio", 0) < 0:
            warnings.append(
                f"backtest Sharpe ratio {metrics.get('sharpe_ratio'):.2f} is negative — "
                "strategy underperformed a risk-free return historically"
            )

    total_estimated_cost = sum(
        Decimal(str(o["estimated_cost"])) for o in proposed_orders if o["side"] == "BUY"
    )
    if total_estimated_cost > user.cash_balance:
        blocking.append(
            f"estimated cost {total_estimated_cost} exceeds current cash balance {user.cash_balance}"
        )

    return RiskAssessment(
        passed=len(blocking) == 0,
        blocking_issues=blocking,
        warnings=warnings,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )


async def re_check_at_approval(db: AsyncSession, plan: ExecutionPlan, user: User) -> RiskAssessment:
    """Checkpoint B: run synchronously inside the approve endpoint, before the
    paper broker is called. Still not authoritative — trading.py re-locks and
    re-reads cash_balance/current_price independently regardless of this result."""
    blocking: list[str] = []
    warnings: list[str] = []

    now = datetime.now(timezone.utc)
    expires_at = plan.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        blocking.append("execution plan has expired; generate a fresh plan")

    total_estimated_cost = Decimal("0")
    for order in plan.proposed_orders:
        asset_result = await db.execute(select(Asset).where(Asset.id == order["asset_id"]))
        asset = asset_result.scalar_one_or_none()
        if asset is None:
            blocking.append(f"asset {order.get('symbol', order['asset_id'])} no longer exists")
            continue
        if order["side"] == "BUY":
            total_estimated_cost += Decimal(str(order["estimated_cost"]))

    if total_estimated_cost > user.cash_balance:
        blocking.append(
            f"estimated cost {total_estimated_cost} exceeds current cash balance {user.cash_balance}"
        )

    return RiskAssessment(
        passed=len(blocking) == 0,
        blocking_issues=blocking,
        warnings=warnings,
        checked_at=now.isoformat(),
    )
