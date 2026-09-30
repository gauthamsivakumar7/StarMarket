from decimal import Decimal

from app.models.backtest_run import BacktestRun, BacktestStatus
from app.models.user import User
from app.schemas.strategy_spec import Condition, ExecutionParams, IndicatorRef, RiskParams, StrategySpec
from app.services import risk_engine


def _spec(**risk_overrides) -> StrategySpec:
    entry = Condition(
        left=IndicatorRef(name="CLOSE", symbol="SPY", params={}),
        op=">",
        right=IndicatorRef(name="SMA", symbol="SPY", params={"window": 20}),
    )
    risk_kwargs = {"max_portfolio_risk_pct": Decimal("1"), "max_position_pct": Decimal("100")}
    risk_kwargs.update(risk_overrides)
    return StrategySpec(
        name="test",
        universe=["SPY"],
        asset_class="equity",
        entry_rule=entry,
        risk=RiskParams(**risk_kwargs),
        execution=ExecutionParams(),
    )


def _completed_backtest(**metric_overrides) -> BacktestRun:
    metrics = {
        "total_return_pct": 10.0,
        "max_drawdown_pct": 5.0,
        "sharpe_ratio": 1.2,
        "win_rate": 60.0,
        "num_trades": 10,
        "avg_trade_return_pct": 1.0,
    }
    metrics.update(metric_overrides)
    return BacktestRun(status=BacktestStatus.COMPLETED, metrics=metrics)


def _user(cash: str) -> User:
    return User(cash_balance=Decimal(cash))


def test_assess_passes_for_healthy_strategy():
    assessment = risk_engine.assess(_spec(), _completed_backtest(), _user("10000"), [])
    assert assessment.passed
    assert assessment.blocking_issues == []


def test_assess_blocks_without_completed_backtest():
    backtest = BacktestRun(status=BacktestStatus.PENDING, metrics=None)
    assessment = risk_engine.assess(_spec(), backtest, _user("10000"), [])
    assert not assessment.passed
    assert any("no completed backtest" in b for b in assessment.blocking_issues)


def test_assess_blocks_on_excessive_drawdown():
    assessment = risk_engine.assess(_spec(), _completed_backtest(max_drawdown_pct=75.0), _user("10000"), [])
    assert not assessment.passed
    assert any("drawdown" in b for b in assessment.blocking_issues)


def test_assess_blocks_on_too_few_trades():
    assessment = risk_engine.assess(_spec(), _completed_backtest(num_trades=0), _user("10000"), [])
    assert not assessment.passed
    assert any("trades" in b for b in assessment.blocking_issues)


def test_assess_warns_but_does_not_block_on_negative_sharpe():
    assessment = risk_engine.assess(_spec(), _completed_backtest(sharpe_ratio=-0.5), _user("10000"), [])
    assert assessment.passed
    assert any("Sharpe" in w for w in assessment.warnings)


def test_assess_blocks_on_insufficient_cash():
    orders = [{"side": "BUY", "estimated_cost": 5000.0}]
    assessment = risk_engine.assess(_spec(), _completed_backtest(), _user("100"), orders)
    assert not assessment.passed
    assert any("exceeds current cash balance" in b for b in assessment.blocking_issues)


def test_assess_blocks_on_invalid_spec():
    bad_spec = _spec(max_portfolio_risk_pct=Decimal("50"))
    assessment = risk_engine.assess(bad_spec, _completed_backtest(), _user("10000"), [])
    assert not assessment.passed
    assert any("validation:" in b for b in assessment.blocking_issues)
