from decimal import Decimal

from app.schemas.strategy_spec import Condition, ExecutionParams, IndicatorRef, RiskParams, StrategySpec
from app.services import strategy_validation_service as validation


def _base_spec(**risk_overrides) -> StrategySpec:
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


def test_valid_spec_has_no_errors():
    issues = validation.validate_spec(_base_spec())
    assert not validation.has_errors(issues)


def test_excessive_risk_pct_is_rejected():
    spec = _base_spec(max_portfolio_risk_pct=Decimal("10"))
    issues = validation.validate_spec(spec)
    assert validation.has_errors(issues)
    assert any(i.code == "invalid_max_portfolio_risk" for i in issues)


def test_excessive_stop_loss_is_rejected():
    spec = _base_spec(stop_loss_pct=Decimal("90"))
    issues = validation.validate_spec(spec)
    assert any(i.code == "invalid_stop_loss" for i in issues)


def test_unsupported_asset_class_rejected_with_clear_message():
    spec = _base_spec()
    spec = spec.model_copy(update={"asset_class": "crypto"})
    issues = validation.validate_spec(spec)
    assert validation.has_errors(issues)
    crypto_issue = next(i for i in issues if i.code == "unsupported_asset_class")
    assert "not yet supported" in crypto_issue.message


def test_universe_length_over_one_rejected():
    spec = _base_spec()
    spec = spec.model_copy(update={"universe": ["SPY", "QQQ"]})
    issues = validation.validate_spec(spec)
    assert any(i.code == "universe_too_large" for i in issues)


def test_empty_universe_rejected():
    spec = _base_spec()
    spec = spec.model_copy(update={"universe": []})
    issues = validation.validate_spec(spec)
    assert any(i.code == "empty_universe" for i in issues)


def test_indicator_window_out_of_bounds_rejected():
    entry = Condition(
        left=IndicatorRef(name="CLOSE", symbol="SPY", params={}),
        op=">",
        right=IndicatorRef(name="SMA", symbol="SPY", params={"window": 5000}),
    )
    spec = _base_spec().model_copy(update={"entry_rule": entry})
    issues = validation.validate_spec(spec)
    assert any(i.code == "invalid_indicator_window" for i in issues)


def test_degenerate_condition_rejected():
    same = IndicatorRef(name="SMA", symbol="SPY", params={"window": 20})
    entry = Condition(left=same, op=">", right=same)
    spec = _base_spec().model_copy(update={"entry_rule": entry})
    issues = validation.validate_spec(spec)
    assert any(i.code == "degenerate_condition" for i in issues)
